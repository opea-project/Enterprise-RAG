# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Optional, Dict, Union

from fastapi.responses import StreamingResponse

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class AbstractConnector(ABC):
    def __init__(self, model_name: str, endpoint: str, disable_streaming: bool, llm_output_guard_exists: bool, insecure_endpoint: bool = False, headers: Optional[Dict[str, str]] = None):
        """
        Initializes a AbstractConnector object.

        Args:
            model_name (str): The name of the model.
            endpoint (str): The endpoint for the model.
            disable_streaming (bool): Whether to disable streaming.
            llm_output_guard_exists (bool): Whether LLM output guard exists.
            insecure_endpoint (bool): Whether the endpoint is insecure.
            headers (Optional[Dict[str, str]]): Optional headers for requests.

        Returns:
            None
        """
        self._model_name = model_name
        self._endpoint = endpoint
        self._disable_streaming = disable_streaming
        self._headers = headers if headers is not None else {}
        self._llm_output_guard_exists = llm_output_guard_exists
        self._insecure_endpoint = insecure_endpoint

    @abstractmethod
    async def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        logger.error("generate method in AbstractConnector is abstract.")
        raise NotImplementedError
    
    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    async def _validate(self) -> None:
        try:
            tested_params = {"messages": [{"role": "system", "content": "test"}, {"role": "user", "content": "test"}], "max_new_tokens": 5}
            test_input = LLMParamsDoc(**tested_params, stream=False)
            await self.generate(test_input)
            logger.info("Connection with LLM model server validated successfully.")
        except Exception as e:
            error_message = f"Error initializing the LLM: {e}"
            logger.exception(error_message)
            raise
