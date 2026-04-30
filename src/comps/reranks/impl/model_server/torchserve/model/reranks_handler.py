# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
ReranksHandler is a custom handler for processing reranks models using TorchServe.

Attributes:
    batch_size (int): The batch size for processing requests.
    initialized (bool): Flag indicating if the handler has been initialized.
    device_type (str): The type of device to run the model on (e.g., 'cpu', 'cuda').
    amp_dtype (torch.dtype): The data type for automatic mixed precision (AMP).
    amp_enabled (bool): Flag indicating if AMP is enabled.
    model (sentence_transformers.SentenceTransformer): The reranks model.

Methods:
    __init__():
        Initializes the ReranksHandler instance.

    initialize(ctx: Context):
        Initializes the model and sets up the environment based on context.

    preprocess(requests):
        Preprocesses the incoming requests to extract input texts.

    inference(input_batch):
        Performs inference on the preprocessed input batch to generate reranking_out.

    postprocess(inference_output):
        Postprocesses the inference output to return the final result.
"""

import glob
import hashlib
import logging
import os
import sys
import tempfile
import time
from abc import ABC
import numpy as np

from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

import intel_extension_for_pytorch as ipex
import torch
from contextlib import nullcontext
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

JIT_CACHE_DIR = os.getenv("TORCHSERVE_JIT_CACHE_DIR", "/data/jit_cache")
WARMUP_ROUNDS = 10
DEFAULT_PRELOAD_TIMEOUT_SEC = "1800"
DEFAULT_PRELOAD_POLL_SEC = "30"


class ReranksHandler(BaseHandler, ABC):
    def __init__(self):
        super(ReranksHandler, self).__init__()
        self.initialized = False

    @staticmethod
    def _cache_key(model_name, amp_dtype):
        tag = f"{model_name}|{amp_dtype}"
        return hashlib.sha256(tag.encode()).hexdigest()[:16]

    @staticmethod
    def runtime_tag():
        return f"pt{torch.__version__}_ipex{ipex.__version__}"

    @staticmethod
    def _purge_stale_caches(prefix, current_tag):
        """Remove cached JIT files for the same model but a different runtime version."""
        for path in glob.glob(os.path.join(JIT_CACHE_DIR, f"{prefix}_*.pt")):
            if current_tag not in os.path.basename(path):
                try:
                    os.remove(path)
                    logger.info(f"Removed stale JIT cache: {path}")
                except OSError:
                    pass

    def initialize(self, ctx : Context):
        model_name = str(os.getenv('TORCHSERVE_MODEL_NAME'))
        if not model_name:
                raise ValueError("The 'TORCHSERVE_MODEL_NAME' cannot be empty.")

        self.device_type = str(os.getenv('TORCHSERVE_DEVICE_TYPE', "cpu")).lower()
        self.amp_dtype = str(os.getenv('TORCHSERVE_AMP_DTYPE'))


        if self.amp_dtype == "BF16":
            self.amp_enabled = True
            self.amp_dtype = torch.bfloat16
            self.additional_context = torch.autocast(device_type=self.device_type, enabled=self.amp_enabled, dtype=self.amp_dtype,)
        elif self.amp_dtype == "FP32":
            self.amp_enabled = False
            self.amp_dtype = torch.float32
            self.additional_context = nullcontext()
        else:
            error_message = f"Invalid AMP_DTYPE value '{self.amp_dtype}'. Expected 'BF16' or 'FP32'."
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info(f"TORCHSERVE_MODEL_NAME is set to {model_name}.")
        logger.info(f"TORCHSERVE_DEVICE_TYPE is set to {self.device_type}.")
        logger.info(f"TORCHSERVE_AMP_DTYPE is set to {self.amp_dtype}.")

        try:
            ipex._C.disable_jit_linear_repack()
            torch._C._jit_set_texpr_fuser_enabled(False)
        except Exception:
            logger.warning("Failed to execute ipex._C.disable_jit_linear_repack() and torch._C._jit_set_texpr_fuser_enabled(False). Proceeding without it.")
            pass

        try:
            t0 = time.monotonic()
            logger.info("Loading model weights from HuggingFace ...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            logger.info(f"Model weights loaded in {time.monotonic() - t0:.1f}s")
            self.model = self.model.to(memory_format=torch.channels_last)
            self.model.eval()

            self.model = ipex.optimize(
                self.model,
                dtype=self.amp_dtype,
                inplace=True,
            )

            pairs = [['what is panda?', 'hi'],
                     ['what is panda?', 'The giant panda (Ailuropoda melanoleuca), sometimes called a panda bear or simply panda, is a bear species endemic to China.']]
            inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt')

            cache_key = self._cache_key(model_name, str(self.amp_dtype))
            runtime_tag = self.runtime_tag()
            jit_prefix = f"reranker_{cache_key}"
            jit_path = os.path.join(JIT_CACHE_DIR, f"{jit_prefix}_{runtime_tag}.pt")

            self._purge_stale_caches(jit_prefix, runtime_tag)

            cache_hit = False
            if os.path.isfile(jit_path):
                logger.info(f"Loading JIT-traced model from cache: {jit_path}")
                t1 = time.monotonic()
                try:
                    with torch.inference_mode(), torch.no_grad(), self.additional_context:
                        model = torch.jit.load(jit_path)
                        model(**inputs)
                    logger.info(f"JIT model loaded from cache in {time.monotonic() - t1:.1f}s")
                    cache_hit = True
                except Exception as e:
                    logger.warning(f"JIT cache load failed ({e}), will re-trace")
                    try:
                        os.remove(jit_path)
                    except OSError:
                        pass

            if not cache_hit:
                logger.info("Starting JIT trace + freeze (this may take several minutes) ...")
                t1 = time.monotonic()
                with torch.inference_mode(), torch.no_grad(), self.additional_context:
                    model = torch.jit.trace(self.model, (inputs["input_ids"], inputs["attention_mask"]), check_trace=False, strict=False)
                    model = torch.jit.freeze(model)
                    model(**inputs)

                for _ in range(WARMUP_ROUNDS):
                    with torch.inference_mode(), torch.no_grad(), self.additional_context:
                        _ = model(**inputs)["logits"].view(-1, ).float()
                logger.info(f"JIT trace + freeze + warmup completed in {time.monotonic() - t1:.1f}s")

                tmp_path = None
                try:
                    os.makedirs(JIT_CACHE_DIR, exist_ok=True)
                    fd, tmp_path = tempfile.mkstemp(dir=JIT_CACHE_DIR, suffix=".pt.tmp")
                    os.close(fd)
                    torch.jit.save(model, tmp_path)
                    os.replace(tmp_path, jit_path)
                    logger.info(f"JIT-traced model saved to cache: {jit_path}")
                except Exception as e:
                    logger.warning(f"Could not save JIT cache to {jit_path}: {e}")
                    if tmp_path:
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass

            self.initialized = True
            logger.info(f"Model '{model_name}' loaded successfully (total: {time.monotonic() - t0:.1f}s)")
        except Exception as e:
            logger.error(f"Error loading model '{model_name}': {str(e)}")
            raise

    def _sigmoid(self, z):
            return float(1/(1 + np.exp(-z)))

    def preprocess(self, requests):
        texts = []
        logger.debug(f"Received requests: {requests}")

        bodies = [data.get("data") or data.get("body") for data in requests]

        for body in bodies:
            query, input_texts = body['query'], body['texts']
            rerank_texts = [[query, text] for text in input_texts]
            texts.append(rerank_texts)

        return texts


    def inference(self, input_batch):
        logger.debug(f"Received input_batch: {input_batch}")

        batching = False
        if len(input_batch) > 1:
            batching = True

        texts = []
        num_texts_in_batch = []
        if batching:
            # For reranking model the batched input needs to be flattened
            for text_pair in input_batch:
                num_texts_in_batch.append(len(text_pair))
                texts.extend(text_pair)
        else:
            texts = input_batch[0]

        with torch.inference_mode(), torch.no_grad(), self.additional_context:
            inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
            reranking_out = self.model(**inputs, return_dict=True)["logits"].view(-1, ).float().tolist()

        if batching:
            restored_list = []
            index = 0
            for count in num_texts_in_batch:
                sublist = []
                for sub_count in range(count):
                    sublist.append({"index": sub_count, "score": self._sigmoid(reranking_out[index])})
                    index += 1
                restored_list.append(sublist)
            return restored_list
        else:
            return [[{"index": i, "score": self._sigmoid(score)} for i, score in enumerate(reranking_out)]]


    def postprocess(self, inference_output):
        logger.debug(f"Received inference_output: {inference_output}")
        return inference_output


def _preload_main():
    """Entry point for cache-warmer initContainer (TORCHSERVE_PRELOAD_MODE=1)."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    cache_dir = os.getenv("TORCHSERVE_JIT_CACHE_DIR", "/data/jit_cache")
    timeout = int(os.getenv("TORCHSERVE_PRELOAD_TIMEOUT_SEC", DEFAULT_PRELOAD_TIMEOUT_SEC))
    poll_interval = int(os.getenv("TORCHSERVE_PRELOAD_POLL_SEC", DEFAULT_PRELOAD_POLL_SEC))
    hostname = os.getenv("HOSTNAME", "localhost")

    os.makedirs(cache_dir, exist_ok=True)

    logger.info("Preload starting on %s", hostname)

    runtime_tag = ReranksHandler.runtime_tag()
    done_file = os.path.join(cache_dir, f".preload-done-{runtime_tag}")
    lock_dir = os.path.join(cache_dir, f".preload-lock-{runtime_tag}")

    if os.path.isfile(done_file):
        logger.info("Cache already warm for %s, exiting.", runtime_tag)
        sys.exit(0)

    try:
        os.mkdir(lock_dir)
    except FileExistsError:
        logger.info("Follower (%s): waiting for cache (%s) ...", hostname, runtime_tag)
        elapsed = 0
        while elapsed < timeout:
            if os.path.isfile(done_file):
                logger.info("Follower (%s): cache ready after %ds.", hostname, elapsed)
                sys.exit(0)
            time.sleep(poll_interval)
            elapsed += poll_interval
        logger.info("Follower (%s): timeout after %ds; removing stale lock.", hostname, timeout)
        try:
            os.rmdir(lock_dir)
        except OSError:
            pass
        sys.exit(1)

    logger.info("Leader (%s): warming cache for %s ...", hostname, runtime_tag)
    try:
        reranks_handler = ReranksHandler()
        reranks_handler.initialize(None)
        logger.info("Leader (%s): preload complete.", hostname)
    except Exception as exc:
        logger.info("Leader (%s): handler failed: %s", hostname, exc)
        try:
            os.rmdir(lock_dir)
        except OSError:
            pass
        sys.exit(1)

    try:
        os.rmdir(lock_dir)
    except OSError:
        pass

    try:
        with open(done_file, "w", encoding="utf-8") as f:
            f.write(f"completed by {hostname} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except OSError as exc:
        logger.warning("Could not create marker file %s: %s", done_file, exc)

    logger.info("Leader (%s): done, marker file created.", hostname)
    sys.exit(0)


if __name__ == "__main__":
    _preload_main()
