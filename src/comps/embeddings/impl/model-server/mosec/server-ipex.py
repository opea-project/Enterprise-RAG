# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import json
import yaml
from typing import List, Union

import intel_extension_for_pytorch as ipex
import torch  # type: ignore
import torch.nn.functional as F  # type: ignore
import transformers  # type: ignore
from llmspec.mixins import JSONSerializableMixin
from msgspec import Struct
from mosec import Runtime, Server, Worker, get_logger

logger = get_logger()

class EmbRequest(Struct, kw_only=True):
    input: str


class EmbResponse(Struct, JSONSerializableMixin, kw_only=True):
    embedding: List[float]


class Embedding(Worker):
    def __init__(self):
        with open('model-config.yaml', 'r') as file:
            model_config = yaml.safe_load(file)
        self.model_name = model_config["model_name"]
        self.amp_dtype = model_config["amp_dtype"]

        logger.debug(f"Loading model: {self.model_name}")
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name)
        self.model = transformers.AutoModel.from_pretrained(self.model_name)
        self.device = "cpu"

        if self.amp_dtype == "BF16":
            self.amp_enabled = True
            self.amp_dtype = torch.bfloat16
        else:
            self.amp_enabled = False
            self.amp_dtype = torch.float32

        self.model = self.model.to(memory_format=torch.channels_last).to(self.device)
        self.model.eval()

        self.model = ipex.llm.optimize(
            self.model,
            dtype=self.amp_dtype,
            inplace=True,
            deployment_mode=True,
        )

        logger.info("Running warm-up runs")
        with torch.inference_mode(), torch.no_grad(), torch.autocast(
            device_type="cpu",
            enabled=self.amp_enabled,
            dtype=self.amp_dtype,
            ):
            for _ in range(5):
                self.get_embedding("test")

        logger.info("Model loaded successfully")

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
        inputs = encoded_input.to(self.device)
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
            device_type="cpu",
            enabled=self.amp_enabled,
            dtype=self.amp_dtype,
            ):
            embeddings = self.get_embedding(inputs)

        embeddings = embeddings.detach()
        if self.device != "cpu":
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
    MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", 32))
    MAX_WAIT_TIME = int(os.environ.get("MAX_WAIT_TIME", 100))
    server = Server()
    emb = Runtime(Embedding, max_batch_size=MAX_BATCH_SIZE, max_wait_time=MAX_WAIT_TIME)
    server.register_runtime(
        {
            "/v1/embeddings": [emb],
            "/embeddings": [emb],
        }
    )
    server.run()
