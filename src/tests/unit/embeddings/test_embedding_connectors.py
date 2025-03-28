# ruff: noqa: E711, E712
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# test_embedding_connectors.py

from typing import List
from unittest import mock
from unittest.mock import MagicMock
import asyncio

import pytest
from docarray import BaseDoc

from comps.embeddings.utils.connectors.connector import EmbeddingConnector
from comps.embeddings.utils.connectors.connector_langchain import (
    HuggingFaceEndpointEmbeddings,
    LangchainEmbedding,
    MosecEmbeddings,
    OVMSEndpointEmbeddings,
)
from comps.embeddings.utils.connectors.connector_llamaindex import (
    LlamaIndexEmbedding,
    TextEmbeddingsInference,
)

@pytest.fixture(autouse=True)
def mock_asyncio_run():
    with mock.patch("asyncio.run") as mock_run:
        yield mock_run

@pytest.fixture
def teardown():
    yield
    clean_singleton()

def clean_singleton():
    LangchainEmbedding._instance = None

class MockEmbeddingConnector(EmbeddingConnector):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, input_text: str) -> BaseDoc:
        mock_doc = MagicMock(spec=BaseDoc)
        mock_doc.embedding = [0.1, 0.2, 0.3]
        return mock_doc

    def change_configuration(self, **kwargs):
        pass

def test_embed_query_valid_input():
    connector = MockEmbeddingConnector("model", "server", "endpoint")
    result = connector.embed_query("test query")
    assert isinstance(result, BaseDoc)
    assert result.embedding == [0.1, 0.2, 0.3]

def test_embed_query_empty_string():
    connector = MockEmbeddingConnector("model", "server", "endpoint")
    result = connector.embed_query("")
    assert isinstance(result, BaseDoc)
    assert result.embedding == [0.1, 0.2, 0.3]

def test_EmbeddingConnector_not_implemented():
    with pytest.raises(TypeError):
        EmbeddingConnector("model", "server", "endpoint")

@pytest.fixture
def mock_hf_embeddings():
    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self, texts: asyncio.Future()), \
         mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: asyncio.Future()):
        future_docs = asyncio.Future()
        future_docs.set_result([[2]])
        HuggingFaceEndpointEmbeddings.embed_documents = lambda self, texts: future_docs

        future_query = asyncio.Future()
        future_query.set_result([3])
        HuggingFaceEndpointEmbeddings.embed_query = lambda self, text: future_query

        yield

@pytest.fixture
def mock_ti_embeddings():
    with mock.patch.object(TextEmbeddingsInference, '_aget_text_embeddings', lambda self, texts: asyncio.Future()), \
         mock.patch.object(TextEmbeddingsInference, '_aget_query_embedding', lambda self, text: asyncio.Future()):
        future_docs = asyncio.Future()
        future_docs.set_result([[2]])
        TextEmbeddingsInference._aget_text_embeddings = lambda self, texts: future_docs

        future_query = asyncio.Future()
        future_query.set_result([3])
        TextEmbeddingsInference._aget_query_embedding = lambda self, text: future_query

        yield

@pytest.mark.asyncio
async def test_langchain_initialization(teardown, mock_hf_embeddings):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    embedding = LangchainEmbedding(model_name, model_server, endpoint)
    assert embedding._model_name == model_name
    assert embedding._model_server == model_server
    assert embedding._endpoint == endpoint
    assert embedding._embedder is not None

@pytest.mark.asyncio
async def test_langchain_singleton_behavior(teardown):
    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        instance1 = LangchainEmbedding("model1", "mosec", "http://endpoint1")
        instance2 = LangchainEmbedding("model1", "mosec", "http://endpoint1")

        assert instance1 is instance2

@pytest.mark.asyncio
async def test_langchain_singleton_behavior_wrong_modelserver(teardown):
    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        LangchainEmbedding("model1", "mosec", "http://endpoint1")
        with pytest.raises(Exception) as exc_info:
            LangchainEmbedding("model2", "ovms", "http://endpoint1")
            assert "LangchainEmbedding instance already exists with different model name or model server." in exc_info.value.args[0]

