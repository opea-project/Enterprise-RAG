# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Iterable, List
from abc import ABC
from comps.cores.mega.logger import get_opea_logger
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc, TextDoc

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

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

    def _check_embedding_index(self, input: EmbedDoc):
        """
        Checks if the index exists in the vector store.
        Args:
            input (EmbedDoc): The input document containing the embedding.
        """
        try:
            if self.client is not None:
                self.client._create_index_if_not_exist(dim=len(input.embedding))
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

    def _parse_search_results(self, input: EmbedDoc, results: Iterable[any]) -> SearchedDoc:
        """
        Parses the search results and returns a `SearchedDoc` object.
        Args:
            input (EmbedDoc): The input document used for the search.
            results (Iterable[any]): The search results.
        Returns:
            SearchedDoc: The parsed search results as a `SearchedDoc` object.
        """
        searched_docs = []
        for r in results:
            searched_docs.append(TextDoc(text=r.page_content))
        return SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)

    def similarity_search_by_vector(self, input: EmbedDoc) -> SearchedDoc:
        """
        Perform a similarity search by vector.
        Args:
            input (EmbedDoc): The input document containing the vector to search for.
        Returns:
            SearchedDoc: The searched document containing the search results.
        """

        self._check_embedding_index(input=input)
        try:
            search_res = self.client.similarity_search_by_vector(
                k=input.k,
                embedding=input.embedding,
                distance_threshold=input.distance_threshold
            )
            return self._parse_search_results(input=input, results=search_res)
        except Exception as e:
            logger.exception("Error occured while searching by vector")
            raise e

    def similarity_search_with_relevance_scores(self, input: EmbedDoc) -> SearchedDoc:
        """
        Perform a similarity search with relevance scores.
        Args:
            input (EmbedDoc): The input document containing the vector to search for.
        Returns:
            SearchedDoc: The searched document containing the search results.
        """

        self._check_embedding_index(input=input)
        try:
            search_res = self.client.similarity_search_with_relevance_scores(
                k=input.k,
                embedding=input.embedding,
                score_threshold=input.score_threshold
            )
            return self._parse_search_results(input=input, results=search_res)
        except Exception as e:
            logger.exception("Error occured while searching with relevance scores")
            raise e

    def max_marginal_relevance_search(self, input: EmbedDoc) -> SearchedDoc:
        """
        Perform a max marginal relevance search.
        Args:
            input (EmbedDoc): The input document containing the vector to search for.
        Returns:
            SearchedDoc: The searched document containing the search results.
        """

        self._check_embedding_index(input=input)
        try:
            search_res = self.client.max_marginal_relevance_search(
                k=input.k,
                embedding=input.embedding,
                fetch_k=input.fetch_k,
                lambda_mult=input.lambda_mult
            )
            return self._parse_search_results(input=input, results=search_res)
        except Exception as e:
            logger.exception("Error occured while searching with max marginal relevance")
            raise e
