# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest import mock
from comps.cores.proto.docarray import EmbedDoc
from comps.retrievers.utils.opea_retriever import OPEARetriever

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
        def similarity_search_by_vector(**kwargs):
            return [SearchRes('a'), SearchRes('b')]
        def similarity_search_with_relevance_scores(self,  **kwargs):
            return []
        def max_marginal_relevance_search(self, **kwargs):
            return []
        def _check_embedding_index(**kwargs):
            return True
        def _create_index_if_not_exist(**kwargs):
            return True
    with mock.patch('comps.vectorstores.utils.wrappers.wrapper_redis.RedisVectorStore._client', return_value=MockDbClient):
        yield

def test_retrieve_docs(mock_vectorstore):
    input = EmbedDoc(text="test", embedding=[1,2,3])
    retriever = OPEARetriever("redis")
    result = retriever.retrieve(input=input)
    print(result)
    assert len(result.retrieved_docs) == 2
