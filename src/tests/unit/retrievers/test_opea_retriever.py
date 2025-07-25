# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.vectorstores.utils.connectors.connector_redis import ConnectorRedis
import pytest
from unittest import mock
from comps.cores.proto.docarray import EmbedDoc, SearchedDoc, TextDoc
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
        def get_files_filter_expression(self):
            return ConnectorRedis.get_files_filter_expression()
        def get_links_filter_expression(self):
            return ConnectorRedis.get_links_filter_expression()
        def get_object_name_filter_expression(self, bucket_name, object_name):
            return ConnectorRedis.get_object_name_filter_expression(bucket_name, object_name)
        def get_bucket_name_filter_expression(self, bucket_names):
            return ConnectorRedis.get_bucket_name_filter_expression(bucket_names)
        
    with mock.patch('comps.vectorstores.utils.connectors.connector_redis.ConnectorRedis', return_value=MockDbClient):
        yield

def test_filter_expression_from_rbac_by():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    rbac_by = {}
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    assert rbac_filter_expression is None

def test_filter_expression_from_rbac_by_no_access():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    rbac_by = {"bucket_names": []}
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    assert rbac_filter_expression is None

def test_filter_expression_from_rbac_by_valid_buckets():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    rbac_by = {"bucket_names": ["bucket1", "bucket2"]}
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    assert rbac_filter_expression is not None
    assert "bucket1" in str(rbac_filter_expression)
    assert "bucket2" in str(rbac_filter_expression)

def test_filter_expression_from_search_by():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is None

def test_filter_expression_from_search_by_bucket_names_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {"bucket_names": []}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is None

