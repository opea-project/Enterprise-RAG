# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
EmbeddingHandler is a custom handler for processing embedding models using TorchServe.

Attributes:
    batch_size (int): The batch size for processing requests.
    initialized (bool): Flag indicating if the handler has been initialized.
    hf_hub (bool): Flag indicating if the input is from Hugging Face Hub.
    device_type (str): The type of device to run the model on (e.g., 'cpu', 'cuda').
    amp_dtype (torch.dtype): The data type for automatic mixed precision (AMP).
    amp_enabled (bool): Flag indicating if AMP is enabled.
    model (sentence_transformers.SentenceTransformer): The embedding model.

Methods:
    __init__():
        Initializes the EmbeddingHandler instance.

    initialize(ctx: Context):
        Initializes the model and sets up the environment based on context.

    preprocess(requests):
        Preprocesses the incoming requests to extract input texts.

    inference(input_batch):
        Performs inference on the preprocessed input batch to generate embeddings.

    postprocess(inference_output):
        Postprocesses the inference output to return the final result.
"""

from abc import ABC
import intel_extension_for_pytorch as ipex
import logging
import os
import sentence_transformers
import torch

from contextlib import nullcontext
from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)

# The handler is responsible for defining how a model processes incoming requests during inference

class EmbeddingHandler(BaseHandler, ABC):
    def __init__(self):
        super(EmbeddingHandler, self).__init__()
        self.batch_size = None
        self.initialized = False


    def initialize(self, ctx : Context):
        model_name = str(os.getenv('TORCHSERVE_MODEL_NAME'))
        if not model_name:
                raise ValueError("The 'TORCHSERVE_MODEL_NAME' cannot be empty.")

        self.device_type = str(os.getenv('TORCHSERVE_DEVICE_TYPE', "cpu")).lower()
        self.batch_size = int(os.getenv('TORCHSERVE_BATCH_SIZE'))
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
        logger.info(f"TORCHSERVE_BATCH_SIZE is set to {self.batch_size}.")
        logger.info(f"TORCHSERVE_AMP_DTYPE is set to {self.amp_dtype}.")

        try:
            ipex._C.disable_jit_linear_repack()
            torch._C._jit_set_texpr_fuser_enabled(False)
        except Exception:
            logger.warning("Failed to execute ipex._C.disable_jit_linear_repack() and torch._C._jit_set_texpr_fuser_enabled(False). Proceeding without it.")
            pass

        try:
            self.model = sentence_transformers.SentenceTransformer(model_name)
            self.model = self.model.to(memory_format=torch.channels_last)
            self.model.eval()

            self.model = ipex.llm.optimize(
                self.model,
                dtype=self.amp_dtype,
                inplace=True,
                deployment_mode=True,
            )
            self.initialized = True
            logger.info(f"Model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model '{model_name}': {str(e)}")
            raise


    def preprocess(self, requests):
        texts = []
        logger.debug(f"Received requests: {requests}")

        bodies = [data.get("data") or data.get("body") for data in requests]

        for body in bodies:
            input_text = body['inputs']

            t_b = [t.strip().replace("\n", " ") for t in input_text]
            texts.append(t_b)

        logger.debug(f"Received texts: {texts}")
        return texts

    def _run_embedding_model(self, input_batch):
        with torch.inference_mode(), torch.no_grad(), self.additional_context:
            embeddings = self.model.encode(input_batch, batch_size=self.batch_size)
        
        return embeddings.tolist()

    def inference(self, input_batch):
        logger.debug(f"Received input_batch: {input_batch}")

        if len(input_batch) > 1:
            # Batching detected
            texts = []
            num_texts_in_batch = []
            
            for text_pair in input_batch:
                num_texts_in_batch.append(len(text_pair))
                texts.extend(text_pair)
    
            embeddings = self._run_embedding_model(texts)
            
            og_embeddings = []
            index = 0
            for count in num_texts_in_batch:
                og_embeddings.append(embeddings[index:index + count])
                index += count
            return og_embeddings
            
        else:
            # No Batching detected
            input_batch = input_batch[0]
            embeddings = self._run_embedding_model(input_batch)
            return [embeddings]


    def postprocess(self, inference_output):
        return inference_output
