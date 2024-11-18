# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Union

from fastapi.responses import StreamingResponse

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LLMConnector(ABC):
    def __init__(self, model_name: str, model_server: str, endpoint: str):
        """
        Initializes a Connector object.

        Args:
            model_name (str): The name of the model.
            model_server (str): The server hosting the model.
            endpoint (str): The endpoint for the model.

        Returns:
            None
        """
        self._model_name = model_name
        self._model_server = model_server
        self._endpoint = endpoint

    @abstractmethod
    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        logger.error("generate method in LLMConnector is abstract.")
        raise NotImplementedError

    def _validate(self) -> None:
        try:
            tested_params = {"query": "test", "max_new_tokens": 5}
            test_input = LLMParamsDoc(**tested_params, streaming=False)
            self.generate(test_input)
            logger.info("Connection with LLM model server validated successfully.")
        except Exception as e:
            logger.exception(f"Error initializing the LLM: {e}")
            raise RuntimeError(f"Error initializing the LLM: {e}")

    @abstractmethod
    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the embedder.
        Args:
            **kwargs: The new configuration parameters.
        """
        logger.error("change_configuration method in LLMConnector is abstract.")
        raise NotImplementedError