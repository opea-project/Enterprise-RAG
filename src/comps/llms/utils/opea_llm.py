import configparser
import logging
import os
import sys
from fastapi.responses import StreamingResponse

from comps import (
    LLMParamsDoc,
    GeneratedDoc,
)
from typing import Optional, Union


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
        self._log_level: str
        self._log_path: str
        self._logger: logging.Logger

        self._load_config()
        self._setup_logging()
        self._validate_config()
        self._connector = self._get_connector()

        self._logger.info(
            f"OPEA LLM Microservice has been successfully initialized and is running on {self.host}:{self.port}"
        )
        self._logger.info(
            f"OPEA LLM Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _get_connector(self):
        if self._framework == "langchain":
            from comps.llms.utils.connectors.wrappers import wrapper_langchain
            return wrapper_langchain.LangchainLLMConnector(self._model_name, self._model_server_endpoint, self._model_server)
        else:
            from comps.llms.utils.connectors import generic
            return generic.GenericLLMConnector(self._model_name, self._model_server_endpoint, self._model_server)

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

        # Logging
        self._log_level = os.getenv(
            "LLM_LOG_LEVEL", config.get("Logging", "log_level")
        )
        self._log_path = os.getenv(
            "LLM_LOG_PATH", config.get("Logging", "log_path")
        )

    def _setup_logging(self):
        """Configure the logger based on the log level and log path."""
        log_level = getattr(logging, self._log_level.upper(), logging.INFO)
        log_dir = os.path.dirname(self._log_path)
        try:
            # ensure the log directory exists and is writable
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            elif not os.access(log_dir, os.W_OK):
                raise PermissionError(
                    f"No write permission for the directory '{log_dir}'"
                )
        except (PermissionError, OSError) as e:
            print(f"Failed to create or access the directory '{log_dir}': {e}")
            raise PermissionError(
                f"Failed to create or access the directory '{log_dir}': {e}"
            )

        # Define the log format string
        log_format = "[%(asctime)-15s] [%(levelname)8s] [%(name)s] - %(message)s"

        # Basic logging configuration
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        # Get the logger instance for this class
        self._logger = logging.getLogger(self.__class__.__name__)

        # Create a file handler
        file_handler = logging.FileHandler(self._log_path)
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(log_level)
        self._logger.addHandler(file_handler)

    def _validate_config(self):
        """Validate the configuration values."""
        try:
            if not self._model_name:
                raise ValueError("The 'model_name' cannot be empty.")
            if not self._model_server_endpoint:
                raise ValueError("The 'model_server_endpoint' cannot be empty.")
            if self._log_level.upper() not in logging._nameToLevel:
                raise ValueError(
                    f"The 'log_level' must be one of {list(logging._nameToLevel.keys())}."
                )

        except Exception as err:
            self._logger.error(f"Configuration validation error: {err}")
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