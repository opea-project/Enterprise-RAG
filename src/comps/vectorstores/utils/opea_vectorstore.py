# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional
from comps.cores.mega.logger import get_opea_logger
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")

class OPEAVectorStore():
    """
    A class representing a vector store for OPEA.
    Args:
        vector_store (str, optional): The type of vector store to use. Defaults to None.
    Attributes:
        _vector_store_name (str): The name representing the vector store.
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

    def _initialize(self, vector_store_name: str):
        """
        Initializes the OPEAVectorStore instance.
        Args:
            vector_store_name (str): The name representing the vector store.
        """
        self._vector_store_name = vector_store_name

        self._SUPPORTED_VECTOR_STORES = {
            "redis": self._import_redis
        }

        if self._vector_store_name not in self._SUPPORTED_VECTOR_STORES:
            err_msg = f"Unsupported vector store: {self._vector_store_name}.\nSupported vector stores: {[vs for vs in self._SUPPORTED_VECTOR_STORES]}"
            logger.error(err_msg)
            raise ValueError(err_msg)
        else:
            logger.info(f"Loading {self._vector_store_name}")
            self._SUPPORTED_VECTOR_STORES[self._vector_store_name]()

    def add_texts(self, input: List[EmbedDoc]) -> List[str]:
        """
        Adds texts to the vector store.
        Args:
            input (List[EmbedDoc]): The list of texts to add.
        Returns:
            List[str]: List of ids added to the vector store.
        """
        return self.vector_store.add_texts(input=input)

    def delete_texts(self, search_field_name: str, search_field_value: str) -> None:
        """
        Deletes texts from the vector store based on field name and value
        """
        return self.vector_store.search_and_delete_documents(
            index_name=f"{search_field_name}_index",
            field_name=search_field_name,
            field_value=search_field_value,
            prefix_name="doc:default_index"
        )

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
            search_res = self.vector_store.similarity_search_by_vector(input.text, input.embedding, input.k)
        elif input.search_type == "similarity_distance_threshold":
            if input.distance_threshold is None:
                raise ValueError("distance_threshold must be provided for similarity_distance_threshold retriever")
            search_res = self.vector_store.similarity_search_by_vector(input.text, input.embedding, input.k, input.distance_threshold)
        elif input.search_type == "similarity_score_threshold":
            raise NotImplementedError("similarity_score_threshold is not implemented")
            # search_res = self.vector_store.similarity_search_with_relevance_scores(input.text, input.embedding, input.k, input.score_threshold)
        elif input.search_type == "mmr":
            search_res = self.vector_store.max_marginal_relevance_search(input.text, input.embedding, input.k, input.fetch_k, input.lambda_mult)
        else:
            raise ValueError(f"Invalid search type: {input.search_type}")
        return search_res

    def _import_redis(self):
        """
        Imports the RedisVectorStore connector.
        """
        try:
            from comps.vectorstores.utils.connectors import connector_redis
            self.vector_store = connector_redis.RedisVectorStore()
        except ModuleNotFoundError:
            logger.exception("exception when loading RedisVectorStore")
