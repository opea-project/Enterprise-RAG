# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc
from comps.vectorstores.utils.opea_vectorstore import OPEAVectorStore
from comps.cores.mega.logger import get_opea_logger, change_opea_logger_level
from comps.vectorstores.utils.opea_rbac import retrieve_bucket_list
from fastapi import Request

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

class OPEARetriever:
    """
    Singleton class for managing ingestion into vector stores via microservice API calls.
    """

    _instance = None

    def __new__(cls, vector_store: str):
        if cls._instance is None:
            cls._instance = super(OPEARetriever, cls).__new__(cls)
            cls._instance._initialize(vector_store)
        return cls._instance

    def _initialize(self, vector_store: str):
        self.vector_store = OPEAVectorStore(vector_store)

    def filter_expression_from_search_by(self, search_by: dict, skip_links=False):
        filter_expression = None
        if search_by:
            if 'object_name' in search_by and 'bucket_name' in search_by:
                try:
                    filter_expression = self.vector_store.get_object_name_filter_expression(bucket_name=search_by['bucket_name'], object_name=search_by['object_name'])
                    logger.debug(f"Searching by bucket name and object_name {search_by['bucket_name']} {search_by['object_name']}")
                except ValueError:
                    logger.warning("Empty bucket name and/or object name")
            if 'bucket_names' in search_by:
                try:
                    filter_expression = self.vector_store.get_bucket_name_filter_expression(bucket_names=search_by['bucket_names'])
                    logger.debug(f"Searching by bucket names {search_by['bucket_names']}")
                except ValueError:
                    logger.warning("Empty bucket names list")
            # Feature: add from<->to document created date range filtering
            # Feature: file extensions filtering
        if filter_expression is None:
            logger.debug("No search_by provided, using empty filter expression")
            filter_expression = self.vector_store.empty_filter_expression()

        if skip_links:
            return filter_expression
        else:
            return filter_expression | self.vector_store.get_links_filter_expression()

    async def retrieve(self, input: EmbedDoc, search_by: dict = None) -> SearchedDoc:
        filter_expression = self.filter_expression_from_search_by(search_by)
        return await self.vector_store.search(input=input, filter_expression=filter_expression)

    async def hierarchical_retrieve(self, input: EmbedDoc, k_summaries: int, k_chunks: int, search_by: dict = None) -> SearchedDoc:
        filter_expression = self.filter_expression_from_search_by(search_by=search_by, skip_links=True)

        # Fetch summaries using filter expression
        summary_expression = self.vector_store.get_hierarchical_summary_filter_expression()
        summary_vectors = await self.vector_store.search(input=input, filter_expression=(filter_expression & summary_expression) | self.vector_store.get_links_filter_expression())

        # Choose first k_summaries summary vectors
        docid_page_list = []
        for summary_doc in summary_vectors.retrieved_docs[:k_summaries]:
            docid_page_list.append((summary_doc.metadata["doc_id"], summary_doc.metadata["page"]))

        # Fetch chunks using filter expression
        retrieved_docs = []
        for doc_id, page in docid_page_list:
            chunk_expression = self.vector_store.get_hierarchical_chunk_filter_expression(doc_id, page)
            chunk_vectors = await self.vector_store.search(input=input, filter_expression=(filter_expression & chunk_expression) | self.vector_store.get_links_filter_expression())
            # Choose first k_chunks chunk vectors for each summary/page
            retrieved_docs.extend(chunk_vectors.retrieved_docs[:k_chunks])

        return SearchedDoc(retrieved_docs=retrieved_docs, user_prompt=input.text)

    def filter_expression_for_rbac(self, request: Request) -> dict:
        try:
            items = retrieve_bucket_list(request.headers.get("Authorization", None))
            logger.debug(f"Retrieved bucket list: {items}")
            items = items['buckets'] if items and 'buckets' in items else []
            return {'bucket_names': items}
        except ValueError as e:
            logger.error(f"Error while retrieving bucket list: {str(e)}")
            return {}
