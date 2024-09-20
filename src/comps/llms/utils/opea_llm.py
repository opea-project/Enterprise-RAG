import os
from typing import Optional, Union

from fastapi.responses import StreamingResponse

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEALlm:
    def __init__(self):
        """
        Initializes the OPEA LLM Microservice.

        The OPEA LLM Microservice is responsible for sending requests to a specified model server endpoint.
        The configuration parameters are read from environment variables.

        Environment Variables:
            - LLM_MODEL_NAME: The name of the LLM model.
            - LLM_MODEL_SERVER: The address of the LLM model server.
            - LLM_CONNECTOR (Optional): The connector to be used for the LLM model.
            - LLM_MODEL_SERVER_ENDPOINT: The endpoint of the LLM model server.

        Raises:
            ValueError: If any of the required environment variables are missing or empty.

        """

        self._model_name: str = _sanitize(os.getenv('LLM_MODEL_NAME'))
        self._model_server: str = _sanitize(os.getenv('LLM_MODEL_SERVER'))
        self._model_server_endpoint: str = _sanitize(os.getenv('LLM_MODEL_SERVER_ENDPOINT'))
        self._connector: Optional[str] = _sanitize(os.getenv('LLM_CONNECTOR'))

        self._validate_config()
        self._connector = self._get_connector()

        logger.info(
            f"OPEA LLM Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _get_connector(self):
        if self._connector.upper() == "LANGCHAIN":
            from comps.llms.utils.connectors.wrappers import wrapper_langchain
            return wrapper_langchain.LangchainLLMConnector(self._model_name, self._model_server, self._model_server_endpoint)
        else:
            from comps.llms.utils.connectors import generic
            return generic.GenericLLMConnector(self._model_name, self._model_server, self._model_server_endpoint)

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

    def run(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        return self._connector.generate(input)


def _sanitize(value: str) -> str:
    """Remove quotes from a configuration value if present.

    Args:
        value (str): The configuration value to sanitize.

    Returns:
        str: The sanitized configuration value.

    """
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    elif value.startswith('\'') and value.endswith('\''):
        value = value[1:-1]
    return value