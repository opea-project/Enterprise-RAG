# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Generic connector for embedding model servers that don't fit the HuggingFace pattern.
This includes vLLM with OpenAI-compatible API and other custom implementations.
"""

import aiohttp
import asyncio
from typing import Any, List, Optional

from comps import get_opea_logger
from comps.embeddings.utils.connectors.connector import EmbeddingConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


def texts_to_single_line(texts: List[str]) -> List[str]:
    """Convert texts with newlines to single lines"""
    return [text.replace("\n", " ") for text in texts]


class VLLMEmbeddings:
    """
    Connector for a vLLM embedding server using an OpenAI-compatible API.

    This implementation doesn't rely on HuggingFace classes since vLLM
    uses a different API format (OpenAI embeddings endpoint).
    """
    
    def __init__(self, model_name: str, base_url: str, timeout: int = 60):
        """
        Initialize vLLM Embeddings connector.
        
        Args:
            model_name: Full model identifier, including the organization/namespace (e.g., 'BAAI/bge-base-en')
            base_url: Base URL of the vLLM server (e.g., 'http://localhost:8108')
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.endpoint = base_url.rstrip('/') + '/v1/embeddings'
        self.timeout = timeout


    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
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
            "model": self.model_name  # vLLM needs full model name
        }

        try:
            logger.debug(f"vLLM embedding request to {self.endpoint}: {len(texts)} texts")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    headers={"Content-Type": "application/json"},
                    json=input_data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
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
            raise ConnectionError(f"Failed to connect to vLLM at {self.endpoint}: {e}")
        except Exception as e:
            logger.exception(f"Error embedding documents with vLLM: {e}")
            raise

        return [] 


    async def aembed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Single embedding vector
        """
        try:
            embeddings = await self.aembed_documents([text])
            if embeddings:
                return embeddings[0]
            
            raise ValueError("vLLM returned empty embeddings")
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise


SUPPORTED_INTEGRATIONS = {
    "vllm": VLLMEmbeddings,
   }


class GenericEmbedding(EmbeddingConnector):
    """
    Connector class for language chain embeddings.

    Args:
        model_name (str): The name of the model.
        model_server (str): The model server to use.
        endpoint (str): The endpoint for the model server.
        api_config (Optional[dict]): Additional configuration for the API (default: None).

    Attributes:
        _endpoint (str): The endpoint for the model server.
        _model_server (str): The model server to use.
        _embedder (Embeddings): The selected embedder.
    """
    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(GenericEmbedding, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing GenericEmbedding instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance


    def _initialize(self, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        super().__init__(model_name, model_server, endpoint)
        self._embedder = self._select_embedder()

        if api_config is not None:
            self._set_api_config(api_config)

        asyncio.run(self._validate())


    def _select_embedder(self, **kwargs):
        """
        Selects the appropriate embedder based on the model server.

        Returns:
            An instance of the selected embedder.

        """
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"
            logger.error(error_message)
            raise ValueError(error_message)

        return SUPPORTED_INTEGRATIONS[self._model_server](model_name=self._model_name, base_url=self._endpoint, **kwargs)


    async def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.

        Returns:
            List[List[float]]: The embedded documents.
        """
        try:
            if kwargs.get("return_pooling"):
                logger.warning(
                    "The 'return_pooling' argument is not supported for this LlamaIndex connector and will be ignored."
                    )

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


    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the embedder.

        Args:
            **kwargs: The new configuration parameters.
        """
        self._embedder = self._select_embedder(**kwargs)
