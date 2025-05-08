# Copyright (C) 2024-2025 Intel Corporation
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

import logging
import os
from abc import ABC
import numpy as np

from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

import intel_extension_for_pytorch as ipex
import torch
from contextlib import nullcontext
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

# The handler is responsible for defining how a model processes incoming requests during inference

class ReranksHandler(BaseHandler, ABC):
    def __init__(self):
        super(ReranksHandler, self).__init__()
        self.initialized = False


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
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
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

            with torch.inference_mode(), torch.no_grad(), self.additional_context:
                model = torch.jit.trace(self.model, (inputs["input_ids"], inputs["attention_mask"]), check_trace=False, strict=False)
                model = torch.jit.freeze(model)
                model(**inputs)

            for _ in range(10):
                with torch.inference_mode(), torch.no_grad(), self.additional_context:
                    _ = model(**inputs)["logits"].view(-1, ).float()

            self.initialized = True
            logger.info(f"Model '{model_name}' loaded successfully")
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