def test_filter_expression_from_search_by_bucket_names_valid():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {"bucket_names": ["bucket1", "bucket2"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is not None
    assert "bucket1" in str(filter_expression)
    assert "bucket2" in str(filter_expression)

def test_filter_expression_from_search_by_object_name_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {"bucket_name": "bucket1"}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is None

def test_filter_expression_from_search_by_bucket_name_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {"object_name": "bucket1"}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is None

def test_filter_expression_from_search_by_bucket_name_and_object_name_invalid():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {"bucket_name": "", "object_name": ""}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is None

def test_filter_expression_from_search_by_bucket_name_and_object_name_valid():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = {"bucket_name": "bucket1", "object_name": "object1"}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    assert filter_expression is not None
    assert "bucket1" in str(filter_expression)
    assert "object1" in str(filter_expression)

# ======================================

def test_generate_retrieve_filter_expression_with_bucket_names_and_rbac_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_names": ["bucket1", "bucket2"] }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" == str(result)

def test_generate_retrieve_filter_expression_with_bucket_name_and_object_name_and_rbac_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" == str(result)

def test_generate_retrieve_filter_expression_with_bucket_name_and_object_name_invalid_and_rbac_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "", "object_name": "" }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" == str(result)

def test_generate_retrieve_filter_expression_empty_and_rbac_filtered():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {}
    rbac_by = { "bucket_names": ["bucket1"] }
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_retrieve_filter_expression_with_bucket_names_and_rbac_missmatch():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_names": ["bucket1", "bucket2"] }
    rbac_by = {"bucket_names": ["bucket3"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" in str(result)

def test_generate_retrieve_filter_expression_with_bucket_name_and_object_name_and_rbac_missmatch():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {"bucket_names": ["bucket3"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" in str(result)

def test_generate_retrieve_filter_expression_with_bucket_names_and_rbac_match():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_names": ["bucket1", "bucket2"] }
    rbac_by = {"bucket_names": ["bucket1"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_retrieve_filter_expression_with_bucket_name_and_object_name_and_rbac_match():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {"bucket_names": ["bucket1"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_retrieve_filter_expression_with_bucket_name_and_object_name_and_rbac_disabled():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=False)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "object1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_retrieve_filter_expression_empty_and_rbac_disabled():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=False)
    search_by = {}
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_retrieve_filter_expression(filter_expression, rbac_filter_expression)
    assert result is None

# =============

def test_generate_hierarchical_retrieve_filter_expression_with_bucket_names_and_rbac_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_names": ["bucket1", "bucket2"] }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" == str(result)

def test_generate_hierarchical_filter_expression_with_bucket_name_and_object_name_and_rbac_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" == str(result)

def test_generate_hierarchical_filter_expression_with_bucket_name_and_object_name_invalid_and_rbac_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "", "object_name": "" }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" == str(result)

def test_generate_hierarchical_filter_expression_empty_and_rbac_filtered():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {}
    rbac_by = { "bucket_names": ["bucket1"] }
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_hierarchical_filter_expression_with_bucket_names_and_rbac_missmatch():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_names": ["bucket1", "bucket2"] }
    rbac_by = {"bucket_names": ["bucket3"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" in str(result)

def test_generate_hierarchical_filter_expression_with_bucket_name_and_object_name_and_rbac_missmatch():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {"bucket_names": ["bucket3"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "ismissing(@file_id)" in str(result)

def test_generate_hierarchical_filter_expression_with_bucket_names_and_rbac_match():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_names": ["bucket1", "bucket2"] }
    rbac_by = {"bucket_names": ["bucket1"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_hierarchical_filter_expression_with_bucket_name_and_object_name_and_rbac_match():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=True)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {"bucket_names": ["bucket1"]}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_hierarchical_filter_expression_with_bucket_name_and_object_name_and_rbac_disabled():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=False)
    search_by = {"bucket_name": "bucket1", "object_name": "object1" }
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert result is not None
    assert "bucket1" in str(result)
    assert "object1" in str(result)
    assert "ismissing(@file_id)" in str(result)

def test_generate_hierarchical_filter_expression_empty_and_rbac_disabled():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis", rbac_enabled=False)
    search_by = {}
    rbac_by = {}
    filter_expression = retriever.filter_expression_from_search_by(search_by)
    summary_filter_expression = retriever.vector_store.get_hierarchical_summary_filter_expression()
    rbac_filter_expression = retriever.filter_expression_from_rbac_by(rbac_by)
    result = retriever.generate_hierarchical_retrieve_filter_expression(filter_expression, summary_filter_expression, rbac_filter_expression)
    assert "summary" in str(result)

# ==================

def test_generate_search_by_empty():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = retriever.generate_search_by({})
    assert search_by == {}

def test_generate_search_by_bucket_names():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = retriever.generate_search_by({'search_by': {"bucket_names": ["123"]}})
    assert search_by == {"bucket_names": ["123"]}

def test_generate_search_by_bucket_name_and_object_name():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    search_by = retriever.generate_search_by({'search_by': {"bucket_name": "bucket1", "object_name": "object1"}})
    assert search_by == {"bucket_name": "bucket1", "object_name": "object1"}

# =================

def test_generate_rbac():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    return_bucket_names = { "buckets": ["bucket1", "bucket2"] }
    with mock.patch('comps.retrievers.utils.opea_retriever.retrieve_bucket_list', return_value=return_bucket_names):
        rbac_by = retriever.generate_rbac(None)
        assert rbac_by is not None
        assert rbac_by['bucket_names'] == return_bucket_names['buckets']

def test_generate_rbac_no_access(): 
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    return_bucket_names = { "buckets": [] }
    with mock.patch('comps.retrievers.utils.opea_retriever.retrieve_bucket_list', return_value=return_bucket_names):
        rbac_by = retriever.generate_rbac(None)
        assert rbac_by is not None
        assert rbac_by['bucket_names'] == []

def test_generate_rbac_malformed(): 
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    return_bucket_names = None
    with mock.patch('comps.retrievers.utils.opea_retriever.retrieve_bucket_list', return_value=return_bucket_names):
        rbac_by = retriever.generate_rbac(None)
        assert rbac_by is not None
        assert rbac_by['bucket_names'] == []

def test_generate_rbac_access_error(): 
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    with mock.patch('comps.retrievers.utils.opea_retriever.retrieve_bucket_list', side_effect=ValueError("Authorization header is missing.")):
        rbac_by = retriever.generate_rbac(None)
        assert rbac_by is not None
        assert rbac_by['bucket_names'] == []

# ===================

@pytest.mark.asyncio
async def test_retrieve():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    input = EmbedDoc(text="test", embedding=[1, 2, 3])

    async def return_none():
        return SearchedDoc(retrieved_docs=[], user_prompt="")

    with mock.patch.object(retriever.vector_store, 'search', return_value=return_none()) as mock_retrieve:
        result = await retriever.retrieve(input=input, search_by={}, rbac_by=None)
        mock_retrieve.assert_called_once()
        assert result is not None

# ==================

@pytest.mark.asyncio
async def test_hierarchical_retrieve():
    OPEARetriever._instance = None
    retriever = OPEARetriever(vector_store="redis")
    input = EmbedDoc(text="test", embedding=[1, 2, 3])

    async def return_docs():
        return SearchedDoc(
            retrieved_docs=[
                TextDoc(text="aaa", metadata={
                    "doc_id": "123",
                    "page": 1
                })
            ],
            user_prompt=""
        )

    with mock.patch.object(retriever.vector_store, 'search', side_effect=[return_docs(), return_docs()]) as mock_retrieve:
        result = await retriever.hierarchical_retrieve(input=input, k_summaries=1, k_chunks=1, search_by={}, rbac_by=None)
        mock_retrieve.assert_called()
        assert result is not None
