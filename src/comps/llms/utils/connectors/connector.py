# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from abc import ABC,abstractmethod
from comps import (
    GeneratedDoc,
    LLMParamsDoc,
)
from typing import Union
from fastapi.responses import StreamingResponse

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
        self._endpoint = endpoint
        self._model_server = model_server

    @abstractmethod
    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        raise NotImplementedError

    def _validate(self) -> None:
        try:
            test_input = LLMParamsDoc(query="test")
            self.generate(test_input)
            logging.debug("LLM initialized successfully.")
        except RuntimeError as e:
            logging.error(f"Error initializing the LLM: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise

    @abstractmethod
    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the embedder.
        Args:
            **kwargs: The new configuration parameters.
        """
        raise NotImplementedError