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
from redisvl.query.filter import FilterExpression, Text

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
        metadata_schema = [
            {
                "name": "bucket_name",
                "type": "text",
            },
            {
                "name": "object_name",
                "type": "text",
            },
            {
                "name": "file_id",
                "type": "text",
            },
            {
                "name": "link_id",
                "type": "text",
            },
            {
                "name": "url",
                "type": "text",
            },
            {
                "name": "timestamp",
                "type": "text",
            }
        ]
        if (sanitize_env(os.getenv("USE_HIERARCHICAL_INDICES")).lower() == "true"):
            metadata_schema.extend([
                {
                    "name": "doc_id",
                    "type": "text",
                },
                {
                    "name": "page",
                    "type": "numeric",
                },
                {
                    "name": "summary",
                    "type": "numeric",
                }
            ])
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
        index = AsyncSearchIndex(schema)
        await index.connect(redis_url=ConnectorRedis.format_url_from_env())
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
        results = await self.search_by_metadata(field_name, field_value)
        client = RedisConnectionFactory.connect(
            redis_url=ConnectorRedis.format_url_from_env(),
            use_async=True
        )
        for r in results.docs:
            await client.delete(r.id)

    def _build_vector_query(
        self,
        vector: List[float],
        k: int,
        distance_threshold: float=None,
        dtype: str="float32",
        filter_expression: Optional[Union[str, FilterExpression]] = None,
        return_fields: Optional[List[str]]=None
    ):
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

        metadata_fields = [VectorQuery.DISTANCE_ID]
        if self._metadata_schema():
            metadata_fields.extend([field['name'] for field in self._metadata_schema()])

        for r in results:
            metadata = {}
            for field in metadata_fields:
                try:
                    metadata[field] = r[field]
                except AttributeError:
                    continue
                except KeyError:
                    continue

            searched_docs.append(
                TextDoc(
                    text=r[ConnectorRedis.CONTENT_FIELD_NAME],
                    metadata=metadata
                )
            )
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
            host = sanitize_env(os.getenv("REDIS_HOST", 'localhost'))
            port = int(sanitize_env(os.getenv("REDIS_PORT", 6379)))

            using_ssl = get_boolean_env_var("REDIS_SSL", False)
            schema = "rediss" if using_ssl else "redis"

            username = sanitize_env(os.getenv("REDIS_USERNAME", "default"))
            password = sanitize_env(os.getenv("REDIS_PASSWORD", None))
            credentials = "" if password is None else f"{username}:{password}@"

            return f"{schema}://{credentials}{host}:{port}/"
