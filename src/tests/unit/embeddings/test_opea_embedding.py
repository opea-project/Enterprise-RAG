# ruff: noqa: E712
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# test_opea_embedding.py

from unittest import mock

import pytest

from comps.embeddings.utils.opea_embedding import OPEAEmbedding


@pytest.fixture
def mock_langchain():
    with mock.patch('comps.embeddings.utils.connectors.connector_langchain.LangchainEmbedding', autospec=True) as MockClass:
        mock_instance = MockClass.return_value
        mock_instance.embed_documents.return_value = 'works'
        mock_instance.embed_query.return_value = 'works'
        yield MockClass

@pytest.fixture
def mock_llamaindex():
    with mock.patch('comps.embeddings.utils.connectors.connector_llamaindex.LlamaIndexEmbedding', autospec=True) as MockClass:
        mock_instance = MockClass.return_value
        mock_instance.embed_documents.return_value = 'works'
        mock_instance.embed_query.return_value = 'works'
        yield MockClass

@pytest.fixture
def teardown():
    yield
    OPEAEmbedding._instance = None

def test_singleton_behavior(mock_langchain, teardown):
    instance1 = OPEAEmbedding("model1", "model_server", "http://test-endpoint", "langchain")
    instance2 = OPEAEmbedding("model1", "model_server", "http://test-endpoint", "langchain")

    assert instance1 is instance2

def test_singleton_behavior_wrong_framework(mock_langchain, teardown):
    OPEAEmbedding("model1", "model_server", "http://test-endpoint", "langchain")
    with pytest.raises(Exception) as exc_info:
        OPEAEmbedding("model2", "model_server", "http://test-endpoint", "llama_index")
        assert "OPEAEmbedding instance already exists with different model name, model server or framework." in exc_info.value.args[0]


def test_initialization(mock_llamaindex, teardown):
    model_name = "test_model"
    model_server = "test_server"
    connector = "llama_index"
    endpoint = "http://test-endpoint"
    embedding = OPEAEmbedding(model_name, model_server, endpoint, connector)

    assert embedding._model_name == model_name
    assert embedding._model_server == model_server
    assert embedding._connector == connector
    assert embedding._endpoint == endpoint

def test_unsupported_framework(teardown):
    with pytest.raises(Exception) as exc_info:
        OPEAEmbedding("test_model", "test_server", "unsupported_framework", "http://test-endpoint")
        assert "Unsupported framework" in exc_info.value.args[0]


def test_import_langchain(mock_langchain, teardown):
    model_name = "test_model"
    model_server = "model_server"
    connector = "langchain"
    endpoint = "http://test-endpoint"
    embedding = OPEAEmbedding(model_name, model_server, endpoint, connector)

    assert hasattr(embedding, "embed_query") == True
    assert hasattr(embedding, "embed_documents") == True
    assert embedding.embed_query is not None
    assert embedding.embed_documents is not None
    mock_langchain.assert_called_with(model_name, model_server, endpoint, None)


def test_import_not_found_langchain(teardown):
    model_name = "test_model"
    model_server = "model_server"
    connector = "langchain"
    endpoint = "http://test-endpoint"

    with pytest.raises(Exception) as exc_info:
        OPEAEmbedding(model_name, model_server, endpoint, connector)
        assert "langchain module not found" in exc_info.value.args[0]


def test_import_llamaindex(mock_llamaindex, teardown):
    model_name = "test_model"
    model_server = "model_server"
    connector = "llama_index"
    endpoint = "http://test-endpoint"
    embedding = OPEAEmbedding(model_name, model_server, endpoint, connector)

    assert hasattr(embedding, "embed_query") == True
    assert hasattr(embedding, "embed_documents") == True
    assert embedding.embed_query is not None
    assert embedding.embed_documents is not None
    mock_llamaindex.assert_called_with(model_name, model_server, endpoint, None)


