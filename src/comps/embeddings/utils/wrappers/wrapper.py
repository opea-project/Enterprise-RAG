# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import re
from abc import ABC, abstractmethod
from typing import List, Optional

from docarray import BaseDoc

from comps import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class EmbeddingWrapper(ABC):
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

    def __init__(self, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        self._endpoint = endpoint
        self._model_name = model_name
        self._model_server = model_server

    def _sanitize_input(value: str) -> str:
        """
        Sanitizes the input value to remove potentially harmful content.

        Args:
            value (str): The value to sanitize.

        Returns:
            str: The sanitized value.
        """
        sanitized_value = re.sub(r'[^\w\-]', '', value)
        return sanitized_value

    # TODO: Add additional env checks. Move to separate function available to other microservices.
    def _set_api_config(self, api_config: dict) -> None:
        """
        Sets the API configuration.

        Args:
            api_config (dict): The API configuration.
        """
        for k, v in api_config.items():
            if isinstance(k, str) and isinstance(v, list) and len(v) > 0:
                sanitized_k = self._sanitize_input(k)
                sanitized_v = self._sanitize_input(v[0])
                try:
                    os.environ[sanitized_k] = sanitized_v
                except Exception as e:
                    logger.exception(f"Error setting environment variable {sanitized_k}: {e}")
                    raise
            else:
                logger.warning(f"Invalid configuration for {k}: {v}")

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of documents.

        Args:
            texts (List[str]): The list of documents to embed.

        Returns:
            List[List[float]]: The embedded documents.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, input_text: str) -> BaseDoc:
        """
        Embeds a query.

        Args:
            input_text (str): The query text.

        Returns:
            BaseDoc: The embedded query.
        """
        raise NotImplementedError

    def _validate(self) -> None:
        """
        Validates the embedder by embedding an empty query.

        Raises:
            RuntimeError: If there is an error initializing the embedder.
        """
        try:
            self.embed_query("test")
            logger.info("Embedder model server validated successfully.")
        except RuntimeError as e:
            logger.exception(f"Error initializing the embedder: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise

    @abstractmethod
    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the embedder.

        Args:
            **kwargs: The new configuration parameters.
        """
        raise NotImplementedError
