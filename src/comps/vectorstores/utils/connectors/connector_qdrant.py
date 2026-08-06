# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import uuid
from typing import Any, Iterable, List, Optional, Union
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from comps.cores.proto.docarray import SearchedDoc, TextDoc
from comps.cores.utils.utils import sanitize_env
from comps.cores.mega.logger import get_opea_logger, change_opea_logger_level
from comps.vectorstores.utils.connectors.connector import VectorStoreConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


def _bool_env(var_name: str, default_value: bool = False) -> bool:
    """
    Boolean environment variable read that tolerates quoted values.

    The generated ConfigMaps and the documented `.env` files render values with
    quotes (QDRANT_ON_DISK_PAYLOAD="true"), and get_boolean_env_var matches the
    raw value, so a quoted value would silently fall back to default_value.
    """
    value = sanitize_env(os.getenv(var_name, None))
    if value is None:
        return default_value
    if value.lower() in ("true", "1", "t", "y", "yes"):
        return True
    if value.lower() in ("false", "0", "f", "n", "no"):
        return False
    return default_value


class QdrantFilterExpression:
    """
    Wrapper around qdrant_client.models.Filter that supports the operators the
    consumers of the vector store layer apply to filter expressions.

    `models.Filter` implements neither `&`, `|`, `str()` nor truthiness, while
    comps/retrievers/utils/opea_retriever.py and
    comps/retrievers/utils/builders/filter_expression_builder.py all rely on
    them. A `Filter` is itself a valid `Condition`, so combination is done by
    nesting the two filters in `must` (AND) or `should` (OR).
    """

    def __init__(self, qdrant_filter: models.Filter):
        self.qdrant_filter = qdrant_filter

    def __and__(self, other):
        if not isinstance(other, QdrantFilterExpression):
            return NotImplemented
        return QdrantFilterExpression(models.Filter(must=[self.qdrant_filter, other.qdrant_filter]))

    def __or__(self, other):
        if not isinstance(other, QdrantFilterExpression):
            return NotImplemented
        return QdrantFilterExpression(models.Filter(should=[self.qdrant_filter, other.qdrant_filter]))

    def __bool__(self):
        f = self.qdrant_filter
        return bool(f.must or f.should or f.must_not or f.min_should)

    def __str__(self):
        return self.qdrant_filter.model_dump_json(exclude_none=True)


