# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List
from abc import ABC
from comps.cores.mega.logger import get_opea_logger
from comps.cores.proto.docarray import SearchedDoc

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")

class VectorStoreConnector(ABC):
    """
    Singleton class for interacting with a specific vector store.
    Args:
        batch_size (int): The batch size for adding texts to the vector store.
        index_name (str, optional): The name of the index. Defaults to "default_index".
    Methods:
        add_texts(input: List[EmbedDoc]) -> None:
            Adds texts to the vector store.
        _parse_search_results(input: EmbedDoc, results: Iterable[any]) -> SearchedDoc:
            Parses the search results and returns a SearchedDoc object.
        similarity_search_by_vector(input: EmbedDoc) -> SearchedDoc:
            Performs similarity search by vector and returns a SearchedDoc object.
        similarity_search_with_relevance_scores(input: EmbedDoc) -> SearchedDoc:
            Performs similarity search with relevance scores and returns a SearchedDoc object.
        max_marginal_relevance_search(input: EmbedDoc) -> SearchedDoc:
            Performs max marginal relevance search and returns a SearchedDoc object.
    """
    def __new__(cls):
        """
        Creates a new instance of the VectorStoreConnector class.
        Returns:
            The instance of the VectorStoreConnector class.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(VectorStoreConnector, cls).__new__(cls)
        return cls.instance

    def __init__(self, batch_size: int):
        """
        Initializes the Connector object.
        Args:
            batch_size (int): The batch size for processing.
            index_name (str, optional): The name of the index. Defaults to "default_index".
        """
        self.batch_size = batch_size
        self.client = None

    def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]=None):
        raise NotImplementedError

    def search_and_delete_by_metadata(self, field_name: str, field_value: str):
        raise NotImplementedError

    def similarity_search_by_vector(self, input_text: str, embedding: List, k: int, distance_threshold: float=None, **kwargs) -> SearchedDoc:
        raise NotImplementedError

    def similarity_search_with_relevance_scores(self, input_text: str, embedding: List, k: int, score_threshold: float, **kwargs) -> SearchedDoc:
        raise NotImplementedError

    def max_marginal_relevance_search(self, input_text: str, embedding: List, k: int, fetch_k: float, lambda_mult: float, **kwargs) -> SearchedDoc:
        raise NotImplementedError

    def get_files_filter_expression(self):
        raise NotImplementedError
    
    def get_links_filter_expression(self):
        return NotImplementedError

    def get_bucket_name_filter_expression(self, bucket_names: List[str]):
        raise NotImplementedError

    def get_object_name_filter_expression(self, bucket_name: str, object_name: str):
        raise NotImplementedError
