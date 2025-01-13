# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from docarray import BaseDoc
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from typing import List, Optional

from comps import get_opea_logger
from comps.embeddings.utils.wrappers.wrapper import EmbeddingWrapper

SUPPORTED_INTEGRATIONS = {
    "tei": TextEmbeddingsInference,
}

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class LlamaIndexEmbedding(EmbeddingWrapper):
    """
    A class representing an embedding model using LlamaIndex.

    Args:
        model_name (str): The name of the model.
        model_server (str): The server hosting the model.
        endpoint (str): The endpoint for accessing the model.
        **kwargs: Additional keyword arguments for configuring the embedding model.

    Attributes:
        _model_name (str): The name of the model.
        _endpoint (str): The endpoint for accessing the model.
        _model_server (str): The server hosting the model.
        _embedder (BaseEmbedding): The embedder object for performing embedding operations.

    Methods:
        embed_documents(input_text: str) -> BaseDoc: Embeds a document or a list of documents.
        embed_query(input_text: str) -> BaseDoc: Embeds a query.
        change_configuration(**kwargs): Changes the configuration of the embedder.

    Raises:
        Exception: If there is an error initializing the embedder.

    """
    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(LlamaIndexEmbedding, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing LlamaIndexEmbedding instance has different parameters: "
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

    def _select_embedder(self, **kwargs) -> BaseEmbedding:
        """
        Selects the appropriate embedder based on the model server.

        Returns:
            BaseEmbedding: An instance of the selected embedder.

        """
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"
            logger.error(error_message)
            raise ValueError(error_message)

        return SUPPORTED_INTEGRATIONS[self._model_server](model_name=self._model_name, base_url=self._endpoint, **kwargs)

    def embed_documents(self, input_text: List[str]) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.

        Returns:
            List[List[float]]: The embedded document(s).

        """
        try:
            output = self._embedder._get_text_embeddings(input_text)
        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

        return output

    def embed_query(self, input_text: str) -> BaseDoc:
        """
        Embeds a query.

        Args:
            input_text (str): The query text to be embedded.

        Returns:
            BaseDoc: The embedded query.

        """
        try:
            output = self._embedder._get_query_embedding(input_text)
        except Exception as e:
            logger.exception(f"Error embedding query: {e}")
            raise

        return output

    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the embedder.

        Args:
            **kwargs: Additional keyword arguments for configuring the embedder.

        """
        self._embedder = self._select_embedder(**kwargs)
