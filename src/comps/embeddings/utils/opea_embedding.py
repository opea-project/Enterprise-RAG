# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional

import yaml

from comps import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEAEmbedding:
    """
    Singleton class for managing embeddings with different frameworks and model servers.
    """

    _instance = None

    def __new__(cls, model_name: str, model_server: str, framework: Optional[str] = None, endpoint: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(OPEAEmbedding, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, framework, endpoint)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server or
                cls._instance._framework != framework):
                logger.warning(f"Existing OPEAEmbedding instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              f"{cls._instance._framework} != {framework}. "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, framework: Optional[str], endpoint: Optional[str]) -> None:
        """
        Initializes the OPEAEmbedding instance.

        Args:
            model_name (str): The name of the model.
            model_server (str): The model server URL.
            framework (Optional[str]): The framework used for embedding. Defaults to None.
            endpoint (Optional[str]): The endpoint for the model server. Defaults to None.
        """
        self._model_name = model_name.lower()
        self._model_server = model_server.lower()
        self._framework = framework.lower() if framework else None
        self._endpoint = endpoint
        self._APIs = []

        self._api_config = None
        if self._is_api_based():
            self._api_config = self._get_api_config()

        self._SUPPORTED_FRAMEWORKS = {
            "langchain": self._import_langchain,
            "llama_index": self._import_llamaindex
        }

        if self._framework not in self._SUPPORTED_FRAMEWORKS:
            logger.error(f"Unsupported framework: {self._framework}. "
                          f"Supported frameworks: {list(self._SUPPORTED_FRAMEWORKS.keys())}")
            raise NotImplementedError(f"Unsupported framework: {self._framework}.")
        else:
            self._SUPPORTED_FRAMEWORKS[self._framework]()

    def _import_langchain(self) -> None:
        try:
            from comps.embeddings.utils.wrappers import wrapper_langchain
            self.embed_query = wrapper_langchain.LangchainEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_query
            self.embed_documents = wrapper_langchain.LangchainEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_documents
        except ModuleNotFoundError:
            logger.exception("langchain module not found. Ensure it is installed if you need its functionality.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise

    def _import_llamaindex(self) -> None:
        try:
            from comps.embeddings.utils.wrappers import wrapper_llamaindex
            self.embed_query = wrapper_llamaindex.LlamaIndexEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_query
            self.embed_documents = wrapper_llamaindex.LlamaIndexEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_documents
        except ModuleNotFoundError:
            logger.exception("llama_index module not found. Ensure it is installed if you need its functionality.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise

    def _get_api_config(self) -> dict:
        try:
            api_config_path = os.environ.get("API_CONFIG_PATH", os.path.join(os.getcwd(), "utils", "api_config", "api_config.yaml"))
            with open(api_config_path, "r") as config:
                return yaml.safe_load(config)
        except FileNotFoundError as e:
            logger.exception(f"API configuration file not found: {e}")
            raise
        except yaml.YAMLError as e:
            logger.exception(f"Error parsing the API configuration file: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading API configuration: {e}")
            raise

    def _is_api_based(self) -> bool:
        """
        Checks if the model server is API-based.

        Returns:
            bool: True if the model server is API-based, False otherwise.
        """
        if self._model_server in self._APIs:
            return True
        else:
            return False
