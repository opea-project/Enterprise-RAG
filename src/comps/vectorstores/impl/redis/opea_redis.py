# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any, Callable, Dict, cast, List, Optional, Union
import numpy as np
from langchain_community.vectorstores import Redis
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.redis.filters import RedisFilterExpression
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from langchain_community.utilities.redis import _buffer_to_array

class OPEARedis(Redis):
    """
    OPEARedis class expands Langchain's implementation of a Redis by adding new functionality.
    Methods like add_texts() and def similarity_search_by_vector() that are implemented in the base class are not shown here.
    Args:
        url (str): The URL of the Redis server.
        index_name (str): The name of the index.
        embedding (Embeddings, optional): The embedding object used for vectorization. Defaults to None.
        index_schema (Optional[Union[Dict[str, List[Dict]], str, os.PathLike]], optional): The schema for the index. Defaults to None.
        vector_schema (Optional[Dict[str, Union[str, int]]], optional): The schema for the vectors. Defaults to None.
        relevance_score_fn (Optional[Callable[[float], float]], optional): The function used to calculate relevance scores. Defaults to None.
        key_prefix (Optional[str], optional): The prefix for the Redis keys. Defaults to None.
        **kwargs (Any): Additional keyword arguments.
    Methods:
        similarity_search_with_relevance_scores(embedding: List[float], k: int, score_threshold: float) -> List[Document]:
            Performs a similarity search with relevance scores using the given embedding.
        max_marginal_relevance_search(embedding: List[float], k: int = 4, fetch_k: int = 20, lambda_mult: float = 0.5,
                                      filter: Optional[RedisFilterExpression] = None, return_metadata: bool = True,
                                      distance_threshold: Optional[float] = None, **kwargs: Any) -> List[Document]:
            Performs a max marginal relevance search using the given embedding.
    """
    def __init__(
        self,
        url: str,
        index_name: str,
        embedding: Embeddings = None,
        index_schema: Optional[Union[Dict[str, List[Dict]], str, os.PathLike]] = None,
        vector_schema: Optional[Dict[str, Union[str, int]]] = None,
        relevance_score_fn: Optional[Callable[[float], float]] = None,
        key_prefix: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes a new instance of the OPEARedis class.
        Args:
            url (str): The URL of the Redis server.
            index_name (str): The name of the index.
            embedding (Embeddings, optional): The embedding object used for vectorization. Defaults to None.
            index_schema (Optional[Union[Dict[str, List[Dict]], str, os.PathLike]], optional): The schema for the index. Defaults to None.
            vector_schema (Optional[Dict[str, Union[str, int]]], optional): The schema for the vectors. Defaults to None.
            relevance_score_fn (Optional[Callable[[float], float]], optional): The function used to calculate relevance scores. Defaults to None.
            key_prefix (Optional[str], optional): The prefix for the Redis keys. Defaults to None.
            **kwargs (Any): Additional keyword arguments.
        """
        self.embedding = embedding
        # langchain_community.vectorstores.Redis already validates the connection
        super().__init__(
            redis_url=url,
            index_name=index_name,
            embedding=embedding,
            index_schema=index_schema,
            vector_schema=vector_schema,
            relevance_score_fn=relevance_score_fn,
            key_prefix=key_prefix,
            **kwargs,
        )

    def similarity_search_with_relevance_scores(
        self,
        embedding: List[float],
        k: int,
        score_threshold: float
    ) -> List[Document]:
        """
        Performs a similarity search with relevance scores using the given embedding.
        Args:
            embedding (List[float]): The embedding to search for.
            k (int): The number of results to return.
            score_threshold (float): The threshold for relevance scores.
        Returns:
            List[Document]: The list of documents matching the search criteria.
        """
        raise NotImplementedError # via lanchain_core > vectorstores > base.py > similaryty_search_with_score

    # Default mmr search overriden to take embedding instead of query!
    def max_marginal_relevance_search(
        self,
        embedding: List[float],
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: Optional[RedisFilterExpression] = None,
        return_metadata: bool = True,
        distance_threshold: Optional[float] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Performs a max marginal relevance search using the given embedding.
        Args:
            embedding (List[float]): The embedding to search for.
            k (int, optional): The number of results to return. Defaults to 4.
            fetch_k (int, optional): The number of documents to fetch initially. Defaults to 20.
            lambda_mult (float, optional): The lambda multiplier for MMR. Defaults to 0.5.
            filter (Optional[RedisFilterExpression], optional): The filter expression for Redis. Defaults to None.
            return_metadata (bool, optional): Whether to return metadata. Defaults to True.
            distance_threshold (Optional[float], optional): The distance threshold for similarity search. Defaults to None.
            **kwargs (Any): Additional keyword arguments.
        Returns:
            List[Document]: The list of documents matching the search criteria.
        """

        # Embed the query
        query_embedding = embedding

        # Fetch the initial documents
        prefetch_docs = self.similarity_search_by_vector(
            query_embedding,
            k=fetch_k,
            filter=filter,
            return_metadata=return_metadata,
            distance_threshold=distance_threshold,
            **kwargs,
        )
        prefetch_ids = [doc.metadata["id"] for doc in prefetch_docs]

        # Get the embeddings for the fetched documents
        prefetch_embeddings = [
            _buffer_to_array(
                cast(
                    bytes,
                    self.client.hget(prefetch_id, self._schema.content_vector_key),
                ),
                dtype=self._schema.vector_dtype,
            )
            for prefetch_id in prefetch_ids
        ]

        # Select documents using maximal marginal relevance
        selected_indices = maximal_marginal_relevance(
            np.array(query_embedding), prefetch_embeddings, lambda_mult=lambda_mult, k=k
        )
        selected_docs = [prefetch_docs[i] for i in selected_indices]

        return selected_docs
