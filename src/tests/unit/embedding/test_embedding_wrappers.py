# ruff: noqa: E711, E712
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# test_wrappers.py

import pytest
from unittest import mock
from unittest.mock import MagicMock
from docarray import BaseDoc
from typing import List
from comps.embeddings.utils.wrappers.wrapper_langchain import LangchainEmbedding
from comps.embeddings.utils.wrappers.wrapper_langchain import HuggingFaceEndpointEmbeddings, MosecEmbeddings, OVMSEndpointEmbeddings
from comps.embeddings.utils.wrappers.wrapper_llamaindex import LlamaIndexEmbedding, TextEmbeddingsInference
from comps.embeddings.utils.wrappers.wrapper import EmbeddingWrapper


class MockEmbeddingWrapper(EmbeddingWrapper):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, input_text: str) -> BaseDoc:
        mock_doc = MagicMock(spec=BaseDoc)
        mock_doc.embedding = [0.1, 0.2, 0.3]
        return mock_doc

    def change_configuration(self, **kwargs):
        pass

def test_embed_query_valid_input():
    wrapper = MockEmbeddingWrapper("model", "server", "endpoint")
    result = wrapper.embed_query("test query")
    assert isinstance(result, BaseDoc)
    assert result.embedding == [0.1, 0.2, 0.3]

def test_embed_query_empty_string():
    wrapper = MockEmbeddingWrapper("model", "server", "endpoint")
    result = wrapper.embed_query("")
    assert isinstance(result, BaseDoc)
    assert result.embedding == [0.1, 0.2, 0.3]

def test_EmbeddingWrapper_not_implemented():
    with pytest.raises(TypeError):
        EmbeddingWrapper("model", "server", "endpoint")

def test_langchain_initialization():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        embedding = LangchainEmbedding(model_name, model_server, endpoint)

    assert embedding._model_name == model_name
    assert embedding._model_server == model_server
    assert embedding._endpoint == endpoint
    assert embedding._embedder is not None

    LangchainEmbedding._instance = None

def test_langchain_singleton_behavior():
    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        instance1 = LangchainEmbedding("model1", "mosec", "http://endpoint1")
        instance2 = LangchainEmbedding("model1", "mosec", "http://endpoint1")

        assert instance1 is instance2

    LangchainEmbedding._instance = None

def test_langchain_singleton_behavior_wrong_modelserver():
    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        LangchainEmbedding("model1", "mosec", "http://endpoint1")
        with pytest.raises(Exception) as exc_info:
            LangchainEmbedding("model2", "ovms", "http://endpoint1")
            assert "LangchainEmbedding instance already exists with different model name or model server." in exc_info.value.args[0]

    LangchainEmbedding._instance = None

def test_langchain_select_embedder():
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        embedding = LangchainEmbedding(model_name, "tei", endpoint)
        assert isinstance(embedding._embedder, HuggingFaceEndpointEmbeddings)
        LangchainEmbedding._instance = None

        embedding = LangchainEmbedding(model_name, "mosec", endpoint)
        assert isinstance(embedding._embedder, MosecEmbeddings)
        LangchainEmbedding._instance = None

        embedding = LangchainEmbedding(model_name, "ovms", endpoint)
        assert isinstance(embedding._embedder, OVMSEndpointEmbeddings)
        LangchainEmbedding._instance = None

        with pytest.raises(ValueError):
            LangchainEmbedding(model_name, "invalid_server", endpoint)
        LangchainEmbedding._instance = None

def test_langchain_embed_documents():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self, text: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        embedding = LangchainEmbedding(model_name, model_server, endpoint)

        texts = ["document1", "document2"]
        output = embedding.embed_documents(texts)
        assert output == [[2]]

        LangchainEmbedding._instance = None

def test_langchain_embed_query():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self, text: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        embedding = LangchainEmbedding(model_name, model_server, endpoint)

        query = "query text"
        output = embedding.embed_query(query)
        assert output == [3]

        LangchainEmbedding._instance = None

def test_langchain_change_configuration():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    with (mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_documents', lambda self, text: [[2]]),
      mock.patch.object(HuggingFaceEndpointEmbeddings, 'embed_query', lambda self, text: [3])):
        embedding = LangchainEmbedding(model_name, model_server, endpoint)

        assert embedding._embedder.huggingfacehub_api_token == None
        new_config = {"huggingfacehub_api_token": "value1"}
        embedding.change_configuration(**new_config)
        assert hasattr(embedding._embedder, "huggingfacehub_api_token") == True
        assert embedding._embedder.huggingfacehub_api_token == "value1"

        LangchainEmbedding._instance = None

def test_llama_index_initialization():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    with mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [[2]]):
        embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

    assert embedding._model_name == model_name
    assert embedding._model_server == model_server
    assert embedding._endpoint == endpoint
    assert embedding._embedder is not None

    LlamaIndexEmbedding._instance = None

def test_llama_index_singleton_behavior():
    with mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [[2]]):
        instance1 = LlamaIndexEmbedding("model1", "tei", "http://endpoint1")
        instance2 = LlamaIndexEmbedding("model1", "tei", "http://endpoint1")

        assert instance1 is instance2

    LlamaIndexEmbedding._instance = None

def test_llama_index_singleton_behavior_wrong_modelserver():
    with mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [[2]]):
        LlamaIndexEmbedding("model1", "tei", "http://endpoint1")
        with pytest.raises(Exception) as exc_info:
            LlamaIndexEmbedding("model2", "ovms", "http://endpoint1")
            assert "LlamaIndexEmbedding instance already exists with different model name or model server." in exc_info.value.args[0]

    LlamaIndexEmbedding._instance = None

def test_llama_index_select_embedder():
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(TextEmbeddingsInference, '_get_text_embeddings', lambda self, text: [[2]]),
        mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [3])):
        embedding = LlamaIndexEmbedding(model_name, "tei", endpoint)
        assert isinstance(embedding._embedder, TextEmbeddingsInference)
        LlamaIndexEmbedding._instance = None

def test_llama_index_embed_documents():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(TextEmbeddingsInference, '_get_text_embeddings', lambda self, text: [[2]]),
        mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [3])):
        embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

        texts = ["document1", "document2"]
        output = embedding.embed_documents(texts)
        assert output == [[2]]

        LlamaIndexEmbedding._instance = None

def test_llama_index_embed_query():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"

    with (mock.patch.object(TextEmbeddingsInference, '_get_text_embeddings', lambda self, text: [[2]]),
        mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [3])):
        embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

        query = "query text"
        output = embedding.embed_query(query)
        assert output == [3]

        LlamaIndexEmbedding._instance = None

def test_llama_index_change_configuration():
    model_name = "test_model"
    model_server = "tei"
    endpoint = "http://test-endpoint"
    with (mock.patch.object(TextEmbeddingsInference, '_get_text_embeddings', lambda self, text: [[2]]),
        mock.patch.object(TextEmbeddingsInference, '_get_query_embedding', lambda self, text: [3])):
        embedding = LlamaIndexEmbedding(model_name, model_server, endpoint)

        assert embedding._embedder.auth_token == None
        new_config = {"auth_token": "value1"}
        embedding.change_configuration(**new_config)
        assert hasattr(embedding._embedder, "auth_token") == True
        assert embedding._embedder.auth_token == "value1"

        LlamaIndexEmbedding._instance = None