def test_import_not_found_llamaindex(teardown):
    model_name = "test_model"
    model_server = "model_server"
    connector = "llama_index"
    endpoint = "http://test-endpoint"

    with pytest.raises(Exception) as exc_info:
        OPEAEmbedding(model_name, model_server, endpoint, connector)
        assert "llama_index module not found" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_return_pooling_uses_smaller_batch_size(mock_langchain, teardown):
    """Test that return_pooling=True uses REQUEST_BATCH_SIZE_POOLING instead of REQUEST_BATCH_SIZE."""
    from comps.cores.proto.docarray import TextDoc, TextDocList
    
    model_name = "test_model"
    model_server = "model_server"
    connector = "langchain"
    endpoint = "http://test-endpoint"
    embedding = OPEAEmbedding(model_name, model_server, endpoint, connector)
    
    # Create a mock for embed_documents that returns token embeddings
    # When return_pooling=True, embeddings are 2D (tokens x dimensions)
    # Mock returns embeddings for each input text
    def mock_embed_side_effect(texts, **kwargs):
        return [[0.1, 0.2, 0.3] for _ in texts]
    
    mock_embed_docs = mock.AsyncMock(side_effect=mock_embed_side_effect)
    embedding.embed_documents = mock_embed_docs
    
    # Create input with return_pooling=True
    docs = [TextDoc(text=f"test document {i}") for i in range(5)]
    input_with_pooling = TextDocList(docs=docs, return_pooling=True)
    
    # Verify that REQUEST_BATCH_SIZE_POOLING is smaller than REQUEST_BATCH_SIZE
    assert embedding.REQUEST_BATCH_SIZE_POOLING < embedding.REQUEST_BATCH_SIZE
    assert embedding.REQUEST_BATCH_SIZE_POOLING == 2
    
    # Run the embedding
    result = await embedding.run(input_with_pooling)
    
    # Verify that embed_documents was called with return_pooling=True
    assert mock_embed_docs.call_count > 0
    for call in mock_embed_docs.call_args_list:
        kwargs = call.kwargs
        assert 'return_pooling' in kwargs
        assert kwargs['return_pooling'] == True
        # Verify batch size is smaller (max 2 documents per batch)
        texts = call.args[0] if call.args else kwargs.get('texts', [])
        assert len(texts) <= embedding.REQUEST_BATCH_SIZE_POOLING
    
    # Verify result structure
    assert len(result.docs) == 5
    for doc in result.docs:
        assert doc.embedding is not None


@pytest.mark.asyncio
async def test_return_pooling_false_uses_regular_batch_size(mock_langchain, teardown):
    """Test that return_pooling=False uses REQUEST_BATCH_SIZE."""
    from comps.cores.proto.docarray import TextDoc, TextDocList
    
    model_name = "test_model"
    model_server = "model_server"
    connector = "langchain"
    endpoint = "http://test-endpoint"
    embedding = OPEAEmbedding(model_name, model_server, endpoint, connector)
    
    # Create a mock for embed_documents that returns regular embeddings
    # When return_pooling=False, embeddings are 1D (just dimensions)
    # Mock returns embeddings for each input text
    def mock_embed_side_effect(texts, **kwargs):
        return [[0.1, 0.2, 0.3] for _ in texts]
    
    mock_embed_docs = mock.AsyncMock(side_effect=mock_embed_side_effect)
    embedding.embed_documents = mock_embed_docs
    
    # Create input with return_pooling=False
    docs = [TextDoc(text=f"test document {i}") for i in range(5)]
    input_without_pooling = TextDocList(docs=docs, return_pooling=False)
    
    # Run the embedding
    result = await embedding.run(input_without_pooling)
    
    # Verify that embed_documents was called with return_pooling=False
    assert mock_embed_docs.call_count > 0
    for call in mock_embed_docs.call_args_list:
        kwargs = call.kwargs
        assert 'return_pooling' in kwargs
        assert kwargs['return_pooling'] == False
        # Verify batch size can be larger (up to REQUEST_BATCH_SIZE)
        texts = call.args[0] if call.args else kwargs.get('texts', [])
        assert len(texts) <= embedding.REQUEST_BATCH_SIZE
    
    # Verify result structure
    assert len(result.docs) == 5
    for doc in result.docs:
        assert doc.embedding is not None
