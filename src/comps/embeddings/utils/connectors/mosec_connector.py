# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from typing import List, Any, Optional

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from comps import get_opea_logger
from comps.embeddings.utils.connectors.connector import EmbeddingConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


def texts_to_single_line(texts: List[str]) -> List[str]:
    return [text.replace("\n", " ") for text in texts]


class MosecConnector(EmbeddingConnector):
    """
    Connector for Mosec embedding models.
    
    This connector communicates with Mosec servers through their /predictions endpoint.
    
    Attributes:
        model_name (str): Full model identifier (e.g., 'BAAI/bge-base-en')
        endpoint (str): Full prediction endpoint URL
        timeout (int): Request timeout in seconds
    """

    _instance = None

    def __new__(cls, model_name: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(MosecConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name):
                logger.warning(f"Existing MosecConnector instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, endpoint: str, api_config: Optional[dict] = None):
        """
        Initialize Mosec Embeddings connector.
        
        Args:
            model_name: Full model identifier (e.g., 'BAAI/bge-base-en')
            endpoint: Base URL of the Mosec server (e.g., 'http://localhost:8108')
            api_config: Additional configuration for the API
        """
        super().__init__(model_name, endpoint)
        
        self._embedder = self._select_embedder()
   
        if api_config is not None:
            self._set_api_config(api_config)

        asyncio.run(self._validate())

    def _select_embedder(self, **kwargs) -> Embeddings:
        """
        Selects the appropriate embedder based on the model server.

        Returns:
            Embeddings: The selected embedder.

        Raises:
            ValueError: If the model server is invalid.
        """

        kwargs["model"] = self._endpoint.rstrip('/') + "/embed"

        return HuggingFaceEndpointEmbeddings(**kwargs)

    async def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.
            **kwargs: Additional keyword arguments.
        Returns:
            List[List[float]]: The embedded documents.
        """

        if kwargs.get("return_pooling"):
            logger.warning(
                "The 'return_pooling' argument is not supported for Mosec Connector and will be ignored."
                )        
        try:
            self._embedder.model_kwargs = kwargs
            input_data = texts_to_single_line(texts)

            responses = await self._embedder.async_client.post(
                json={"inputs": input_data}
            )
            output = json.loads(responses.decode())["embedding"]

        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

        return output

    async def embed_query(self, text: str) -> List[float]:
        """
        Embeds a query.

        Args:
            text (str): The query text.

        Returns:
            List[float]: The embedded query.
        """
    
        try:
            embeddings = await self.embed_documents([text])
            if embeddings:
                return embeddings[0]
            
            raise ValueError("Mosec returned empty embeddings")
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise
