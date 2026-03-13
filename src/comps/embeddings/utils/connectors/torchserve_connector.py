# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from typing import List, Any, Optional

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from comps import get_opea_logger
from comps.embeddings.utils.connectors.connector import EmbeddingConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class TorchServeConnector(EmbeddingConnector):
    """
    Connector for TorchServe embedding models.

    This connector communicates with TorchServe servers through their /predictions endpoint,
    using HuggingFaceEndpointEmbeddings as the underlying embedder.
    """

    _instance = None

    def __new__(cls, model_name: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(TorchServeConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, endpoint, api_config)
        else:
            if cls._instance._model_name != model_name:
                logger.warning(f"Existing TorchServeConnector instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, endpoint: str, api_config: Optional[dict] = None):
        """
        Initialize TorchServe Embeddings connector.
        
        Args:
            model_name: Full model identifier (e.g., 'BAAI/bge-base-en')
            endpoint: Base URL of the TorchServe server (e.g., 'http://localhost:8080')
            api_config: Additional configuration for the API
        """
        super().__init__(model_name, endpoint)
        
        self._embedder = self._select_embedder()
   
        if api_config is not None:
            self._set_api_config(api_config)

        asyncio.run(self._validate())

    def _select_embedder(self, **kwargs) -> Embeddings:
        """
        Builds and returns a HuggingFaceEndpointEmbeddings instance pointed at the
        TorchServe predictions endpoint for the configured model.

        Returns:
            Embeddings: A HuggingFaceEndpointEmbeddings instance.
        """
        self._endpoint = self._endpoint.rstrip('/')
        kwargs["model"] = self._endpoint.rstrip('/') + f"/predictions/{self._model_name.split('/')[-1]}"

        return HuggingFaceEndpointEmbeddings(**kwargs)

    async def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.

        Returns:
            List[List[float]]: The embedded documents.
        """
        try:
            self._embedder.model_kwargs = kwargs
            output = await self._embedder.aembed_documents(texts)
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
            output = await self._embedder.aembed_query(text)
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise

        return output
