# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import aiohttp
import asyncio
from typing import List, Any, Optional

from comps import get_opea_logger
from comps.embeddings.utils.connectors.connector import EmbeddingConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class TorchServeConnector(EmbeddingConnector):
    """
    Connector for TorchServe embedding models.

    This connector communicates with TorchServe servers through their /predictions endpoint
    using direct HTTP calls. This avoids compatibility issues with HuggingFace client API
    changes and allows passing custom parameters like return_pooling.
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

        self._endpoint = self._endpoint.rstrip('/')
        self._prediction_url = f"{self._endpoint}/predictions/{self._model_name.split('/')[-1]}"
        self._timeout = 120

        if api_config is not None:
            self._set_api_config(api_config)

        asyncio.run(self._validate())

    async def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.
            **kwargs: Additional parameters passed to TorchServe (e.g., return_pooling).

        Returns:
            List[List[float]]: The embedded documents.
        """
        texts = [text.replace("\n", " ") for text in texts]
        return_pooling = kwargs.get("return_pooling", False)

        payload = {
            "inputs": texts,
            "parameters": {"return_pooling": return_pooling},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._prediction_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._timeout),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(
                            f"TorchServe error (status {response.status}): {error_text}"
                        )
                    output = await response.json(content_type=None)
        except aiohttp.ClientError as e:
            logger.exception(f"Error embedding documents: {e}")
            raise
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
            result = await self.embed_documents(texts=[text])
            if len(result) == 1 and isinstance(result[0], list):
                return result[0]
            return result
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise
