# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import requests
from typing import List

from langchain.embeddings.base import Embeddings as LangchainEmbeddings

from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class Embeddings(LangchainEmbeddings):
    def __init__(self, embedding_service_endpoint: str):
        self.embedding_service_endpoint = embedding_service_endpoint
        self.headers = {"Content-Type": "application/json"}

    def embed_documents(self, texts: List[str], batch_size: int = 128) -> List[List[float]]:
        """
        Generates embeddings for a list of input texts using the OPEA embedding microservice.

        Args:
            texts (List[str]): List of input text strings to embed.
            batch_size (int): Max texts per request (default: 128)
        Note:
            The default `batch_size` of 128 matches the value used by the embedding service during the embedding phase.
            At the moment, it is not configurable at runtime in SemanticSplitter.
        Returns:
            List[List[float]]: A list of embedding vectors corresponding to the input texts.
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            texts_batch = texts[i:i+batch_size]
            payload = {
                "docs": [{"text": t} for t in texts_batch]
            }
            try:
                logger.debug("Sending request to embedding usvc")
                response = requests.post(self.embedding_service_endpoint, json=payload, headers=self.headers)
                response.raise_for_status()
                logger.debug(f"Received response {response.status_code}")
                batch_embeddings = [doc["embedding"] for doc in response.json()["docs"]]
                embeddings.extend(batch_embeddings)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error connecting to embedding service {self.embedding_service_endpoint}, err: {e}")
                raise RuntimeError(f"Error connecting to embedding service {self.embedding_service_endpoint}, err: {e}")

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def aembed_query(self, text: str) -> list[float]:
        raise NotImplementedError