class ConnectorQdrant(VectorStoreConnector):
    CONTENT_FIELD_NAME = "text"
    EMBEDDING_FIELD_NAME = "dense"
    DISTANCE_FIELD_NAME = "vector_distance"

    POINT_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "")

    SIBLING_SCAN_LIMIT = 100

    _DISTANCE_METRICS = {
        "COSINE": models.Distance.COSINE,
        "L2": models.Distance.EUCLID,
    }

    _DATATYPES = {
        "FLOAT32": models.Datatype.FLOAT32,
        "FLOAT16": models.Datatype.FLOAT16,
    }

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.collection_dict = {}
        self._client = None

    def _dims(self):
        return int(sanitize_env(str(os.getenv("VECTOR_DIMS", 768))))

    def _distance(self) -> models.Distance:
        metric = str(sanitize_env(os.getenv("VECTOR_DISTANCE_METRIC", "COSINE"))).upper()
        if metric == "IP":
            raise ValueError(
                "VECTOR_DISTANCE_METRIC 'IP' is not supported on Qdrant: the raw inner product is "
                "unbounded, so vector_distance values and distance_threshold cannot be interpreted. "
                f"Set VECTOR_DISTANCE_METRIC to one of {list(ConnectorQdrant._DISTANCE_METRICS)}."
            )
        if metric not in ConnectorQdrant._DISTANCE_METRICS:
            raise ValueError(f"Unsupported VECTOR_DISTANCE_METRIC for Qdrant: {metric}. Supported: {list(ConnectorQdrant._DISTANCE_METRICS)}")
        return ConnectorQdrant._DISTANCE_METRICS[metric]

    def _datatype(self) -> models.Datatype:
        datatype = str(sanitize_env(os.getenv("VECTOR_DATATYPE", "FLOAT32"))).upper()
        if datatype not in ConnectorQdrant._DATATYPES:
            raise ValueError(f"Unsupported VECTOR_DATATYPE for Qdrant: {datatype}. Supported: {list(ConnectorQdrant._DATATYPES)}")
        return ConnectorQdrant._DATATYPES[datatype]

    def _vector_schema_from_env(self):
        vector_schema = {
            "algorithm": str(sanitize_env(os.getenv("VECTOR_ALGORITHM", "FLAT"))).upper(), # "FLAT", "HNSW"
            "dims": self._dims(),
            "datatype": self._datatype(),
            "distance_metric": self._distance(),
            # On-disk storage is the default profile: vectors are always mmap'd by
            # Qdrant, `on_disk` only controls page cache prefault.
            "on_disk": _bool_env("QDRANT_ON_DISK_VECTORS", True),
            "on_disk_payload": _bool_env("QDRANT_ON_DISK_PAYLOAD", True),
            # The HNSW graph is deliberately kept in RAM. Qdrant documents that a
            # cold graph turns every query into many small random reads.
            "hnsw_on_disk": _bool_env("QDRANT_HNSW_ON_DISK", False),
        }
        if vector_schema["algorithm"] == "HNSW":
            vector_schema.update(
                {
                    "m": int(sanitize_env(str(os.getenv("VECTOR_HNSW_M", 16)))),
                    "ef_construct": int(sanitize_env(str(os.getenv("VECTOR_HNSW_EF_CONSTRUCTION", 200)))),
                    "ef_runtime": int(sanitize_env(str(os.getenv("VECTOR_HNSW_EF_RUNTIME", 10)))),
                }
            )
        elif vector_schema["algorithm"] == "FLAT":
            # m=0 disables the graph, which is Qdrant's brute force search.
            vector_schema.update({"m": 0, "ef_construct": None, "ef_runtime": None})
        else:
            raise ValueError(
                f"Unsupported VECTOR_ALGORITHM for Qdrant: {vector_schema['algorithm']}. "
                "Qdrant supports FLAT and HNSW only. SVS-VAMANA is a Redis-only index type, "
                "set VECTOR_ALGORITHM to HNSW (or FLAT) when vector_store is qdrant."
            )
        return vector_schema

    def _quantization_config_from_env(self) -> Optional[models.ScalarQuantization]:
        quantization = str(sanitize_env(os.getenv("QDRANT_QUANTIZATION", "none"))).lower()
        if quantization in ("", "none", "off", "false"):
            return None
        if quantization != "int8":
            raise ValueError(f"Unsupported QDRANT_QUANTIZATION value: {quantization}. Supported: none, int8")
        return models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8,
                quantile=float(sanitize_env(str(os.getenv("QDRANT_QUANTIZATION_QUANTILE", 0.99)))),
                always_ram=_bool_env("QDRANT_QUANTIZATION_ALWAYS_RAM", True),
            )
        )

    def _payload_index_schema(self) -> dict:
        """
        Payload indexes for every field this connector filters on. Fields that are
        stored but never filtered (url, timestamp, etag) are left unindexed because
        Qdrant keeps all values of an indexed field in RAM.
        """
        # Exact match fields. bucket_name and site_name carry the access control
        # decision, so they must never be tokenized.
        keyword_fields = ["bucket_name", "site_name", "object_name", "file_id", "link_id"]
        keyword_fields.extend([f"Header{i}" for i in range(1, 7)])
        integer_fields = ["start_index", "creation_date", "ingestion_date", "last_update_date"]

        schema = {
            field: models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD)
            for field in keyword_fields
        }
        schema.update({
            field: models.IntegerIndexParams(type=models.IntegerIndexType.INTEGER, lookup=True, range=True)
            for field in integer_fields
        })
        # Word intersection matching, mirrors the Redis text fields queried with `%`.
        schema.update({
            field: models.TextIndexParams(type=models.TextIndexType.TEXT)
            for field in ["file_title", "author"]
        })

        return schema

    def _collection_name(self) -> str:
        collection_name = sanitize_env(os.getenv("QDRANT_COLLECTION_NAME", None))
        if collection_name:
            return collection_name

        schema = self._vector_schema_from_env()
        model_name = sanitize_env(os.getenv("EMBEDDING_MODEL_NAME", "default")).replace("/", "_").replace("-", "_")
        return f"{model_name.lower()}_{schema['algorithm'].lower()}_{schema['datatype'].value}_{schema['distance_metric'].value.lower()}_{schema['dims']}"

    def get_client(self) -> AsyncQdrantClient:
        """
        Returns the Qdrant client, connecting lazily so that no network I/O
        happens at import or construction time.
        """
        if self._client is None:
            self._client = AsyncQdrantClient(**ConnectorQdrant.connection_config_from_env())
        return self._client

    async def _create_collection(self, collection_name: str) -> None:
        client = self.get_client()
        schema = self._vector_schema_from_env()
        logger.info(f"Creating collection: {collection_name}")

        hnsw_config = models.HnswConfigDiff(m=schema['m'], ef_construct=schema['ef_construct'], on_disk=schema['hnsw_on_disk'])
        try:
            await client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    ConnectorQdrant.EMBEDDING_FIELD_NAME: models.VectorParams(
                        size=schema['dims'],
                        distance=schema['distance_metric'],
                        datatype=schema['datatype'],
                        on_disk=schema['on_disk'],
                        hnsw_config=hnsw_config,
                    )
                },
                on_disk_payload=schema['on_disk_payload'],
                quantization_config=self._quantization_config_from_env(),
            )
        except UnexpectedResponse as e:
            if e.status_code == 409:
                logger.info(f"Collection {collection_name} already exists, reusing it.")
                return
            raise

    async def _ensure_payload_indexes(self, collection_name: str) -> None:
        """
        Creates every payload index this connector filters on. Payload indexes
        have to exist before any point is written, otherwise the filterable HNSW
        graph never gets its filter aware edges, and they cannot be retrofitted
        without a reindex. Called on every path into vector_collection - fresh
        create, 409 race and pre-existing collection - because a collection that
        already exists is the common case on redeploy, restored volume or a
        second ingestion pod. create_payload_index is idempotent in Qdrant for an
        identical schema, so repeating it is free.
        """
        client = self.get_client()
        for field_name, field_schema in self._payload_index_schema().items():
            await client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema,
            )

    async def vector_collection(self) -> str:
        """
        Returns the name of the collection, creating it on first use.
        """
        collection_name = self._collection_name()
        if self.collection_dict.get(collection_name, False):
            return collection_name

        client = self.get_client()
        if not await client.collection_exists(collection_name):
            await self._create_collection(collection_name)
        await self._ensure_payload_indexes(collection_name)
        self.collection_dict[collection_name] = True
        return collection_name

    def _forget_collection(self) -> None:
        """
        Drops the memoized existence of the current collection so the next call
        checks the server again. Without this a volume reset, snapshot restore,
        manual drop or helm reinstall makes every read return zero documents and
        every write fail until the pod restarts.
        """
        self.collection_dict.pop(self._collection_name(), None)

    async def existing_collection(self) -> Optional[str]:
        """
        Returns the name of the collection or None when it does not exist yet.
        Read paths must not create the collection: the retriever may be given a
        read only API key.
        """
        collection_name = self._collection_name()
        if self.collection_dict.get(collection_name, False):
            return collection_name
        if not await self.get_client().collection_exists(collection_name):
            return None
        self.collection_dict[collection_name] = True
        return collection_name

    def _point_id(self, text: str, metadata: dict) -> str:
        """
        Deterministic point id so that reingesting the same chunk overwrites it
        instead of duplicating it. Qdrant accepts only u64 or UUID identifiers.
        The natural key is the owning document id, the chunk offset and the chunk
        text, which is what makes a chunk unique in this product.
        """
        document_id = metadata.get("file_id") or metadata.get("link_id") or ""
        start_index = metadata.get("start_index", "")
        doc_id = metadata.get("doc_id", "")
        page = metadata.get("page", "")
        summary = metadata.get("summary", "")
        return str(uuid.uuid5(
            ConnectorQdrant.POINT_ID_NAMESPACE,
            f"{document_id}|{start_index}|{doc_id}|{page}|{summary}|{text}",
        ))

    def _process_data(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]=None):
        if len(embeddings) != len(texts):
            raise ValueError(f"Got {len(texts)} texts but {len(embeddings)} embeddings, they have to match.")
        if metadatas is not None and len(metadatas) != len(texts):
            raise ValueError(f"Got {len(texts)} texts but {len(metadatas)} metadata entries, they have to match.")

        points = []
        for text, embedding, metadata in zip(texts, embeddings, metadatas or [None] * len(texts)):
            metadata = metadata if metadata is not None else {}
            points.append(
                models.PointStruct(
                    id=self._point_id(text, metadata),
                    vector={ConnectorQdrant.EMBEDDING_FIELD_NAME: embedding},
                    payload={ConnectorQdrant.CONTENT_FIELD_NAME: text, **metadata},
                )
            )
        return points

    async def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]=None):
        try:
            points = self._process_data(texts, embeddings, metadatas)
            collection_name = await self.vector_collection()
            client = self.get_client()

            for offset in range(0, len(points), self.batch_size):
                batch = points[offset:offset + self.batch_size]
                # wait=True only on the last batch: it acts as a visibility barrier
                # so that a read straight after ingestion sees the data, without
                # blocking the update queue on every batch.
                is_last_batch = offset + self.batch_size >= len(points)
                result = await client.upsert(collection_name=collection_name, points=batch, wait=is_last_batch)
                if result.status not in (models.UpdateStatus.COMPLETED, models.UpdateStatus.ACKNOWLEDGED):
                    raise RuntimeError(f"Qdrant upsert did not succeed, status: {result.status}")

            return [point.id for point in points]
        except UnexpectedResponse as e:
            if e.status_code == 404:
                # The collection was memoized as existing but is gone from the
                # server. Forget it so the next attempt recreates it.
                self._forget_collection()
            logger.exception("Error occured while adding texts")
            raise e
        except Exception as e:
            logger.exception("Error occured while adding texts")
            raise e

    async def search_by_metadata(self, field_name: str, field_value: str):
        raise NotImplementedError("search_by_metadata is not implemented for Qdrant")

    async def search_and_delete_by_metadata(self, field_name: str, field_value: str):
        collection_name = await self.existing_collection()
        if collection_name is None:
            logger.warning("No such collection found in vector store. Import data first.")
            return

        logger.debug(f"Deleting documents with {field_name}={field_value}")
        await self.get_client().delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key=field_name, match=models.MatchValue(value=field_value))]
                )
            ),
            wait=True,
        )

    @staticmethod
    def _as_qdrant_filter(filter_expression) -> Optional[models.Filter]:
        if filter_expression is None:
            return None
        if isinstance(filter_expression, QdrantFilterExpression):
            return filter_expression.qdrant_filter
        if isinstance(filter_expression, models.Filter):
            return filter_expression
        raise ValueError(f"Unsupported filter expression type for Qdrant: {type(filter_expression)}")

    def _search_params(self, schema: dict) -> Optional[models.SearchParams]:
        if schema['algorithm'] != "HNSW":
            return None
        return models.SearchParams(hnsw_ef=schema['ef_runtime'])

    def _to_vector_distance(self, score: float) -> float:
        """
        Converts a Qdrant score into the lower-is-better distance the rest of the
        pipeline expects. Qdrant returns a similarity for cosine and dot product
        but the raw distance for euclid.
        """
        if self._distance() == models.Distance.EUCLID:
            return score
        return 1.0 - score

    def _to_score_threshold(self, distance_threshold: float) -> float:
        if self._distance() == models.Distance.EUCLID:
            return distance_threshold
        return 1.0 - distance_threshold

    def _convert_to_text_doc(self, point, vector_distance: float) -> TextDoc:
        """Helper method to convert a raw Qdrant point to a TextDoc"""
        payload = point.payload or {}
        metadata = {key: value for key, value in payload.items() if key != ConnectorQdrant.CONTENT_FIELD_NAME}
        metadata["id"] = str(point.id)
        metadata[ConnectorQdrant.DISTANCE_FIELD_NAME] = vector_distance

        return TextDoc(
            text=payload.get(ConnectorQdrant.CONTENT_FIELD_NAME, ""),
            metadata=metadata
        )

    def _parse_search_results(self, input_text: str, results: Iterable[Any]) -> SearchedDoc:
        searched_docs = []
        for r in results:
            searched_docs.append(self._convert_to_text_doc(r, self._to_vector_distance(r.score)))

        return SearchedDoc(retrieved_docs=searched_docs, user_prompt=input_text)

    async def similarity_search_by_vector(self, input_text: str, embedding: List[float], k: int, distance_threshold: float = None, filter_expression: Optional[Union[str, QdrantFilterExpression]] = None, parse_result: bool = True) -> SearchedDoc:
        try:
            query_filter = ConnectorQdrant._as_qdrant_filter(filter_expression)
            schema = self._vector_schema_from_env()
            logger.info(
                f"Building vector query: k={k}, distance_threshold={distance_threshold}, "
                f"datatype={schema['datatype'].value}, filter_expression={str(filter_expression)}"
            )

            collection_name = await self.existing_collection()
            if collection_name is None:
                logger.warning("No such collection found in vector store. Import data first.")
                return SearchedDoc(retrieved_docs=[], user_prompt=input_text)

            result = await self.get_client().query_points(
                collection_name=collection_name,
                query=embedding,
                using=ConnectorQdrant.EMBEDDING_FIELD_NAME,
                limit=k,
                query_filter=query_filter,
                with_payload=True,
                # Never ship vectors back, they would be read from disk.
                with_vectors=False,
                score_threshold=None if distance_threshold is None else self._to_score_threshold(distance_threshold),
                search_params=self._search_params(schema),
            )

            if parse_result:
                return self._parse_search_results(input_text=input_text, results=result.points)
            else:
                return result
        except UnexpectedResponse as e:
            if e.status_code == 404:
                self._forget_collection()
                logger.warning("No such collection found in vector store. Import data first.")
                return SearchedDoc(retrieved_docs=[], user_prompt=input_text)
            logger.exception("Error occured while searching by vector")
            raise e
        except Exception as e:
            logger.exception("Error occured while searching by vector")
            raise e

    def get_files_filter_expression(self) -> QdrantFilterExpression:
        """
        Filters out links by requiring link_id to be absent, so only files remain.
        Returns:
            QdrantFilterExpression: Returns a filter expression matching only files.
        """
        logger.debug("Adding files filter expression")
        return QdrantFilterExpression(
            models.Filter(must=[models.IsEmptyCondition(is_empty=models.PayloadField(key="link_id"))])
        )

    def get_links_filter_expression(self) -> QdrantFilterExpression:
        """
        Filters out files by requiring file_id to be absent, so only links remain.
        Returns:
            QdrantFilterExpression: Returns a filter expression to query only links.
        """
        logger.debug("Adding links filter expression")
        return QdrantFilterExpression(
            models.Filter(must=[models.IsEmptyCondition(is_empty=models.PayloadField(key="file_id"))])
        )

    def get_bucket_name_filter_expression(self, bucket_names: List[str]) -> QdrantFilterExpression:
        """
        Constructs a filter expression for bucket names.
        Args:
            bucket_names (List[str]): List of bucket names to filter by.
        Returns:
            QdrantFilterExpression: The filter expression for the bucket names.
        Raises:
            ValueError: If bucket_names is empty.
        """
        logger.debug(f"Bucket names in filter expression: {bucket_names}")
        if len(bucket_names) == 0:
            raise ValueError("Bucket names list cannot be empty")

        bucket_name_filter = QdrantFilterExpression(
            models.Filter(must=[models.FieldCondition(key="bucket_name", match=models.MatchAny(any=list(bucket_names)))])
        )
        logger.debug(f"Filter expression for bucket names: {str(bucket_name_filter)}")
        return bucket_name_filter

    def get_site_name_filter_expression(self, site_names: List[str]) -> QdrantFilterExpression:
        """
        Constructs a filter expression for SharePoint site names.
        Args:
            site_names (List[str]): List of site names to filter by.
        Returns:
            QdrantFilterExpression: The filter expression for the site names.
        Raises:
            ValueError: If site_names is empty.
        """
        logger.debug(f"Site names in filter expression: {site_names}")
        if len(site_names) == 0:
            raise ValueError("Site names list cannot be empty")

        site_name_filter = QdrantFilterExpression(
            models.Filter(must=[models.FieldCondition(key="site_name", match=models.MatchAny(any=list(site_names)))])
        )
        logger.debug(f"Filter expression for site names: {str(site_name_filter)}")
        return site_name_filter

    def get_object_name_filter_expression(self, bucket_name: str, object_name: str) -> QdrantFilterExpression:
        """
        Constructs a filter expression for bucket name and object name.
        Args:
            bucket_name (str): The name of the bucket.
            object_name (str): The name of the object.
        Returns:
            QdrantFilterExpression: The filter expression for the bucket and object name.
        Raises:
            ValueError: If bucket_name and/or object_name is empty.
        """
        if len(bucket_name) == 0 or len(object_name) == 0:
            raise ValueError("Bucket name and object name cannot be empty")

        bucket_object_filter = QdrantFilterExpression(
            models.Filter(must=[
                models.FieldCondition(key="bucket_name", match=models.MatchValue(value=bucket_name)),
                models.FieldCondition(key="object_name", match=models.MatchValue(value=object_name)),
            ])
        )
        logger.debug(f"Filter expression for bucket name and object name: {str(bucket_object_filter)}")
        return bucket_object_filter

    async def _scroll_chunks(self, collection_name: str, scroll_filter: models.Filter) -> List[Any]:
        points, _ = await self.get_client().scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=ConnectorQdrant.SIBLING_SCAN_LIMIT,
            with_payload=True,
            with_vectors=False,
        )
        return points

    async def similarity_search_with_siblings(self, input_text: str, embedding: List[float],
                                              k: int,
                                              distance_threshold: float = None,
                                              filter_expression: Optional[Union[str, QdrantFilterExpression]] = None) -> SearchedDoc:
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

        # If no results or error, return empty result
        if not hasattr(initial_result, 'points') or not initial_result.points:
            return SearchedDoc(retrieved_docs=[], user_prompt=input_text)

        collection_name = await self.existing_collection()
        base_filter = ConnectorQdrant._as_qdrant_filter(filter_expression)

        # Process the main retrieved documents
        primary_docs = [
            self._convert_to_text_doc(point, self._to_vector_distance(point.score))
            for point in initial_result.points
        ]

        logger.debug(f"Found {len(primary_docs)} primary documents for input: {input_text}")
        all_sibling_docs = {}

        # We only find siblings for files therefore use file_id for file uniqueness.
        # Using object_name would not work since it might not be unique across different buckets.
        for point in initial_result.points:
            sibling_docs = []
            payload = point.payload or {}
            if "file_id" not in payload or "start_index" not in payload:
                continue

            object_id = payload["file_id"]
            start_index = int(payload["start_index"])

            conditions = [models.FieldCondition(key="file_id", match=models.MatchValue(value=object_id))]
            if base_filter is not None:
                conditions.append(base_filter)

            header_conditions = []
            for i in range(1, 7):
                header_value = payload.get(f'Header{i}', None)
                if header_value:
                    header_conditions.append(
                        models.FieldCondition(key=f'Header{i}', match=models.MatchValue(value=header_value))
                    )

            if header_conditions:
                # Case 1: Document has headers - get siblings with matching headers
                header_filter = models.Filter(must=conditions + header_conditions)
                header_chunks = await self._scroll_chunks(collection_name, header_filter)
                logger.debug(f"Retrieved header chunks: {len(header_chunks)} for header_filter: {header_filter}")

                if header_chunks:
                    sorted_chunks = sorted(header_chunks, key=lambda x: int((x.payload or {}).get('start_index', 0)))
                    current_pos = -1
                    for i, chunk in enumerate(sorted_chunks):
                        if chunk.id == point.id:
                            current_pos = i
                            break

                    if current_pos != -1:
                        if current_pos > 0:
                            sibling_docs.append(self._convert_to_text_doc(sorted_chunks[current_pos - 1], -1))

                        if current_pos < len(sorted_chunks) - 1:
                            sibling_docs.append(self._convert_to_text_doc(sorted_chunks[current_pos + 1], -1))
            else:
                # Case 2: Document doesn't have headers - get nearest chunks by start_index
                before_filter = models.Filter(
                    must=conditions + [models.FieldCondition(key="start_index", range=models.Range(lt=start_index))]
                )
                before_chunks = await self._scroll_chunks(collection_name, before_filter)

                if before_chunks:
                    prev_chunk = max(before_chunks, key=lambda x: int((x.payload or {}).get('start_index', 0)))
                    logger.debug(f"Retrieved previous chunk: {prev_chunk.id, (prev_chunk.payload or {}).get('start_index')}")
                    # Siblings do not have a distance score
                    sibling_docs.append(self._convert_to_text_doc(prev_chunk, -1))

                after_filter = models.Filter(
                    must=conditions + [models.FieldCondition(key="start_index", range=models.Range(gt=start_index))]
                )
                after_chunks = await self._scroll_chunks(collection_name, after_filter)

                if after_chunks:
                    next_chunk = min(after_chunks, key=lambda x: int((x.payload or {}).get('start_index', 0)))
                    logger.debug(f"Retrieved next chunk: {next_chunk.id, (next_chunk.payload or {}).get('start_index')}")
                    # Siblings do not have a distance score
                    sibling_docs.append(self._convert_to_text_doc(next_chunk, -1))

            all_sibling_docs[str(point.id)] = sibling_docs

        logger.debug(f"Final sibling docs: {all_sibling_docs}")
        return SearchedDoc(retrieved_docs=primary_docs, sibling_docs=all_sibling_docs, user_prompt=input_text)

    def get_author_filter_expression(self, authors: Union[str, List[str]]) -> QdrantFilterExpression:
        """
        Constructs a filter expression for one or more authors.
        Args:
            authors (Union[str, List[str]]): Single author name or list of author names to filter by.
        Returns:
            QdrantFilterExpression: The filter expression for author(s) - uses OR logic for multiple authors.
        Raises:
            ValueError: If authors is empty, contains only whitespace, or is an empty list.
        """
        # Normalize to list
        author_list = [authors] if isinstance(authors, str) else authors

        if not author_list or (len(author_list) == 1 and not author_list[0].strip()):
            raise ValueError("Author(s) cannot be empty")

        # Filter out empty strings and strip whitespace
        author_list = [a.strip() for a in author_list if a and a.strip()]

        if not author_list:
            raise ValueError("Author(s) cannot be empty after filtering")

        logger.debug(f"Adding author filter expression for {len(author_list)} author(s): {author_list}")

        # MatchText is a word intersection match on the full text index, which is
        # the equivalent of the Redis `%` operator used for authors.
        return QdrantFilterExpression(
            models.Filter(should=[
                models.FieldCondition(key="author", match=models.MatchText(text=author))
                for author in author_list
            ])
        )

    def get_text_exclude_filter_expression(self, field: str, value: str) -> QdrantFilterExpression:
        """
        Constructs a negated filter expression for any text field (NOT match).
        Args:
            field (str): The text field name (e.g. 'author', 'file_title').
            value (str): The value to exclude.
        Returns:
            QdrantFilterExpression: The negated filter expression.
        Raises:
            ValueError: If field or value is empty or whitespace.
        """
        if not field or not field.strip():
            raise ValueError("Field name cannot be empty")
        if not value or not value.strip():
            raise ValueError("Exclusion value cannot be empty")
        value = value.strip()
        logger.debug(f"Adding exclusion filter expression for {field}: {value}")
        return QdrantFilterExpression(
            models.Filter(must_not=[models.FieldCondition(key=field, match=models.MatchText(text=value))])
        )

    def get_author_exclude_filter_expression(self, author: str) -> QdrantFilterExpression:
        """
        Constructs a negated word-intersection filter for author.
        Uses the same matching logic as inclusion so that e.g.
        excluding "Jane Doe" also excludes "Doe, Jane".
        """
        if not author or not author.strip():
            raise ValueError("Author exclusion value cannot be empty")
        logger.debug(f"Adding author exclusion filter expression: {author.strip()}")
        return self.get_text_exclude_filter_expression("author", author)

    # File extensions that indicate the query value is a filename (not a document title)
    _FILENAME_EXTENSIONS = frozenset({
        "pdf", "docx", "xlsx", "pptx", "doc", "xls", "ppt",
        "txt", "md", "json", "yaml", "yml", "csv", "html", "xml", "log",
    })

    @staticmethod
    def _looks_like_filename(value: str) -> bool:
        """Return True if *value* has a recognised file extension."""
        dot = value.rfind(".")
        return dot > 0 and value[dot + 1:].lower() in ConnectorQdrant._FILENAME_EXTENSIONS

    def get_title_filter_expression(self, title_pattern: str, exact_match: bool = False) -> QdrantFilterExpression:
        """
        Constructs a filter expression for file_title field.

        When the pattern looks like a filename (e.g. ``report.pptx``), the
        expression also searches the ``object_name`` field with OR logic so
        that files stored by their original name can be found.

        Args:
            title_pattern (str): The title or pattern to filter by.
            exact_match (bool): If True, use exact match; if False, use word intersection.
        Returns:
            QdrantFilterExpression: The filter expression for file_title (and optionally object_name).
        Raises:
            ValueError: If title_pattern is empty.
        """
        if not title_pattern or not title_pattern.strip():
            raise ValueError("Title pattern cannot be empty")
        title_pattern = title_pattern.strip()
        logger.debug(f"Adding title filter expression: {title_pattern}, exact_match={exact_match}")

        if exact_match:
            title_condition = models.FieldCondition(key="file_title", match=models.MatchValue(value=title_pattern))
        else:
            title_condition = models.FieldCondition(key="file_title", match=models.MatchText(text=title_pattern))

        # When the value is a filename, also search object_name (stores the
        # original uploaded file name / object key in the bucket).
        if ConnectorQdrant._looks_like_filename(title_pattern):
            logger.debug(f"Filename detected - also searching object_name for: {title_pattern}")
            return QdrantFilterExpression(
                models.Filter(should=[
                    title_condition,
                    models.FieldCondition(key="object_name", match=models.MatchText(text=title_pattern)),
                ])
            )

        return QdrantFilterExpression(models.Filter(must=[title_condition]))

    def get_date_range_filter_expression(self, field: str, start: int = None, end: int = None) -> QdrantFilterExpression:
        """
        Constructs a filter expression for date range filtering.
        Args:
            field (str): The date field to filter by. Must be one of: creation_date, ingestion_date, or last_update_date.
            start (int): Optional start timestamp (inclusive). If None, only end is used.
            end (int): Optional end timestamp (inclusive). If None, only start is used.
        Returns:
            QdrantFilterExpression: The filter expression for the date range.
        Raises:
            ValueError: If field is invalid or both start and end are None.
        """
        if field not in ("creation_date", "ingestion_date", "last_update_date"):
            raise ValueError(f"Invalid date field: {field}")
        if start is None and end is None:
            raise ValueError("At least one of start or end timestamp required")
        return QdrantFilterExpression(
            models.Filter(must=[models.FieldCondition(key=field, range=models.Range(gte=start, lte=end))])
        )

    @staticmethod
    def connection_config_from_env() -> dict:
        """
        Builds the AsyncQdrantClient keyword arguments from environment variables.
        QDRANT_API_KEY is the only key the connector reads, so the connector holds
        no privilege policy of its own: the deployment decides which key a pod
        gets. The retriever is given the read-only key under this name so the read
        path cannot write to the database.
        Returns:
            dict: The Qdrant client connection configuration.
        """
        config = {
            "port": int(sanitize_env(str(os.getenv("QDRANT_PORT", 6333)))),
            "grpc_port": int(sanitize_env(str(os.getenv("QDRANT_GRPC_PORT", 6334)))),
            "prefer_grpc": _bool_env("QDRANT_PREFER_GRPC", False),
            "api_key": sanitize_env(os.getenv("QDRANT_API_KEY", None)),
        }

        qdrant_url = sanitize_env(os.getenv("QDRANT_URL", None))
        if qdrant_url:
            config["url"] = qdrant_url
        else:
            config["host"] = sanitize_env(os.getenv("QDRANT_HOST", "localhost"))
            config["https"] = _bool_env("QDRANT_HTTPS", False)

        timeout = sanitize_env(os.getenv("QDRANT_TIMEOUT", None))
        if timeout:
            config["timeout"] = int(timeout)

        # Never log the API key.
        logger.info(f"Qdrant connection: {({k: v for k, v in config.items() if k != 'api_key'})}")
        return config
