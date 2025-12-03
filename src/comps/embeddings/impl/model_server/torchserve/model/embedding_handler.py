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
import orjson

from contextlib import nullcontext
from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)

# List of models that require trust_remote_code=True for proper functionality.
TRUSTED_MODELS = [
    "jinaai/jina-embeddings-v2-base-en",
    "jinaai/jina-embeddings-v3"
    # Add more trusted models here as needed
]

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
            trust_remote_code = False
            if model_name.lower() in TRUSTED_MODELS:
                logger.info(f"Model '{model_name}' is in trusted list. Loading with trust_remote_code=True.")
                trust_remote_code = True

            self.model = sentence_transformers.SentenceTransformer(model_name, device=self.device_type, trust_remote_code=trust_remote_code)

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

        bodies = [data.get("data") or data.get("body") for data in requests]

        for body in bodies:
            input_text = body['inputs']
            parameters = body.get('parameters', {})

            t_b = [t.strip().replace("\n", " ") for t in input_text]

            texts.append({"text": t_b, "return_pooling": parameters.get("return_pooling", False)})

        return texts


    def _run_embedding_model(self, input_batch, return_pooling=False):
        if return_pooling:
            # for late chunking use case
            logger.debug("The parameter return_pooling is set to True. Generating embeddings using model output's last_hidden_state.")
            with torch.inference_mode(), torch.no_grad(), self.additional_context:
                inputs = self.model.tokenizer(input_batch, padding=True, truncation=True, return_tensors='pt')
                model_output = self.model._first_module().auto_model(**inputs)
                embeddings = model_output.last_hidden_state
                return embeddings.tolist()

        else:
            # standard use case
            logger.debug("The parameter return_pooling is set to False. Generating embeddings using model.encode().")
            with torch.inference_mode(), torch.no_grad(), self.additional_context:
                embeddings = self.model.encode(input_batch, batch_size=self.batch_size)
                return embeddings.tolist()


    def inference(self, input_batch):
        logger.debug(f"Received input_batch: {input_batch}")

        if len(input_batch) > 1:
            #Batching detected
            num_texts_in_batch = []
            pooling_flags = []
            
            for text_pair in input_batch:
                num_texts_in_batch.append(len(text_pair["text"])) # record text length
                pooling_flags.append(text_pair["return_pooling"]) # record pooling flag (boolean)


            pooling_texts = [t["text"] for t in input_batch if t.get("return_pooling", False)]
            non_pooling_texts = [t["text"] for t in input_batch if not t.get("return_pooling", False)]

            # compute embeddings separately for each group
            embeddings_pooling = []
            embeddings_non_pooling = []

            if pooling_texts:
                    # Flatten the list of text arrays into a single list
                    num_texts_in_pooling_texts = []
                    texts = []
                    for text_pair in pooling_texts:
                        num_texts_in_pooling_texts.append(len(text_pair))
                        texts.extend(text_pair)
            

                    embeddings_pooling = self._run_embedding_model(
                        texts,
                        return_pooling=True
                    )


            if non_pooling_texts:
                # Flatten the list of text arrays into a single list
                num_texts_in_non_pooling_texts = []
                texts = []
                for text_pair in non_pooling_texts:
                    num_texts_in_non_pooling_texts.append(len(text_pair))
                    texts.extend(text_pair)

                embeddings_non_pooling = self._run_embedding_model(
                    texts,
                    return_pooling=False
                )
 
            # Regroup embeddings based on the original structure
            # For pooling embeddings, regroup based on num_texts_in_pooling_texts
            regrouped_pooling = []

            if pooling_texts:
                index = 0
                for count in num_texts_in_pooling_texts:
                    regrouped_pooling.append(embeddings_pooling[index:index + count])
                    index += count

            # For non-pooling embeddings, regroup based on num_texts_in_non_pooling_texts
            regrouped_non_pooling = []

            if non_pooling_texts:
                index = 0
                for count in num_texts_in_non_pooling_texts:
                    regrouped_non_pooling.append(embeddings_non_pooling[index:index + count])

                    index += count

            # Merge the results for pooling and non-pooling texts in the original order
            embeddings = []
            pooling_index = 0
            non_pooling_index = 0

            for flag in pooling_flags:
                if flag:
                    embeddings.append(regrouped_pooling[pooling_index])

                    pooling_index += 1
                else:
                    embeddings.append(regrouped_non_pooling[non_pooling_index])

                    non_pooling_index += 1
            
            return embeddings
            
        else:
            # No Batching detected
            logger.debug("No Batching detected")
            input_batch = input_batch[0]
            embeddings = self._run_embedding_model(input_batch["text"], input_batch["return_pooling"])
            return [embeddings]


    def postprocess(self, inference_output):
        # orjson is significantly faster and produces more compact JSON
        serialized = [orjson.dumps(emb).decode('utf-8') for emb in inference_output]
        return serialized
