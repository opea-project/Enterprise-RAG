# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import List, Union

import intel_extension_for_pytorch as ipex
import torch  # type: ignore
import torch.nn.functional as F  # type: ignore
import transformers  # type: ignore
from llmspec.mixins import JSONSerializableMixin
from mosec import Runtime, Server, Worker, get_logger
from msgspec import Struct

logger = get_logger()


class EmbRequest(Struct, kw_only=True):
    input: str


class EmbResponse(Struct, JSONSerializableMixin, kw_only=True):
    embedding: List[float]


class Embedding(Worker):
    def __init__(self):
        self.model_name = str(os.getenv('MOSEC_MODEL_NAME'))
        if not self.model_name:
            raise ValueError("The 'MOSEC_MODEL_NAME' cannot be empty.")

        self.device_type = str(os.getenv('MOSEC_DEVICE_TYPE', "cpu")).lower()
        self.amp_dtype = str(os.getenv('MOSEC_AMP_DTYPE'))

        if self.amp_dtype == "BF16":
            self.amp_enabled = True
            self.amp_dtype = torch.bfloat16
        elif self.amp_dtype == "FP32":
            self.amp_enabled = False
            self.amp_dtype = torch.float32

        else:
            error_message = f"Invalid AMP_DTYPE value '{self.amp_dtype}'. Expected 'BF16' or 'FP32'."
            logger.error(error_message)
            raise ValueError(error_message)
        

        logger.info(f"MOSEC_MODEL_NAME is set to {self.model_name}.")
        logger.info(f"MOSEC_DEVICE_TYPE is set to {self.device_type}.")
        logger.info(f"MOSEC_AMP_DTYPE is set to {self.amp_dtype}.")

        logger.debug(f"Loading model: {self.model_name}")
        try:
            # Attempt to load the tokenizer and model from the given model name
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name)
            self.model = transformers.AutoModel.from_pretrained(self.model_name)
        except Exception as e:
            logger.error(f"Error loading model '{self.model_name}': {str(e)}")
            raise
        
        try:
            self.model = self.model.to(memory_format=torch.channels_last).to(self.device_type)
            self.model.eval()
        except Exception as e:
            logger.error(f"Error setting model to device '{self.device_type}': {str(e)}")
            raise

        try:
            self.model = ipex.llm.optimize(
                self.model,
                dtype=self.amp_dtype,
                inplace=True,
                deployment_mode=True,
            )
        except Exception as e:
            logger.error(f"Error optimizing model with IPEX: {str(e)}")
            raise


        logger.info("Running warm-up runs")
        try:
            with torch.inference_mode(), torch.no_grad(), torch.autocast(
                device_type=self.device_type,
                enabled=self.amp_enabled,
                dtype=self.amp_dtype,
                ):
                for _ in range(5):
                    self.get_embedding("test")
        except Exception as e:
            logger.error(f"Error during warm-up runs: {str(e)}")
            raise


        logger.info(f"Model '{self.model_name}' loaded successfully on device '{self.device_type}' with AMP dtype '{self.amp_dtype}'")

    # TODO: utilize sentence-transformers for embeddings
    def get_embedding(self, sentences: Union[str, List[Union[str, List[int]]]]):
        # Mean Pooling - Take attention mask into account for correct averaging
        def mean_pooling(model_output, attention_mask):
            # First element of model_output contains all token embeddings
            token_embeddings = model_output["last_hidden_state"]
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                input_mask_expanded.sum(1), min=1e-9
            )

        # Tokenize sentences
        encoded_input = self.tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")
        inputs = encoded_input.to(self.device_type)
        # Compute token embeddings
        model_output = self.model(**inputs)
        # Perform pooling
        sentence_embeddings = mean_pooling(model_output, inputs["attention_mask"])
        # Normalize embeddings
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

        return sentence_embeddings

    def deserialize(self, data: bytes) -> EmbRequest:
        input_text = json.loads(data.decode("utf-8"))
        logger.info(f"Received input_text: {input_text}")

        return EmbRequest(input=input_text["inputs"])

    def serialize(self, data: EmbResponse) -> bytes:
        logger.info("Inference completed")
        return data.to_json()

    def forward(self, data: List[EmbRequest]) -> List[EmbResponse]:
        inputs = []
        inputs_lens = []
        for d in data:
            inputs.extend(d.input if isinstance(d.input, list) else [d.input])
            inputs_lens.append(len(d.input) if isinstance(d.input, list) else 1)

        with torch.inference_mode(), torch.no_grad(), torch.autocast(
            device_type=self.device_type,
            enabled=self.amp_enabled,
            dtype=self.amp_dtype,
            ):
            embeddings = self.get_embedding(inputs)

        embeddings = embeddings.detach()
        if self.device_type != "cpu":
            embeddings = embeddings.cpu()
        embeddings = embeddings.numpy()
        embeddings = [emb.tolist() for emb in embeddings]

        resp = []
        emb_idx = 0
        for lens in inputs_lens:
            resp.append(
                EmbResponse(
                    embedding=embeddings[emb_idx : emb_idx + lens],
                )
            )
            emb_idx += lens
        return resp


if __name__ == "__main__":
    MAX_BATCH_SIZE = int(os.environ.get("MOSEC_MAX_BATCH_SIZE", 32))
    MAX_WAIT_TIME = int(os.environ.get("MOSEC_MAX_WAIT_TIME", 100))
    logger.info(f"Runtime configuration: MOSEC_MAX_BATCH_SIZE set to {MAX_BATCH_SIZE}, MOSEC_MAX_WAIT_TIME set to {MAX_WAIT_TIME}.")
    logger.info("Initializing server...")

    try:
        server = Server()
        emb = Runtime(Embedding, max_batch_size=MAX_BATCH_SIZE, max_wait_time=MAX_WAIT_TIME)
        server.register_runtime(
            {
                "/embed": [emb],
            }
        )
        server.run()
    except Exception as e:
        logger.error(f"Error running server: {str(e)}")
        raise
