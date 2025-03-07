# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest import mock
from comps.cores.proto.docarray import EmbedDoc
from comps.retrievers.utils.opea_retriever import OPEARetriever
from typing import List, Union, Optional
from redisvl.query.filter import FilterExpression, Text
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc, TextDoc

@pytest.fixture
def mock_vectorstore():
    class SearchRes:
        def __init__(self, content=""):
            self.page_content = content
    class MockDbClient:
        def __init__(self, *args, **kwargs):
            pass
        def add_texts(texts, **kwargs):
            return texts
        async def similarity_search_by_vector(input_text: str, embedding: List[float], k: int, distance_threshold: float = None, filter_expression: Optional[Union[str, FilterExpression]] = None, parse_result: bool = True):
            return SearchedDoc(
        initial_query="This is my sample query?",
        retrieved_docs=[
            TextDoc(text=""),
            TextDoc(text="  "),  
        ],
        top_n=1,
    )
        def similarity_search_with_relevance_scores(self,  input_text: str, embedding: List, k: int, score_threshold: float):
            return []
        def max_marginal_relevance_search(self, **kwargs):
            return []
        def _check_embedding_index(**kwargs):
            return True
        def _create_index_if_not_exist(**kwargs):
            return True
    with mock.patch('comps.vectorstores.utils.connectors.connector_redis.ConnectorRedis', return_value=MockDbClient):
        yield

@pytest.mark.asyncio
async def test_retrieve_docs(mock_vectorstore):
    input = EmbedDoc(text="test", embedding=[1,2,3])
    retriever = OPEARetriever("redis")
    result = await retriever.retrieve(input=input)
    assert len(result.retrieved_docs) == 2

def test_singleton_instance():
    retriever1 = OPEARetriever("redis")
    retriever2 = OPEARetriever("redis")
    assert retriever1 is retriever2

def test_initialize_method():
    retriever = OPEARetriever("redis")
    assert retriever.vector_store is not None
