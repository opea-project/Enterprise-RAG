# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from typing import List, Optional

from comps import get_opea_logger
from comps.embeddings.utils.wrappers.wrapper import EmbeddingWrapper

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


def texts_to_single_line(texts: List[str]) -> List[str]:
    return [text.replace("\n", " ") for text in texts]

class MosecEmbeddings(HuggingFaceEndpointEmbeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        input_data = texts_to_single_line(texts)
        try:
            responses = self.client.post(
                json={"inputs": input_data}
            )

            return json.loads(responses.decode())["embedding"]

        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

class OVMSEndpointEmbeddings(HuggingFaceEndpointEmbeddings):
    """
    Implementation of OVMSEndpoint with usage of HuggingFaceEndpointEmbeddings.
    Attributes:
        model_name (str): The name of the model.
        input_name (str): The name of the input. Defaults to None.
    Methods:
        get_input_name(url: str) -> str:
            Retrieves the input name from the model.
        embed_documents(texts: List[str]) -> List[List[float]]:
            Embeds a list of documents and returns the embeddings as a list of lists of floats.
    """

    model_name: str
    input_name: str = None

    def get_input_name(self, url: str) -> str:
        if self.input_name is None:
            import requests
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
                self.input_name = json.loads(response.text)["inputs"][0]["name"]
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise
            except KeyError as e:
                logger.error(f"Key error: {e}")
                raise
        return self.input_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        endpoint = f"v2/models/{self.model_name}"
        url = f"{self.model}/{endpoint}"

        try:
            from huggingface_hub import (
                    InferenceClient,
                )
            self.client = InferenceClient(
                    model=f"{url}/infer",
                )
        except ImportError as e:
            error_message =  "Could not import huggingface_hub python package.\n" \
                             "Please install it with `pip install huggingface_hub`.\n"  \
                             f"Error: {e}"
            logger.exception(error_message)
            raise

        try:
            input_name = self.get_input_name(url)
        except Exception:
            raise

        texts = texts_to_single_line(texts)
        input_data = [{
            "name": input_name,
            "shape": [len(texts)],
            "datatype": "BYTES",
            "data": texts
        }]

        try:
            responses = self.client.post(
                json={"inputs": input_data}
            )
            responses_data = json.loads(responses.decode())
            if "outputs" in responses_data and len(responses_data["outputs"]) > 0:
                embeddings = responses_data["outputs"][0]["data"]
                if embeddings:
                    return [embeddings]
        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

        return []

SUPPORTED_INTEGRATIONS = {
    "tei": HuggingFaceEndpointEmbeddings,
    "torchserve": HuggingFaceEndpointEmbeddings,
    "mosec": MosecEmbeddings,
    "ovms": OVMSEndpointEmbeddings,
}

class LangchainEmbedding(EmbeddingWrapper):
    """
    Wrapper class for language chain embeddings.

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
            cls._instance = super(LangchainEmbedding, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing LangchainEmbedding instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        super().__init__(model_name, model_server, endpoint)
        self._embedder = self._select_embedder()

        if api_config is not None:
            self._set_api_config(api_config)

        self._validate()

    def _select_embedder(self, **kwargs) -> Embeddings:
        """
        Selects the appropriate embedder based on the model server.

        Returns:
            Embeddings: The selected embedder.

        Raises:
            ValueError: If the model server is invalid.
        """
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"
            logger.error(error_message)
            raise ValueError(error_message)

        if "model" not in kwargs:
            if self._model_server == "torchserve":
                self._endpoint = self._endpoint.rstrip('/')
                kwargs["model"] = self._endpoint + f"/predictions/{self._model_name.split('/')[-1]}"
            elif self._model_server == "mosec":
                kwargs["model"] = self._endpoint.rstrip('/') + "/embed"
            else:
                kwargs["model"] = self._endpoint

        if self._model_server == "ovms":
            kwargs["model_name"] = self._model_name

        return SUPPORTED_INTEGRATIONS[self._model_server](**kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.

        Returns:
            List[List[float]]: The embedded documents.
        """
        try:
            output = self._embedder.embed_documents(texts)
        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

        return output

    def embed_query(self, input_text: str) -> List[float]:
        """
        Embeds a query.

        Args:
            input_text (str): The query text.

        Returns:
            List[float]: The embedded query.
        """
        try:
            output = self._embedder.embed_query(input_text)
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
