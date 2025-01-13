# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# TODO: Implement a Generic Connector

import concurrent
import os
import yaml

from fastapi import HTTPException
from typing import Union

from comps import get_opea_logger
from comps.cores.proto.docarray import EmbedDoc, EmbedDocList, TextDoc, TextDocList

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEAEmbedding:
    """
    Singleton class for managing embeddings with different frameworks as a connector and model servers.
    This class ensures that only one instance is created and reused across the application.
    """

    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str, connector: str):

        if cls._instance is None:
            cls._instance = super(OPEAEmbedding, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, connector)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server or
                cls._instance._connector != connector):
                logger.warning(f"Existing OPEAEmbedding instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              f"{cls._instance._connector} != {connector}. "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str, connector: str) -> None:
        """
        Initializes the OPEAEmbedding instance.

        Args:
            model_name (str): The full name of the model, which may include the repository ID (e.g., 'BAAI/bge-large-en-v1.5'). 
                      Internally, only the short name (the last part after the final '/') will be used. For instance, 
                      'bge-large-en-v1.5' will be extracted from 'BAAI/bge-large-en-v1.5'.
                      
            model_server (str): The URL of the model server.
            endpoint (str): The endpoint for the model server.
            connector (str): The name of the connector framework to be used.
        """
        self._model_name = model_name.split('/')[-1].lower()    # Extract the last part of the model name
        self._model_server = model_server.lower()
        self._endpoint = endpoint
        self._connector = connector.lower()
        self._APIs = []

        self._api_config = None
        if self._is_api_based():
            self._api_config = self._get_api_config()

        self._SUPPORTED_FRAMEWORKS = {
            "langchain": self._import_langchain,
            "llama_index": self._import_llamaindex
        }

        if self._connector not in self._SUPPORTED_FRAMEWORKS:
            logger.error(f"Unsupported framework: {self._connector}. "
                          f"Supported frameworks: {list(self._SUPPORTED_FRAMEWORKS.keys())}")
            raise NotImplementedError(f"Unsupported framework: {self._connector}.")
        else:
            self._SUPPORTED_FRAMEWORKS[self._connector]()

    def run(self, input: Union[TextDoc, TextDocList]) -> Union[EmbedDoc, EmbedDocList]:
        """
        Processes the input document using the OPEAEmbedding.

        Args:
            input (Union[TextDoc, TextDocList]): The input document to be processed.

        Returns:
            Union[EmbedDoc, EmbedDocList]: The processed document.
        """

        docs = []
        if isinstance(input, TextDoc):
            if input.text.strip() == "":
                raise HTTPException(status_code=400, detail="Input text is empty. Provide a valid input text.")

            embed_vector = self.embed_query(input.text)
            res = EmbedDoc(text=input.text, embedding=embed_vector, metadata=input.metadata)
            return res # return EmbedDoc
        else:
            docs_to_parse = input.docs

            docs_to_parse = [s for s in docs_to_parse if s.text.strip()]
            if len(docs_to_parse) == 0:
                raise HTTPException(status_code=400, detail="Input text is empty. Provide a valid input text.")

            # Multithreaded executor is needed to enabled batching in the model server
            def multithreaded_embed_query(doc):
                res_vector = self.embed_query(doc.text)
                return EmbedDoc(text=doc.text, embedding=res_vector, metadata=doc.metadata)

            # Hardcoded to 4 workers per request
            # TODO: Make the number of workers configurable
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                f = [executor.submit(multithreaded_embed_query, doc) for doc in docs_to_parse]
                docs = [future.result() for future in concurrent.futures.as_completed(f)]

            return EmbedDocList(docs=docs) # return EmbedDocList

    def _import_langchain(self) -> None:
        try:
            from comps.embeddings.utils.wrappers import wrapper_langchain
            self.embed_query = wrapper_langchain.LangchainEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_query
            self.embed_documents = wrapper_langchain.LangchainEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_documents
            self.validate_method = wrapper_langchain.LangchainEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config)._validate
        except ModuleNotFoundError:
            logger.exception("langchain module not found. Ensure it is installed if you need its functionality.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while initializing the wrapper_langchain module {e}")
            raise

    def _import_llamaindex(self) -> None:
        try:
            from comps.embeddings.utils.wrappers import wrapper_llamaindex
            self.embed_query = wrapper_llamaindex.LlamaIndexEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_query
            self.embed_documents = wrapper_llamaindex.LlamaIndexEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config).embed_documents
            self.validate_method = wrapper_llamaindex.LlamaIndexEmbedding(self._model_name, self._model_server, self._endpoint, self._api_config)._validate
        except ModuleNotFoundError:
            logger.exception("llama_index module not found. Ensure it is installed if you need its functionality.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while initializing the wrapper_llamaindex module: {e}")
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
