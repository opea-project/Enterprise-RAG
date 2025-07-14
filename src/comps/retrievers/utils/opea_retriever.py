# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc
from comps.vectorstores.utils.opea_vectorstore import OPEAVectorStore
from comps.cores.mega.logger import get_opea_logger, change_opea_logger_level
from comps.vectorstores.utils.opea_rbac import retrieve_bucket_list

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

class OPEARetriever:
    """
    Singleton class for managing ingestion into vector stores via microservice API calls.
    """

    _instance = None

    def __new__(cls, vector_store: str, rbac_enabled: bool = False):
        if cls._instance is None:
            cls._instance = super(OPEARetriever, cls).__new__(cls)
            cls._instance._initialize(vector_store, rbac_enabled)
        return cls._instance

    def _initialize(self, vector_store: str, rbac_enabled: bool = False):
        self.vector_store = OPEAVectorStore(vector_store)
        self.rbac_enabled = rbac_enabled

    def filter_expression_from_rbac_by(self, rbac_by: dict = None):
        if rbac_by is not None and 'bucket_names' in rbac_by: # bucket_names can be empty meaning no access
            try:
                return self.vector_store.get_bucket_name_filter_expression(bucket_names=rbac_by['bucket_names'])
            except ValueError:
                logger.warning("No access due rbac with empty bucket_names value")
                return None
        return None

    def filter_expression_from_search_by(self, search_by: dict = {}):
        logger.debug(f"Generating filter expression from search_by: {search_by}")
        filter_expression = None
        if 'object_name' in search_by and 'bucket_name' in search_by:
            try:
                filter_expression = self.vector_store.get_object_name_filter_expression(bucket_name=search_by['bucket_name'], object_name=search_by['object_name'])
                logger.debug(f"Searching by bucket_name and object_name {search_by['bucket_name']} {search_by['object_name']}")
            except ValueError:
                logger.warning("Empty bucket_name and/or object_name value in search_by")
        if 'bucket_names' in search_by:
            try:
                filter_expression = self.vector_store.get_bucket_name_filter_expression(bucket_names=search_by['bucket_names'])
                logger.debug(f"Searching by bucket_names {search_by['bucket_names']}")
            except ValueError:
                logger.warning("Empty bucket_names value in search_by")
            # Feature: add from<->to document created date range filtering
            # Feature: file extensions filtering
        return filter_expression

    def generate_retrieve_filter_expression(self, filter_expression, rbac_filter_expression):
        """
        Generate filter expression for retrieval so that the search filters and rbac filters are correcly combined.
        This combination is especially importand since filters cannot be combined if any of them is NoneType.
        The filter_expression is the search filter expression (Optional) and rbac_filter_expression is the RBAC filter expression.
        RBAC filter has to be ad the end of the expression to ensure that it applies to any other filter expression defined by filter_expression.
        Finally, since those filters apply to files, and OR filter to include links has to be appended.
        """
        filter_links_expression = self.vector_store.get_links_filter_expression()
        new_filter_expression = None

        if self.rbac_enabled:
            if rbac_filter_expression is None:
                new_filter_expression = filter_links_expression # no access to data
            else:
                if filter_expression is not None:
                    new_filter_expression = (filter_expression & rbac_filter_expression) | filter_links_expression
                else:
                    new_filter_expression = rbac_filter_expression | filter_links_expression
        else:
            if filter_expression is not None:
                new_filter_expression = filter_expression | filter_links_expression
            else:
                new_filter_expression = None # no filter expression, search all files and links

        logger.debug(f"Generated filter expression for retrieval: {str(new_filter_expression)}")
        return new_filter_expression

    def generate_hierarchical_retrieve_filter_expression(self, filter_expression, additional_expression, rbac_filter_expression):
        """
        Generate filter expression for hierarchical retrieval so that the search filters, hierarchical filters and rbac filters are correcly combined.
        This combination is especially importand since filters cannot be combined if any of them is NoneType.
        The filter_expression is the search filter expression (Optional), additional_expression is the hierarchical filter expression (e.g. summaries or chunks), and rbac_filter_expression is the RBAC filter expression.
        RBAC filter has to be ad the end of the expression to ensure that it applies to any other filter expression defined by filter_expression.
        Finally, since those filters apply to files, and OR filter to include links has to be appended.

        The difference between generate_hierarchical_retrieve_filter_expression and generate_retrieve_filter_expression
        is that the former allows for additional filters to be applied on top of the search filter expression,
        and is separated to different method so that there is no additional conditional layer on in one method.
        """
        filter_links_expression = self.vector_store.get_links_filter_expression()
        new_filter_expression = None
        if additional_expression is None:
            raise ValueError("Additional expression for hierarchical retrieval cannot be None.")

        if self.rbac_enabled:
            if rbac_filter_expression is None:
                new_filter_expression = filter_links_expression # no access to data
            else:
                if filter_expression is not None:
                    new_filter_expression = (filter_expression & additional_expression & rbac_filter_expression) | filter_links_expression
                else:
                    new_filter_expression = (additional_expression & rbac_filter_expression) | filter_links_expression
        else:
            if filter_expression is not None:
                new_filter_expression = (filter_expression & additional_expression) | filter_links_expression
            else:
                new_filter_expression = additional_expression | filter_links_expression # additional filter or links
        
        logger.debug(f"Generated filter expression for hierarchical retrieval: {str(new_filter_expression)}")
        return new_filter_expression

    async def retrieve(self, input: EmbedDoc, search_by: dict = None, rbac_by: dict = None) -> SearchedDoc:
        filter_expression = self.filter_expression_from_search_by(search_by=search_by)
        rbac_filter_expression = self.filter_expression_from_rbac_by(rbac_by=rbac_by)
        retrieve_filter_expression = self.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
        return await self.vector_store.search(input=input, filter_expression=retrieve_filter_expression)

    async def hierarchical_retrieve(self, input: EmbedDoc, k_summaries: int, k_chunks: int, search_by: dict = None, rbac_by: dict = None) -> SearchedDoc:
        filter_expression = self.filter_expression_from_search_by(search_by=search_by)
        rbac_filter_expression = self.filter_expression_from_rbac_by(rbac_by=rbac_by)

        # Fetch summaries using filter expression
        summary_expression = self.vector_store.get_hierarchical_summary_filter_expression()
        new_filter_expression = self.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_expression, rbac_filter_expression)
        summary_vectors = await self.vector_store.search(input=input, filter_expression=new_filter_expression)

        # Choose first k_summaries summary vectors
        docid_page_list = []
        for summary_doc in summary_vectors.retrieved_docs[:k_summaries]:
            docid_page_list.append((summary_doc.metadata["doc_id"], summary_doc.metadata["page"]))

        # Fetch chunks using filter expression
        retrieved_docs = []
        for doc_id, page in docid_page_list:
            chunk_expression = self.vector_store.get_hierarchical_chunk_filter_expression(doc_id, page)
            new_filter_expression = self.generate_hierarchical_retrieve_filter_expression(filter_expression, chunk_expression, rbac_filter_expression)
            chunk_vectors = await self.vector_store.search(input=input, filter_expression=new_filter_expression)
            # Choose first k_chunks chunk vectors for each summary/page
            retrieved_docs.extend(chunk_vectors.retrieved_docs[:k_chunks])

        return SearchedDoc(retrieved_docs=retrieved_docs, user_prompt=input.text)

    def generate_search_by(self, request_json: dict = {}) -> dict:
        return request_json['search_by'] if 'search_by' in request_json else {}

    def generate_rbac(self, auth_header: str = "") -> dict:
        try:
            items = retrieve_bucket_list(auth_header)
            items = items['buckets'] if items and 'buckets' in items else []
            return { 'bucket_names': items }
        except ValueError as e:
            logger.error(f"Returning empty list of buckets due to RBAC request error: {e}")
            return { 'bucket_names': [] }
