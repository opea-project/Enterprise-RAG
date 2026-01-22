# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Dict, Union

from fastapi.responses import StreamingResponse

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger
from comps.llms.utils.connectors.vllm_connector import VLLMConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

SUPPORTED_INTEGRATIONS = {
    "vllm": VLLMConnector
}

class OPEALlm:
    def __init__(self, model_name: str, model_server: str, model_server_endpoint: str, insecure_endpoint: bool = False, disable_streaming: Optional[bool] = False, llm_output_guard_exists: Optional[bool] = True, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the OPEALlm instance with the given parameters.

        :param model_name: Name of the LLM model.
        :param model_server: Server hosting the LLM model.
        :param model_server_endpoint: Endpoint for the LLM model server.

        Raises:
            ValueError: If any of the required environment variables are missing or empty.
        """
        self._model_name = model_name
        self._model_server = model_server
        self._model_server_endpoint = model_server_endpoint
        self._disable_streaming = disable_streaming
        self._llm_output_guard_exists = llm_output_guard_exists
        self._insecure_endpoint = insecure_endpoint
        self._headers = headers if headers is not None else {}
        self._validate_config()
        
        self._connector = self._get_connector()

        logger.info(
            f"OPEA LLM Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _get_connector(self):
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"

            logger.error(error_message)
            raise ValueError(error_message)
        kwargs = {
            "model_name": self._model_name,
            "endpoint": self._model_server_endpoint,
            "disable_streaming": self._disable_streaming,
            "llm_output_guard_exists": self._llm_output_guard_exists,
            "insecure_endpoint": self._insecure_endpoint
        }
        if self._model_server == "vllm":
            kwargs["headers"] = self._headers
        return SUPPORTED_INTEGRATIONS[self._model_server](**kwargs)

    def _validate_config(self):
        """Validate the configuration values."""
        try:
            if not self._model_name:
                raise ValueError("The 'LLM_MODEL_NAME' cannot be empty.")
            if not self._model_server_endpoint:
                raise ValueError("The 'LLM_MODEL_SERVER_ENDPOINT' cannot be empty.")
            if not self._model_server:
                raise ValueError("The 'LLM_MODEL_SERVER' cannot be empty.")
        except Exception as e:
            logger.exception(f"Configuration validation error: {e}")
            raise

    async def run(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        return await self._connector.generate(input)
