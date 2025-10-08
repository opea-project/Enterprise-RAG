# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from redis import exceptions
from typing import Iterable, List, Optional, Union
from comps.cores.proto.docarray import SearchedDoc, TextDoc
from comps.cores.utils.utils import sanitize_env
from comps.cores.utils.utils import get_boolean_env_var
from comps.cores.mega.logger import get_opea_logger, change_opea_logger_level
from comps.vectorstores.utils.connectors.connector import VectorStoreConnector
from redisvl.redis.connection import RedisConnectionFactory
from redisvl.schema import IndexSchema
from redisvl.index import AsyncSearchIndex
from redisvl.query import VectorQuery, VectorRangeQuery, FilterQuery
from redisvl.redis.utils import array_to_buffer
from redisvl.query.filter import FilterExpression, Text, Num
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

class ConnectorRedis(VectorStoreConnector):
    CONTENT_FIELD_NAME = "text"
    EMBEDDING_FIELD_NAME = "embedding"

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.index_dict = {}

    def _dims(self):
        return self._vector_schema_from_env()['dims']

    def _dtype(self):
        return self._vector_schema_from_env()['datatype']

    def _vector_schema_from_env(self):
        vector_schema = {
            "algorithm": str(sanitize_env(os.getenv("VECTOR_ALGORITHM", "FLAT"))), # "FLAT", "HNSW"
            "dims": int(sanitize_env(str(os.getenv("VECTOR_DIMS", 768)))),
            "datatype": str(sanitize_env(os.getenv("VECTOR_DATATYPE", "FLOAT32"))), # BFLOAT16, FLOAT16, FLOAT32, FLOAT64
            "distance_metric": str(sanitize_env(os.getenv("VECTOR_DISTANCE_METRIC", "COSINE"))) # L2, IP, COSINE
        }
        if vector_schema["algorithm"] == "HNSW":
            vector_schema.update(
                {
                    "m": int(sanitize_env(str(os.getenv("VECTOR_HNSW_M", 16)))),
                    "ef_construction": int(sanitize_env(str(os.getenv("VECTOR_HNSW_EF_CONSTRUCTION", 200)))),
                    "ef_runtime": int(sanitize_env(str(os.getenv("VECTOR_HNSW_EF_RUNTIME", 10)))),
                    "epsilon": float(sanitize_env(str(os.getenv("VECTOR_HNSW_EPSILON", 0.01))))
                }
            )
        return vector_schema

    def _metadata_schema(self):
        base_fields = [
            "id", "bucket_name", "object_name", "file_id", "link_id", "url", "timestamp",
            "Header1", "Header2", "Header3", "Header4", "Header5", "Header6"
        ]

        metadata_schema = [{"name": field, "type": "text"} for field in base_fields]
        metadata_schema.append({"name": "start_index", "type": "numeric"})

        # Find and update the bucket_name field to include index_missing attribute
        for field in metadata_schema:
            if field["name"] == "file_id":
                field["attrs"] = {"index_missing": True}
            if field["name"] == "link_id":
                field["attrs"] = {"index_missing": True}  

        if sanitize_env(os.getenv("USE_HIERARCHICAL_INDICES")).lower() == "true":
            hierarchical_fields = [
                {"name": "doc_id", "type": "text"},
                {"name": "page", "type": "numeric"},
                {"name": "summary", "type": "numeric"},
            ]
            metadata_schema.extend(hierarchical_fields)

        return metadata_schema

    def _vector_schema(self, schema: dict, metadata_schema: Optional[dict]=None) -> IndexSchema:
        index_name = f"{schema['algorithm'].lower()}_{schema['datatype'].lower()}_{schema['distance_metric'].lower()}_index"

        data = {
            "index": {
                "name": index_name,
                "prefix": "erag",
                "storage_type": "hash"
            },
            "fields": [
                {
                    "name": ConnectorRedis.CONTENT_FIELD_NAME,
                    "type": "text"
                },
                {
                    "name": ConnectorRedis.EMBEDDING_FIELD_NAME,
                    "type": "vector",
                    "attrs": {
                        "datatype": schema['datatype'],
                        "algorithm": schema['algorithm'],
                        "dims": schema['dims'],
                        "distance_metric": schema['distance_metric'],
                    },
                }
            ]
        }

        if metadata_schema:
            data["fields"].extend(metadata_schema)

        if schema['algorithm'].lower() == "hnsw":
            data['fields'][1]['attrs'].update(
                {
                    "m": schema['m'],
                    "ef_construction": schema['ef_construction'],
                    "ef_runtime": schema['ef_runtime'],
                    "epsilon": schema['epsilon']
                }
            )

        return IndexSchema.from_dict(data)

    async def _create_index(self, schema: IndexSchema, overwrite: bool=False) -> AsyncSearchIndex:
        logger.info(f"Creating index: {schema.index.name}")
        index = AsyncSearchIndex(schema=schema, redis_url=ConnectorRedis.format_url_from_env())
        await index.create(overwrite=overwrite)
        return index

    async def vector_index(self) -> AsyncSearchIndex:
        schema = self._vector_schema(self._vector_schema_from_env(), self._metadata_schema())
        index_name = schema.index.name

        if self.index_dict.get(index_name, None) is not None:
            index = self.index_dict[index_name]
            exists = await index.exists()
            if exists:
                return index
            else:
                logger.info(f"Index {index_name} memoized but not available in redis.")

        index = await self._create_index(schema)
        self.index_dict[index_name]=index
        return index

    def _process_data(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]=None):
        datas = [
            {
                "text": text,
                "embedding": array_to_buffer(embedding, dtype=self._dtype()),
                **(metadata if metadata is not None else {})
            }
            for text, embedding, metadata in zip(
                texts, embeddings, metadatas or [None] * len(texts)
            )
        ]
        return datas

    async def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]=None):
        try:
            data = self._process_data(texts, embeddings, metadatas)
            index = await self.vector_index()
            result = await index.load(data)
            return list(result) if result is not None else []
        except Exception as e:
            logger.exception("Error occured while adding texts")
            raise e

    def _search_schema(self, field_name: str) -> IndexSchema:
        data = {
            "index": {
                "name": f"search_{field_name}",
                "prefix": "erag",
                "storage_type": "hash"
            },
            "fields": [
                {
                    "name": field_name,
                    "type": "text"
                }
            ]
        }
        return IndexSchema.from_dict(data)

    async def search_index(self, field_name: str) -> AsyncSearchIndex:
        schema = self._search_schema(field_name)
        index_name = schema.index.name

        if self.index_dict.get(index_name, None) is not None:
            index = self.index_dict[index_name]
            exists = await index.exists()
            if exists:
                logger.info(f"Using index {index_name} exists.")
                return index
            else:
                logger.info(f"Index {index_name} memoized but not available in redis.")

        index = await self._create_index(schema)
        self.index_dict[index_name]=index
        return index

    async def search_by_metadata(self, field_name: str, field_value: str):
        filter = Text(field_name) == field_value
        query = FilterQuery(num_results=10000, filter_expression=filter)
        index = await self.search_index(field_name)
        return await index.search(query)

    async def search_and_delete_by_metadata(self, field_name: str, field_value: str):
        client = RedisConnectionFactory.connect(
            redis_url=ConnectorRedis.format_url_from_env(),
            use_async=True
        )
        try:
            logger.debug(f"Searching and deleting documents with {field_name}={field_value}")
            while True:
                results = await self.search_by_metadata(field_name, field_value)
                if not results.docs or len(results.docs) == 0:
                    logger.debug("No more documents found to delete.")
                    break
                logger.debug(f"Deleting {len(results.docs)} documents")
                for r in results.docs:
                    await client.delete(r.id)
        finally:
            if client is not None:
                await client.close()

    def _build_vector_query(
        self,
        vector: List[float],
        k: int,
        distance_threshold: float=None,
        dtype: str="float32",
        filter_expression: Optional[Union[str, FilterExpression]] = None,
        return_fields: Optional[List[str]]=None
    ):
        logger.info(f"Building vector query with k={k}, distance_threshold={distance_threshold}, dtype={dtype}, filter_expression={filter_expression}, return_fields={return_fields}")

        if distance_threshold is not None:
            return VectorRangeQuery(
                vector=vector,
                vector_field_name="embedding",
                num_results=k,
                filter_expression=filter_expression,
                distance_threshold=distance_threshold,
                dtype=dtype,
                return_fields=return_fields
            )
        else:
            return VectorQuery(
                vector=vector,
                vector_field_name="embedding",
                num_results=k,
                filter_expression=filter_expression,
                dtype=dtype,
                return_fields=return_fields
            )

    def _parse_search_results(self, input_text: str, results: Iterable[any]) -> SearchedDoc:
        searched_docs = []
        for r in results:
            searched_docs.append(self._convert_to_text_doc(r))

        return SearchedDoc(retrieved_docs=searched_docs, user_prompt=input_text)

    async def similarity_search_by_vector(self, input_text: str, embedding: List[float], k: int, distance_threshold: float = None, filter_expression: Optional[Union[str, FilterExpression]] = None, parse_result: bool = True) -> SearchedDoc:
        try:
            fields = [ConnectorRedis.CONTENT_FIELD_NAME, VectorQuery.DISTANCE_ID]
            if self._metadata_schema():
                fields.extend([field['name'] for field in self._metadata_schema()])

            v = self._build_vector_query(
                vector=embedding,
                k=k,
                dtype=self._dtype(),
                return_fields=fields,
                distance_threshold=distance_threshold,
                filter_expression=filter_expression
            )
            index = await self.vector_index()
            result = await index.search(v.query, query_params=v.params)

            if parse_result:
                return self._parse_search_results(input_text=input_text, results=result.docs)
            else:
                return result
        except exceptions.ResponseError as e:
            if "no such index" in str(e):
                logger.warning("No such index found in vector store. Import data first.")
                return SearchedDoc(retrieved_docs=[], user_prompt=input_text)
            raise e
        except Exception as e:
            logger.exception("Error occured while searching by vector")
            raise e

    def get_files_filter_expression(self) -> FilterExpression:
        """
        Use is_missing operator for link_id to filter out links and return only files.
        Returns:
            FilterExpression: Returns a filter expression matching only files.
        """
        logger.debug("Adding files filter expression")
        return Text("link_id").is_missing()

    def get_links_filter_expression(self) -> FilterExpression:
        """
        Use is_missing operator for file_id to filter out files and return only links.
        Returns:
            FilterExpression: Returns a filter expression to query only links.
        """
        logger.debug("Adding links filter expression")
        return Text("file_id").is_missing()

    def get_bucket_name_filter_expression(self, bucket_names: List[str]) -> FilterExpression:
        """
        Constructs a filter expression for bucket names.
        Args:
            bucket_names (List[str]): List of bucket names to filter by.
        Returns:
            FilterExpression: The filter expression for the bucket names.
        """
        logger.debug(f"Bucket names in filter expression: {bucket_names}")
        if len(bucket_names) == 0:
            raise ValueError("Bucket names list cannot be empty")
        bucket_name_filter = Text("bucket_name") == bucket_names[0]
        for bucket_name in bucket_names[1:]:
            bucket_name_filter |= Text("bucket_name") == bucket_name

        logger.debug(f"Filter expression for bucket names: {str(bucket_name_filter)}")
        return bucket_name_filter

    def get_object_name_filter_expression(self, bucket_name: str, object_name: str) -> FilterExpression:
        """
        Constructs a filter expression for bucket name and object name.
        Args:
            bucket_name (str): The name of the bucket.
            object_name (str): The name of the object.
        Returns:
            FilterExpression: The filter expression for the bucket names.
        Raises:
            ValueError: If bucket_name and/or object_name is empty.
        """
        if len(bucket_name) == 0 or len(object_name) == 0:
            raise ValueError("Bucket name and object name cannot be empty")
        bucket_name_filter = Text("bucket_name") == bucket_name
        object_name_filter = Text("object_name") == object_name

        bucket_object_filter = bucket_name_filter & object_name_filter
        logger.debug(f"Filter expression for bucket name and object name: {str(bucket_object_filter)}")
        return bucket_object_filter

    def get_hierarchical_summary_filter_expression(self):
        """
        Constructs a filter expression for hierarchical indices to retrieve summaries.
        Returns:
            FilterExpression: The filter expression for the hierarchical index.
        """
        return Num("summary") == 1

    def get_hierarchical_chunk_filter_expression(self, doc_id, page):
        """
        Constructs a filter expression for hierarchical indices based on doc_id and page.
        Args:
            doc_id (str): The document ID.
            page (int): The page number.
        Returns:
            FilterExpression: The filter expression for the hierarchical index.
        """
        doc = Text("doc_id") == doc_id
        page = Num("page") == page
        summary = Num("summary") == 0
        return doc & page & summary

    def _convert_to_text_doc(self, doc):
        """Helper method to convert a raw Redis result to a TextDoc"""
        metadata = {}
        for field in [VectorQuery.DISTANCE_ID] + [field['name'] for field in self._metadata_schema()]:
            try:
                metadata[field] = doc[field]
            except (AttributeError, KeyError):
                continue

        return TextDoc(
            text=doc[ConnectorRedis.CONTENT_FIELD_NAME],
            metadata=metadata
        )

    async def similarity_search_with_siblings(self, input_text: str, embedding: List[float],
                                              k: int,
                                              distance_threshold: float = None,
                                              filter_expression: Optional[Union[str, FilterExpression]] = None) -> SearchedDoc:
        """
        Performs a similarity search and retrieves sibling chunks based on document structure.

        For chunks with headers: Retrieves 1 chunk before and 1 after with matching headers
        For chunks without headers: Retrieves 1 chunk before and 1 after based on start_index

        Args:
            input_text: The user query text
            embedding: The vector embedding for similarity search
            k: Number of similar chunks to retrieve initially
            distance_threshold: Optional threshold for similarity
            filter_expression: Optional filters for the initial search

        Returns:
            SearchedDoc containing both the similar chunks and their siblings
        """
        # First get the k most similar chunks
        initial_result = await self.similarity_search_by_vector(
            input_text=input_text,
            embedding=embedding,
            k=k,
            distance_threshold=distance_threshold,
            filter_expression=filter_expression,
            parse_result=False  # Get raw results to work with
        )

        # Get vector index to use for sibling queries
        index = await self.vector_index()

        # If no results or error, return empty result
        if not hasattr(initial_result, 'docs') or not initial_result.docs:
            return SearchedDoc(retrieved_docs=[], user_prompt=input_text)

        # Process the main retrieved documents
        primary_docs = []

        for doc in initial_result.docs:
            metadata = {}
            for field in [VectorQuery.DISTANCE_ID] + [field['name'] for field in self._metadata_schema()]:
                try:
                    metadata[field] = doc[field]
                except (AttributeError, KeyError):
                    continue

            primary_docs.append(
                TextDoc(
                    text=doc[ConnectorRedis.CONTENT_FIELD_NAME],
                    metadata=metadata
                )
            )

        logger.debug(f"Found {len(primary_docs)} primary documents for input: {input_text}")
        all_sibling_docs = {}

        # We only find siblings for files therefore use file_id for file uniqueness.
        # Using object_name would not work since it might not be unique across different buckets.
        for doc in initial_result.docs:
            sibling_docs = []
            if not hasattr(doc, 'file_id') or not hasattr(doc, 'start_index'):
                continue

            object_id = doc.file_id
            start_index = doc.start_index

            has_headers = False
            header_filter = filter_expression & (Text('file_id') == object_id)

            for i in range(1, 7):
                header_key = f'Header{i}'
                header_value = getattr(doc, header_key, None)
                if header_value:
                    has_headers = True
                    header_value = header_value.replace(":", "")
                    header_filter = header_filter & (Text(header_key) % str(header_value))

            if has_headers:
                # Case 1: Document has headers - get siblings with matching headers
                header_query = FilterQuery(filter_expression=header_filter, num_results=100)
                header_result = await index.search(header_query)
                logger.debug(f"Retrieved header chunks: {len(header_result.docs)} for header_filter: {header_filter}")

                if header_result.docs:
                    sorted_chunks = sorted(header_result.docs, key=lambda x: int(x.start_index) if hasattr(x, 'start_index') else 0)
                    current_pos = -1
                    for i, chunk in enumerate(sorted_chunks):
                        if chunk.id == doc.id:
                            current_pos = i
                            break

                    if current_pos != -1:
                        if current_pos > 0:
                            prev_chunk = sorted_chunks[current_pos - 1]
                            sibling_docs.append(self._convert_to_text_doc(prev_chunk))

                        if current_pos < len(sorted_chunks) - 1:
                            next_chunk = sorted_chunks[current_pos + 1]
                            sibling_docs.append(self._convert_to_text_doc(next_chunk))
            else:
                # Case 2: Document doesn't have headers - get nearest chunks by start_index
                before_filter = filter_expression & (Text('file_id') == object_id) & (Num('start_index') < int(start_index))
                before_query = FilterQuery(filter_expression=before_filter, num_results=100)
                before_result = await index.search(before_query)

                if before_result.docs:
                    prev_chunk = max(before_result.docs, key=lambda x: int(x.start_index) if hasattr(x, 'start_index') else 0)
                    logger.debug(f"Retrieved previous chunk: {prev_chunk.id, prev_chunk.start_index}")
                    sibling_docs.append(self._convert_to_text_doc(prev_chunk))

                after_filter = filter_expression & (Text('file_id') == object_id) & (Num('start_index') > int(start_index))
                after_query = FilterQuery(filter_expression=after_filter, num_results=100)
                after_result = await index.search(after_query)

                if after_result.docs:
                    next_chunk = min(after_result.docs, key=lambda x: int(x.start_index) if hasattr(x, 'start_index') else 0)
                    logger.debug(f"Retrieved next chunk: {next_chunk.id, next_chunk.start_index}")
                    sibling_docs.append(self._convert_to_text_doc(next_chunk))

            all_sibling_docs[doc.id] = sibling_docs

        logger.debug(f"Final sibling docs: {all_sibling_docs}")
        return SearchedDoc(retrieved_docs=primary_docs, sibling_docs=all_sibling_docs, user_prompt=input_text)

    @staticmethod
    def format_url_from_env():
        """
        Formats the Redis URL based on environment variables.
        Returns:
            str: The formatted Redis URL.
        """
        redis_url = sanitize_env(os.getenv("REDIS_URL", None))
        vector_store = sanitize_env(os.getenv("VECTOR_STORE", "")).lower()
        should_be_cluster = True if vector_store == "redis-cluster" else False

        if redis_url:
            parsed_url = urlparse(redis_url)
            query_params = parse_qs(parsed_url.query)
            # Get query parameter keys, make them lowercase, and ensure uniqueness
            query_keys = {key.lower() for key in query_params.keys()}

            # Check if "cluster" parameter exists and if required, append it
            if "cluster" not in query_keys and should_be_cluster:
                query_params["cluster"] = ["true"]

            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                "/" if parsed_url.path == "" else parsed_url.path,
                parsed_url.params,
                urlencode(query_params, doseq=True),
                parsed_url.fragment
            ))
            return new_url
        else:
            host = sanitize_env(os.getenv("REDIS_HOST", 'localhost'))
            port = int(sanitize_env(os.getenv("REDIS_PORT", 6379)))
            using_ssl = get_boolean_env_var("REDIS_SSL", False)
            schema = "rediss" if using_ssl else "redis"
            username = sanitize_env(os.getenv("REDIS_USERNAME", "default"))
            password = sanitize_env(os.getenv("REDIS_PASSWORD", None))

            query_params = {}
            if should_be_cluster:
                query_params["cluster"] = ["true"]

            netloc = f"{username}:{password}@{host}:{port}" if password else f"{host}:{port}"
            new_url = urlunparse((
                schema,
                netloc,
                "/", # path
                "", # params
                urlencode(query_params, doseq=True), # query
                "" # fragment
            ))
            return new_url
