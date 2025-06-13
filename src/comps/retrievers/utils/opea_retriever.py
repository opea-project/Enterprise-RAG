# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.docarray import EmbedDoc, SearchedDoc
from comps.vectorstores.utils.opea_vectorstore import OPEAVectorStore

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

    async def retrieve(self, input: EmbedDoc) -> SearchedDoc:
        return await self.vector_store.search(input=input)

    async def hierarchical_retrieve(self, input: EmbedDoc, k_summaries: int, k_chunks: int) -> SearchedDoc:
        # Fetch summaries using filter expression
        summary_expression = '@summary:[1 1]'
        summary_vectors = await self.vector_store.search(input=input, filter_expression=summary_expression)

        # Choose first k_summaries summary vectors
        docid_page_list = []
        for summary_doc in summary_vectors.retrieved_docs[:k_summaries]:
            docid_page_list.append((summary_doc.metadata["doc_id"], summary_doc.metadata["page"]))

        # Fetch chunks using filter expression
        retrieved_docs = []
        for doc_id, page in docid_page_list:
            chunk_expression = f'((@doc_id:("{doc_id}") @page:[{page} {page}]) @summary:[0 0])'
            chunk_vectors = await self.vector_store.search(input=input, filter_expression=chunk_expression)
            # Choose first k_chunks chunk vectors for each summary/page
            retrieved_docs.extend(chunk_vectors.retrieved_docs[:k_chunks])

        return SearchedDoc(retrieved_docs=retrieved_docs, user_prompt=input.text)
