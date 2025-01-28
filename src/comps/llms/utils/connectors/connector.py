# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Union

from fastapi.responses import StreamingResponse
from requests.exceptions import ConnectionError, ReadTimeout

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LLMConnector(ABC):
    def __init__(self, model_name: str, model_server: str, endpoint: str, disable_streaming: bool, llm_output_guard_exists: bool, headers: Optional[Dict[str, str]] = None):
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
        self._disable_streaming = disable_streaming
        self._headers = headers if headers is not None else {}
        self._llm_output_guard_exists = llm_output_guard_exists

    @abstractmethod
    async def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        logger.error("generate method in LLMConnector is abstract.")
        raise NotImplementedError

    def _validate(self) -> None:
        try:
            tested_params = {"query": "test", "max_new_tokens": 5}
            test_input = LLMParamsDoc(**tested_params, streaming=False)
            asyncio.run(self.generate(test_input))
            logger.info("Connection with LLM model server validated successfully.")
        except ReadTimeout as e:
            error_message = f"Error initializing the LLM: {e}"
            logger.exception(error_message)
            raise ReadTimeout(error_message)
        except ConnectionError as e:
            error_message = f"Error initializing the LLM: {e}"
            logger.exception(error_message)
            raise ConnectionError(error_message)
        except Exception as e:
            error_message = f"Error initializing the LLM: {e}"
            logger.exception(error_message)
            raise Exception(error_message)

    @abstractmethod
    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the embedder.
        Args:
            **kwargs: The new configuration parameters.
        """
        logger.error("change_configuration method in LLMConnector is abstract.")
        raise NotImplementedError