@pytest.mark.asyncio
async def test_langchain_select_embedder(teardown):
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        embedding = LangchainEmbedding(model_name, "tei", endpoint)
        assert isinstance(embedding._embedder, HuggingFaceEndpointEmbeddings)
        clean_singleton()

        embedding = LangchainEmbedding(model_name, "mosec", endpoint)
        assert isinstance(embedding._embedder, MosecEmbeddings)
        clean_singleton()

        embedding = LangchainEmbedding(model_name, "ovms", endpoint)
        assert isinstance(embedding._embedder, OVMSEndpointEmbeddings)
        clean_singleton()

        with pytest.raises(ValueError):
            LangchainEmbedding(model_name, "invalid_server", endpoint)
        clean_singleton()

@pytest.mark.asyncio
async def test_langchain_embed_documents(teardown, mock_hf_embeddings):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    embedding = LangchainEmbedding(model_name, model_server, endpoint)

    texts = ["document1", "document2"]
    output = await embedding.embed_documents(texts)
    assert output == [[2]]

@pytest.mark.asyncio
async def test_langchain_embed_query(teardown,mock_hf_embeddings):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    embedding = LangchainEmbedding(model_name, model_server, endpoint)
    query = "query text"
    output = await embedding.embed_query(query)
    assert output == [3]

@pytest.mark.asyncio
async def test_langchain_change_configuration(teardown,mock_hf_embeddings):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    embedding = LangchainEmbedding(model_name, model_server, endpoint)
    assert embedding._embedder.huggingfacehub_api_token == None
    new_config = {"huggingfacehub_api_token": "value1"}
    embedding.change_configuration(**new_config)
    assert hasattr(embedding._embedder, "huggingfacehub_api_token") == True
    assert embedding._embedder.huggingfacehub_api_token == "value1"

@pytest.mark.asyncio
async def test_llama_index_initialization(teardown):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    with mock.patch.object(TextEmbeddingsInference, '_aget_query_embedding', lambda self, text: [[2]]):
        embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

    assert embedding._model_name == model_name
    assert embedding._model_server == model_server
    assert embedding._endpoint == endpoint
    assert embedding._embedder is not None


@pytest.mark.asyncio
async def test_llama_index_singleton_behavior(teardown):
    with mock.patch.object(TextEmbeddingsInference, '_aget_query_embedding', lambda self, text: [[2]]):
        instance1 = LlamaIndexEmbedding("model1", "tei", "http://endpoint1")
        instance2 = LlamaIndexEmbedding("model1", "tei", "http://endpoint1")

        assert instance1 is instance2

@pytest.mark.asyncio
async def test_llama_index_singleton_behavior_wrong_modelserver(teardown):
    with mock.patch.object(TextEmbeddingsInference, '_aget_query_embedding', lambda self, text: [[2]]):
        LlamaIndexEmbedding("model1", "tei", "http://endpoint1")
        with pytest.raises(Exception) as exc_info:
            LlamaIndexEmbedding("model2", "ovms", "http://endpoint1")
            assert "LlamaIndexEmbedding instance already exists with different model name or model server." in exc_info.value.args[0]

@pytest.mark.asyncio
async def test_llama_index_select_embedder(teardown):
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(TextEmbeddingsInference, '_aget_text_embeddings', lambda self, text: [[2]]),
        mock.patch.object(TextEmbeddingsInference, '_aget_query_embedding', lambda self, text: [3])):
        embedding = LlamaIndexEmbedding(model_name, "tei", endpoint)
        assert isinstance(embedding._embedder, TextEmbeddingsInference)

@pytest.mark.asyncio
async def test_llama_index_embed_documents(teardown, mock_ti_embeddings):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

    texts = ["document1", "document2"]
    output = await embedding.embed_documents(texts)
    assert output == [[2]]

@pytest.mark.asyncio
async def test_llama_index_embed_query(teardown,mock_ti_embeddings):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)
    query = "query text"
    output = await embedding.embed_query(query)
    assert output == [3]

@pytest.mark.asyncio
async def test_llama_index_change_configuration(teardown):
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    with (mock.patch.object(TextEmbeddingsInference, '_aget_text_embeddings', lambda self, text: [[2]]),
        mock.patch.object(TextEmbeddingsInference, '_aget_query_embedding', lambda self, text: [3])):
        embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

        assert embedding._embedder.auth_token == None
        new_config = {"auth_token": "value1"}
        embedding.change_configuration(**new_config)
        assert hasattr(embedding._embedder, "auth_token") == True
        assert embedding._embedder.auth_token == "value1"