import configparser
import os
from typing import Optional, Union

from fastapi.responses import StreamingResponse

from comps import (
    GeneratedDoc,
    LLMParamsDoc,
    get_opea_logger
)

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEALlm:
    def __init__(self, config_file: str):
        """
        Initializes the OPEA LLM Microservice.
        Args:
            config_file (str): The path to the configuration file.
        Raises:
            FileNotFoundError: If the configuration file is not found.
            ValueError: If the configuration file is invalid.
        """
        self._config_file = config_file
        self.name: str
        self.port: int
        self.host: str
        self._model_name: str
        self._model_server: str
        self._framework: Optional[str] = None
        self._model_server_endpoint: str

        self._load_config()
        self._validate_config()
        self._connector = self._get_connector()

        logger.info(
            f"OPEA LLM Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _get_connector(self):
        if self._framework == "langchain":
            from comps.llms.utils.connectors.wrappers import wrapper_langchain
            return wrapper_langchain.LangchainLLMConnector(self._model_name, self._model_server, self._model_server_endpoint)
        else:
            from comps.llms.utils.connectors import generic
            return generic.GenericLLMConnector(self._model_name, self._model_server, self._model_server_endpoint)

    def _load_config(self):
        """
        Loads the configuration from the specified config file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """

        if not os.path.exists(self._config_file):
            raise FileNotFoundError(
                f"The configuration file {self._config_file} does not exist"
            )

        config = configparser.ConfigParser()
        config.read(self._config_file)

        # Microservice
        self.name = os.getenv(
            "USVC_NAME", _sanitize(config.get("OPEA_Microservice", "name"))
        )
        self.host = os.getenv(
            "USVC_HOST", _sanitize(config.get("OPEA_Microservice", "host"))
        )
        self.port = int(os.getenv(
            "USVC_PORT", config.getint("OPEA_Microservice", "port")
        ))

        # Model
        self._model_name = os.getenv(
            "LLM_NAME", _sanitize(config.get("Model", "model_name"))
        )
        self._model_server_endpoint = os.getenv(
            "LLM_MODEL_SERVER_ENDPOINT", _sanitize(config.get("Model", "model_server_endpoint"))
        )
        self._model_server = os.getenv(
            "MODEL_SERVER", _sanitize(config.get("Model", "model_server"))
        )
        self._framework = os.getenv(
            "FRAMEWORK", _sanitize(config.get("Model", "framework"))
        )

    def _validate_config(self):
        """Validate the configuration values."""
        try:
            if not self._model_name:
                raise ValueError("The 'model_name' cannot be empty.")
            if not self._model_server_endpoint:
                raise ValueError("The 'model_server_endpoint' cannot be empty.")
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
    return value