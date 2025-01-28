# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Dict, Union

from fastapi.responses import StreamingResponse

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEALlm:
    def __init__(self, model_name: str, model_server: str, model_server_endpoint: str, connector_name: Optional[str] = "generic", disable_streaming: Optional[bool] = False, llm_output_guard_exists: Optional[bool] = True, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the OPEALlm instance with the given parameters.

        :param model_name: Name of the LLM model.
        :param model_server: Server hosting the LLM model.
        :param model_server_endpoint: Endpoint for the LLM model server.
        :param connector_name: Connector name for the LLM.

        Raises:
            ValueError: If any of the required environment variables are missing or empty.
        """
        self._model_name = model_name
        self._model_server = model_server
        self._model_server_endpoint = model_server_endpoint
        self._connector_name = connector_name
        self._disable_streaming = disable_streaming
        self._llm_output_guard_exists = llm_output_guard_exists
        self._headers = headers if headers is not None else {}
        self._validate_config()
        self._connector = self._get_connector()

        logger.info(
            f"OPEA LLM Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _get_connector(self):
        if self._connector_name.upper() == "LANGCHAIN":
            from comps.llms.utils.connectors import langchain_connector
            return langchain_connector.LangchainLLMConnector(self._model_name, self._model_server, self._model_server_endpoint, self._disable_streaming, self._llm_output_guard_exists, self._headers)
        elif self._connector_name.upper() == "GENERIC" or not self._connector_name.strip():
            from comps.llms.utils.connectors import generic_connector
            return generic_connector.GenericLLMConnector(self._model_name, self._model_server, self._model_server_endpoint, self._disable_streaming, self._llm_output_guard_exists, self._headers)
        else:
            raise ValueError(f"Invalid connector name: {self._connector_name}. Expected to be either 'langchain', 'generic', or unset.")

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
