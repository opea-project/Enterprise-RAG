# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from abc import ABC

import sentence_transformers

from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

import intel_extension_for_pytorch as ipex
import torch

logger = logging.getLogger(__name__)


class EmbeddingHandler(BaseHandler, ABC):
    def __init__(self):
        super(EmbeddingHandler, self).__init__()
        self.batch_size = None
        self.initialized = False
        self.hf_hub = False

    def initialize(self, ctx : Context):
        model_name = ctx.model_yaml_config["handler"]["model_name"]
        self.batch_size = ctx.model_yaml_config["handler"]["batch_size"]
        self.amp_dtype = ctx.model_yaml_config["handler"]["amp_dtype"]

        try:
            ipex._C.disable_jit_linear_repack()
            torch._C._jit_set_texpr_fuser_enabled(False)
        except Exception:
            pass

        if self.amp_dtype == "BF16":
            self.amp_enabled = True
            self.amp_dtype = torch.bfloat16
        else:
            self.amp_enabled = False
            self.amp_dtype = torch.float32

        self.model = sentence_transformers.SentenceTransformer(model_name)

        self.model = self.model.to(memory_format=torch.channels_last)
        self.model.eval()

        self.model = ipex.llm.optimize(
            self.model,
            dtype=self.amp_dtype,
            inplace=True,
            deployment_mode=True,
        )

        logger.info("Model %s loaded successfully", ctx.model_name)
        self.initialized = True

    def preprocess(self, requests):
        print(f"REQUESTS: {requests}")
        input_texts = [data.get("data") or data.get("body") for data in requests]
        if isinstance(input_texts[0], dict):
            input_texts = input_texts[0]["inputs"]
            self.hf_hub = True
        texts = list(map(lambda x: x.replace("\n", " "), input_texts))
        return texts


    def inference(self, input_batch):
        print(f"INPUT: {input_batch}")
        with torch.inference_mode(), torch.no_grad(), torch.autocast(
            device_type="cpu",
            enabled=self.amp_enabled,
            dtype=self.amp_dtype,
            ):
            embeddings = self.model.encode(input_batch, batch_size=self.batch_size)
        return embeddings.tolist()

    def postprocess(self, inference_output):
        if self.hf_hub:
            return [inference_output]
        return inference_output