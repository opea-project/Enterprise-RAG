# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import redis
from typing import List, Optional
from comps.vectorstores.impl.redis.opea_redis import OPEARedis
from comps.cores.proto.docarray import SearchedDoc
from comps.cores.utils.utils import sanitize_env
from comps.vectorstores.utils.connectors.connector import VectorStoreConnector
from comps.cores.utils.utils import get_boolean_env_var
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")

class RedisVectorStore(VectorStoreConnector):
    """
    A connector class for Redis vector store.
    Args:
        batch_size (int): The batch size for vector operations. Defaults to 32.
    Attributes:
        batch_size (int): The batch size for vector operations.
        client (OPEARedis): The Redis client for vector operations.
    Methods:
        format_url_from_env(): Formats the Redis URL based on environment variables.
    """
    def __init__(self, batch_size: int = 32):
        """
        Initializes a RedisVectorStore object.
        Args:
            batch_size (int): The batch size for vector operations. Defaults to 32.
        """

        # https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/#create-a-vector-index
        # name field ommited, created by default. passing only setting fields
        vector_schema = {
            "algorithm": str(os.getenv("VECTOR_ALGORITHM", "FLAT")), # "FLAT", "HNSW"
            "dims": 1536, # Not used, overriden when creating the index
            "datatype": str(os.getenv("VECTOR_DATATYPE", "FLOAT32")), # FLOAT16, FLOAT32, FLOAT64
            "distance_metric": str(os.getenv("VECTOR_DISTANCE_METRIC", "COSINE")) # L2, IP, COSINE
        }
        if vector_schema["algorithm"] == "HNSW":
            vector_schema.update(
                {
                    "m": int(os.getenv("VECTOR_HNSW_M", 16)),
                    "ef_construction": int(os.getenv("VECTOR_HNSW_EF_CONSTRUCTION", 200)),
                    "ef_runtime": int(os.getenv("VECTOR_HNSW_EF_RUNTIME", 10)),
                    "epsilon": float(os.getenv("VECTOR_HNSW_EPSILON", 0.01))
                }
            )

        url = RedisVectorStore.format_url_from_env()
        self.index_name = f"{vector_schema['algorithm'].lower()}_{vector_schema['datatype'].lower()}_{vector_schema['distance_metric'].lower()}_index"
        self.client = self._client(url=url, index_name=self.index_name, vector_schema=vector_schema, key_prefix="doc:default_index")
        self.batch_size = batch_size

    def _client(self, url: str, index_name: str, vector_schema: Optional[dict] = None, key_prefix: Optional[str] = None) -> OPEARedis:
        return OPEARedis(url=url, index_name=index_name, vector_schema=vector_schema, key_prefix=key_prefix)

    @staticmethod
    def format_url_from_env():
        """
        Formats the Redis URL based on environment variables.
        Returns:
            str: The formatted Redis URL.
        """
        redis_url = sanitize_env(os.getenv("REDIS_URL", None))
        if redis_url:
            return redis_url
        else:
            host = os.getenv("REDIS_HOST", 'localhost')
            port = int(os.getenv("REDIS_PORT", 6379))

            using_ssl = get_boolean_env_var("REDIS_SSL", False)
            schema = "rediss" if using_ssl else "redis"

            username = os.getenv("REDIS_USERNAME", "default")
            password = os.getenv("REDIS_PASSWORD", None)
            credentials = "" if password is None else f"{username}:{password}@"

            return f"{schema}://{credentials}{host}:{port}/"

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

        try:
            search_res = self.client.similarity_search_by_vector(
                k=k,
                embedding=embedding,
                distance_threshold=distance_threshold
            )
            return self._parse_search_results(input_text=input_text, results=search_res)
        except redis.exceptions.ResponseError as e:
            if "no such index" in str(e):
                logger.warning("No such index found in vector store. Import data first.")
                return SearchedDoc(retrieved_docs=[], initial_query=input_text)
            raise e
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

        try:
            docs_and_similarities = self.client.similarity_search_with_relevance_scores(
                k=k,
                query=input_text,
                score_threshold=score_threshold
            )
            search_res = [doc for doc, _ in docs_and_similarities]
            return self._parse_search_results(input_text=input_text, results=search_res)
        except redis.exceptions.ResponseError as e:
            if "no such index" in str(e):
                logger.warning("No such index found in vector store. Import data first.")
                return SearchedDoc(retrieved_docs=[], initial_query=input_text)
            raise e
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

        try:
            search_res = self.client.max_marginal_relevance_search(
                k=k,
                embedding=embedding,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult
            )
            return self._parse_search_results(input_text=input_text, results=search_res)
        except redis.exceptions.ResponseError as e:
            if "no such index" in str(e):
                logger.warning("No such index found in vector store. Import data first.")
                return SearchedDoc(retrieved_docs=[], initial_query=input_text)
            raise e
        except Exception as e:
            logger.exception("Error occured while searching with max marginal relevance")
            raise e
