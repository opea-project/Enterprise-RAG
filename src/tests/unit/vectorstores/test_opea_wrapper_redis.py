# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest import mock
from comps.vectorstores.utils.wrappers.wrapper_redis import RedisVectorStore

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

def test_singleton_behavior(mock_vectorstore):
    instance1 = RedisVectorStore()
    instance2 = RedisVectorStore()
    assert instance1 is instance2
    RedisVectorStore._instance = None

def test_url_formatting_with_redis_url(monkeypatch, mock_vectorstore):
    # Mock the environment variable
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
    vs = RedisVectorStore()

    assert vs.format_url_from_env() == 'redis://localhost:6379'
    assert vs.client is not None

    # Reset the singleton instance
    RedisVectorStore._instance = None

def test_url_formatting_with_redis_specific_envs_for_url(monkeypatch, mock_vectorstore):
    # Mock the environment variable
    host = 'localhost'
    port = '1234'
    ssl = 'true'
    test_username = 'test'
    test_p = 'test'

    monkeypatch.setenv('REDIS_HOST', host)
    monkeypatch.setenv('REDIS_PORT', port)
    monkeypatch.setenv('REDIS_SSL', ssl)
    monkeypatch.setenv('REDIS_USERNAME', test_username)
    monkeypatch.setenv('REDIS_PASSWORD', test_p)
    vs = RedisVectorStore()

    assert vs.format_url_from_env() == f'rediss://{test_username}:{test_p}@{host}:{port}/'
    assert vs.client is not None

    # Reset the singleton instance
    RedisVectorStore._instance = None