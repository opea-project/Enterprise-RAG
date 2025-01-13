# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest import mock
from comps.vectorstores.utils.wrappers.wrapper_qdrant import QdrantVectorStore

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
    with mock.patch('comps.vectorstores.utils.wrappers.wrapper_qdrant.QdrantVectorStore._client', return_value=MockDbClient):
        yield

def test_qdrant_singleton_behavior(mock_vectorstore):
    instance1 = QdrantVectorStore()
    instance2 = QdrantVectorStore()
    assert instance1 is instance2
    QdrantVectorStore._instance = None

def test_url_formatting_with_qdrant_url(monkeypatch, mock_vectorstore):
    with mock.patch('comps.vectorstores.utils.wrappers.wrapper_qdrant.OPEAQdrant', return_value=True):
        # Mock the environment variable
        monkeypatch.setenv('QDRANT_URL', 'http://localhost:1235')
        vs = QdrantVectorStore()
        
        assert vs.format_url_from_env() == 'http://localhost:1235'
        assert vs.client is not None
        
        # Reset the singleton instance
        QdrantVectorStore._instance = None

def test_url_formatting_with_qdrant_specific_envs_for_url(monkeypatch, mock_vectorstore):
    with mock.patch('comps.vectorstores.utils.wrappers.wrapper_qdrant.OPEAQdrant', return_value=True):
        # Mock the environment variable
        host = 'localhost'
        port = '1234'

        monkeypatch.setenv('QDRANT_HOST', host)
        monkeypatch.setenv('QDRANT_PORT', port)
        vs = QdrantVectorStore()
        
        assert vs.format_url_from_env() == 'http://localhost:1234/'
        assert vs.client is not None
        
        # Reset the singleton instance
        QdrantVectorStore._instance = None