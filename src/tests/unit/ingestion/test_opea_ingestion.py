# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest import mock
from comps.cores.proto.docarray import EmbedDoc, EmbedDocList
from comps.ingestion.utils.opea_ingestion import OPEAIngestion

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

def test_ingest_multiple_docs(mock_vectorstore):
    docs = [
        EmbedDoc(text="doc1", embedding=[1,2,3]),
        EmbedDoc(text="doc2", embedding=[1,2,3])
    ]
    input_docs = EmbedDocList(docs=docs)
    ingestion = OPEAIngestion("redis")
    result = ingestion.ingest(input_docs)

    assert len(result.docs) == 2

def test_ingest_single_docs(mock_vectorstore):
    doc = EmbedDoc(text="doc1", embedding=[1,2,3])

    input_docs = EmbedDocList(docs=[doc])
    ingestion = OPEAIngestion("redis")
    result = ingestion.ingest(input_docs)

    assert isinstance(result.docs[0], EmbedDoc)
    assert result.docs[0].text == "doc1"
