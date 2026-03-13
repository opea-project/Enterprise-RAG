# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from typing import List, Any, Optional

import numpy as np

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from comps import get_opea_logger
from comps.embeddings.utils.connectors.connector import EmbeddingConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


def texts_to_single_line(texts: List[str]) -> List[str]:
    return [text.replace("\n", " ") for text in texts]


class OVMSConnector(EmbeddingConnector):
    """
    Connector for OVMS embedding models.
    
    This connector communicates with OVMS servers through their /predictions endpoint.
    """

    _instance = None
    _input_name: str = None

    def __new__(cls, model_name: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(OVMSConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name):
                logger.warning(f"Existing OVMSConnector instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, endpoint: str, api_config: Optional[dict] = None):
        """
        Initialize OVMS Embeddings connector.
        
        Args:
            model_name: Full model identifier (e.g., 'BAAI/bge-base-en')
            endpoint: Base URL of the OVMS server (e.g., 'http://localhost:8108')
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

        kwargs["model_name"] = self._model_name.split('/')[-1]
        kwargs["model"] = self._endpoint

        return OVMSEndpointEmbeddings(**kwargs)
    
    async def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.
            **kwargs: Additional keyword arguments.
        Returns:
            List[List[float]]: The embedded documents.
        """
        endpoint = f"v2/models/{self._embedder.model_name}"
        url = f"{self._endpoint}/{endpoint}"

        if kwargs.get("return_pooling"):
            logger.warning(
                "The 'return_pooling' argument is not supported for OVMS Connector and will be ignored."
                )   

        try:
            from huggingface_hub import (
                    AsyncInferenceClient,
                )
            self._embedder.async_client = AsyncInferenceClient(
                    model=f"{url}/infer",
                )
        except ImportError as e:
            error_message =  "Could not import huggingface_hub python package.\n" \
                             "Please install it with `pip install huggingface_hub`.\n"  \
                             f"Error: {e}"
            logger.exception(error_message)
            raise

        try:
            input_name = await self._embedder._get_input_name(url)

            texts = texts_to_single_line(texts)
            input_data = [{
                "name": input_name,
                "shape": [len(texts)],
                "datatype": "BYTES",
                "data": texts
            }]

            responses = await self._embedder.async_client.post(
                json={"inputs": input_data}
            )
            responses_data = json.loads(responses.decode())
            if "outputs" in responses_data and len(responses_data["outputs"]) > 0:
                output = responses_data["outputs"][0]
                flat_data = output["data"]
                shape = output["shape"]  # e.g. [batch, tokens, hidden] or [batch, hidden]
                if flat_data:
                    arr = np.array(flat_data).reshape(shape)
                    if arr.ndim == 3:
                        # OVMS returns raw token embeddings [batch, tokens, hidden] — apply mean pooling
                        arr = arr.mean(axis=1)  # -> [batch, hidden]
                    return arr.tolist()

        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

        return []


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
            
            raise ValueError("OVMS returned empty embeddings")
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise

class OVMSEndpointEmbeddings(HuggingFaceEndpointEmbeddings):
    model_name: str
    input_name: Optional[str] = None

    async def _get_input_name(self, url: str) -> str:
        if self.input_name is None:
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response_text = await response.text()
                        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)

                        self.input_name = json.loads(response_text)["inputs"][0]["name"]

            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {e}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise
            except KeyError as e:
                logger.error(f"Key error: {e}")
                raise
        return self.input_name
