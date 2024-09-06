# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Optional

from comps.cores.proto.docarray import EmbedDoc, SearchedDoc

class OPEAVectorStore():
    """
    A class representing a vector store for OPEA.
    Args:
        vector_store (str, optional): The type of vector store to use. Defaults to None.
    Attributes:
        _vector_store_key (str): The key representing the vector store.
        _SUPPORTED_VECTOR_STORES (dict): A dictionary mapping supported vector stores to their corresponding import methods.
        vector_store: The instance of the vector store.
    Methods:
        add_texts(input: List[EmbedDoc]) -> Any:
            Adds texts to the vector store.
        search(input: EmbedDoc) -> SearchedDoc:
            Performs a search in the vector store based on the input.
    """

    _instance = None
    def __new__(cls, vector_store: Optional[str] = None):
        """
        Creates a new instance of the OPEAVectorStore class.
        Args:
            vector_store (str, optional): The type of vector store to use. Defaults to None.
        Returns:
            OPEAVectorStore: The OPEAVectorStore instance.
        """
        if cls._instance is None:
            cls._instance = super(OPEAVectorStore, cls).__new__(cls)
            cls._instance._initialize(vector_store)
        return cls._instance

    def _initialize(self, vector_store_key: str):
        """
        Initializes the OPEAVectorStore instance.
        Args:
            vector_store_key (str): The key representing the vector store.
        """
        self._vector_store_key = vector_store_key

        self._SUPPORTED_VECTOR_STORES = {
            "redis": self._import_redis,
            "qdrant": self._import_qdrant,
            "milvus": self._import_milvus
        }

        if self._vector_store_key not in self._SUPPORTED_VECTOR_STORES:
            logging.error(f"Unsupported vector store: {self._vector_store_key}.\nSupported vector stores: {[vs for vs in self._SUPPORTED_VECTOR_STORES]}")
        else:
            logging.info(f"Loading {self._vector_store_key}")
            self._SUPPORTED_VECTOR_STORES[self._vector_store_key]()

    def add_texts(self, input: List[EmbedDoc]) -> List[str]:
        """
        Adds texts to the vector store.
        Args:
            input (List[EmbedDoc]): The list of texts to add.
        Returns:
            List[str]: List of ids added to the vector store.
        """
        return self.vector_store.add_texts(input=input)

    def search(self, input: EmbedDoc) -> SearchedDoc:
        """
        Performs a search in the vector store based on the input.
        Args:
            input (EmbedDoc): The input for the search.
        Returns:
            SearchedDoc: The result of the search.
        """
        search_res = None
        if input.search_type == "similarity":
            search_res = self.vector_store.similarity_search_by_vector(input=input)
        elif input.search_type == "similarity_distance_threshold":
            if input.distance_threshold is None:
                raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
            search_res = self.vector_store.similarity_search_by_vector(input=input)
        elif input.search_type == "similarity_score_threshold":
            raise NotImplementedError
        elif input.search_type == "mmr":
            search_res = self.vector_store.max_marginal_relevance_search(input=input)
        return search_res

    def _import_redis(self):
        """
        Imports the RedisVectorStore wrapper.
        """
        try:
            from comps.vectorstores.utils.wrappers import wrapper_redis
            self.vector_store = wrapper_redis.RedisVectorStore()
        except ModuleNotFoundError:
            logging.exception("exception when loading RedisVectorStore")

    def _import_qdrant(self):
        """
        Imports the QdrantVectorStore wrapper.
        """
        try:
            from comps.vectorstores.utils.wrappers import wrapper_qdrant
            self.vector_store = wrapper_qdrant.QdrantVectorStore()
        except ModuleNotFoundError:
            logging.exception("exception when loading QdrantVectorStore")

    def _import_milvus(self):
        """
        Imports the MilvusVectorStore wrapper.
        """
        try:
            from comps.vectorstores.utils.wrappers import wrapper_milvus
            self.vector_store = wrapper_milvus.MilvusVectorStore()
        except ModuleNotFoundError:
            logging.exception("exception when loading MilvusVectorStore")
