# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Iterable, List
from abc import ABC
from comps.cores.mega.logger import get_opea_logger
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc, TextDoc

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")

class VectorStoreWrapper(ABC):
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
        Creates a new instance of the VectorStoreWrapper class.
        Returns:
            The instance of the VectorStoreWrapper class.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(VectorStoreWrapper, cls).__new__(cls)
        return cls.instance

    def __init__(self, batch_size: int, index_name: str = "default_index"):
        """
        Initializes the Wrapper object.
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

    def search_and_delete_documents(self, index_name, field_name, field_value, prefix_name):
        """
        Search and delete documents from the vector store based on filed name and value.
        """
        try:
            return self.client.search_and_delete_documents(index_name, field_name, field_value, prefix_name)
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
        """
        Perform a similarity search by vector.
        Args:
            input_text (str): The input text to search for.
            embedding (List): The embedding to search for.
            k (int): The number of results to retrieve.
            distance_threshold (float): The distance threshold for the search.
        Returns:
            SearchedDoc: The searched document containing the search results.
        """

        self._check_embedding_index(embedding)
        try:
            search_res = self.client.similarity_search_by_vector(
                k=k,
                embedding=embedding,
                distance_threshold=distance_threshold
            )
            return self._parse_search_results(input_text=input_text, results=search_res)
        except Exception as e:
            logger.exception("Error occured while searching by vector")
            raise e

    def similarity_search_with_relevance_scores(self, input_text: str, embedding: List, k: int, score_threshold: float) -> SearchedDoc:
        """
        Perform a similarity search with relevance scores.
        Args:
            embedding (List): The embedding to search for.
            k (int): The number of results to retrieve.
            score_threshold (float): The distance threshold for the search.
        Returns:
            SearchedDoc: The searched document containing the search results.
        """
        if score_threshold < 0 or score_threshold > 1:
            raise ValueError(f"score_threshold must be between 0 and 1. Received: {score_threshold}")

        self._check_embedding_index(embedding)
        try:
            # FIXME: redis.exceptions.ResponseError: Error parsing vector similarity query: query vector blob size (4096) does not match index's expected size (16)
            docs_and_similarities = self.client.similarity_search_with_relevance_scores(
                k=k,
                query=input_text,
                score_threshold=score_threshold
            )
            search_res = [doc for doc, _ in docs_and_similarities]
            return self._parse_search_results(input_text=input_text, results=search_res)
        except Exception as e:
            logger.exception("Error occured while searching with relevance scores")
            raise e

    def max_marginal_relevance_search(self, input_text: str, embedding: List, k: int, fetch_k: float, lambda_mult: float) -> SearchedDoc:
        """
        Perform a max marginal relevance search.
        Args:
            embedding (List): The embedding to search for.
            k (int): The number of results to retrieve.
            distance_threshold (float): The distance threshold for the search.
        Returns:
            SearchedDoc: The searched document containing the search results.
        """
        if lambda_mult < 0 or lambda_mult > 1:
            raise ValueError(f"lambda_mult must be between 0 and 1. Received: {lambda_mult}")

        self._check_embedding_index(embedding)
        try:
            search_res = self.client.max_marginal_relevance_search(
                k=k,
                embedding=embedding,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult
            )
            return self._parse_search_results(input_text=input_text, results=search_res)
        except Exception as e:
            logger.exception("Error occured while searching with max marginal relevance")
            raise e
