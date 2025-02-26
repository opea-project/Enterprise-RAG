# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Iterable, List
from abc import ABC
from comps.cores.mega.logger import get_opea_logger
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc, TextDoc

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

    def _check_embedding_index(self, embedding: List):
        """
        Checks if the index exists in the vector store.
        Args:
            embedding (List): The embedding to check.
        """
        try:
            if self.client is not None:
                self.client._create_index_if_not_exist(dim=len(embedding))
        except Exception as e:
            logger.exception("Error occured while checking vector store index")
            raise e

    def add_texts(self, input: List[EmbedDoc]) -> List[str]:
        """
        Add texts to the vector store.
        Args:
            input (List[EmbedDoc]): A list of EmbedDoc objects containing the texts, embeddings, and metadata.
        Returns:
            List[str]: A list of IDs assigned to the added texts.
        """
        texts = [i.text for i in input]
        metadatas = [i.metadata for i in input]
        embeddings = [i.embedding for i in input]
        try:
            ids = self.client.add_texts(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                batch_size=self.batch_size,
                clean_metadata=False
            )
            return ids
        except Exception as e:
            logger.exception("Error occured while adding texts to vector store")
            raise e

    def search_and_delete_by_metadata(self, index_name, field_name, field_value, prefix_name):
        """
        Search and delete documents from the vector store based on filed name and value.
        """
        try:
            return self.client.search_and_delete(field_name, field_value)
        except Exception as e:
            logger.exception("Error occured while deleting documents.")
            raise e

    def _parse_search_results(self, input_text: str, results: Iterable[any]) -> SearchedDoc:
        """
        Parses the search results and returns a `SearchedDoc` object.
        Args:
            input_text (str): The input document used for the search.
            results (Iterable[any]): The search results.
        Returns:
            SearchedDoc: The parsed search results as a `SearchedDoc` object.
        """
        searched_docs = []
        for r in results:
            searched_docs.append(TextDoc(text=r.page_content))
        return SearchedDoc(retrieved_docs=searched_docs, initial_query=input_text)

    def similarity_search_by_vector(self, input_text: str, embedding: List, k: int, distance_threshold: float=None) -> SearchedDoc:
        raise NotImplementedError

    def similarity_search_with_relevance_scores(self, input_text: str, embedding: List, k: int, score_threshold: float) -> SearchedDoc:
        raise NotImplementedError

    def max_marginal_relevance_search(self, input_text: str, embedding: List, k: int, fetch_k: float, lambda_mult: float) -> SearchedDoc:
        raise NotImplementedError
