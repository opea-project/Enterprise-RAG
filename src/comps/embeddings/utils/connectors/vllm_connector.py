# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import aiohttp
import asyncio
from typing import Any, List, Optional

from comps import get_opea_logger
from comps.embeddings.utils.connectors.connector import EmbeddingConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


def texts_to_single_line(texts: List[str]) -> List[str]:
    """Convert texts with newlines to single lines"""
    return [text.replace("\n", " ") for text in texts]


class VLLMConnector(EmbeddingConnector):
    """
    Connector for vLLM embedding models via the OpenAI-compatible API.

    This connector communicates with vLLM servers through their /v1/embeddings endpoint.
    """

    _instance = None

    def __new__(cls, model_name: str, endpoint: str, timeout: int = 60, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(VLLMConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, endpoint, timeout, api_config)
        else:
            if cls._instance._model_name != model_name:
                logger.warning(
                    f"Existing VLLMConnector instance has different parameters: "
                    f"{cls._instance._model_name} != {model_name}"
                    "Proceeding with the existing instance."
                )
        return cls._instance

    def __init__(self, model_name: str, endpoint: str, timeout: int = 60, api_config: Optional[dict] = None):
        # Singleton pattern: all initialization is done once in __new__ -> _initialize.
        # This override prevents EmbeddingConnector.__init__ from being called on every
        # subsequent instantiation attempt, which would reset self._endpoint to the raw
        # URL (without the /v1/embeddings suffix).
        pass

    def _initialize(self, model_name: str, endpoint: str, timeout: int = 60, api_config: Optional[dict] = None):
        """
        Initialize vLLM Embeddings connector.

        Args:
            model_name: Full model identifier, including the organization/namespace (e.g., 'BAAI/bge-base-en')
            endpoint: Base URL of the vLLM server (e.g., 'http://localhost:8108')
            timeout: Timeout for API requests in seconds
            api_config: Additional configuration for the API
        """
        super().__init__(model_name, endpoint, api_config)
        self._endpoint = endpoint.rstrip('/') + '/v1/embeddings'

        self._timeout = timeout

        if api_config is not None:
            self._set_api_config(api_config)

        asyncio.run(self._validate())


    async def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """
        Embed multiple documents asynchronously.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """

        texts = texts_to_single_line(texts)
        input_data = {
            "input": texts,
            "model": self._model_name  # vLLM needs full model name
        }

        if kwargs.get("return_pooling"):
                logger.warning(
                    "The 'return_pooling' argument is not supported for VLLM Connector and will be ignored."
                    )

        try:
            logger.debug(f"vLLM embedding request to {self._endpoint}: {len(texts)} texts")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._endpoint,
                    headers={"Content-Type": "application/json"},
                    json=input_data,
                    timeout=aiohttp.ClientTimeout(total=self._timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=None,
                            status=response.status,
                            message=str(error_text),
                        )

                    result = await response.json()
                    embeddings = [item["embedding"] for item in result.get("data", [])]

                    logger.debug(f"vLLM returned {len(embeddings)} embeddings")
                    return embeddings

        except aiohttp.ClientResponseError as e:
            logger.exception(f"Client response error calling vLLM: {e}")
            raise ValueError(f"vLLM returned an error response: {e.status} - {e.message}")
        except aiohttp.ClientError as e:
            logger.exception(f"Network error calling vLLM: {e}")
            raise ConnectionError(f"Failed to connect to vLLM at {self._endpoint}: {e}")
        except Exception as e:
            logger.exception(f"Error embedding documents with vLLM: {e}")
            raise

        return [] 

    async def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Single embedding vector for the query
        """
        try:
            embeddings = await self.embed_documents([text])
            if embeddings:
                return embeddings[0]
            
            raise ValueError("vLLM returned empty embeddings")
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise
