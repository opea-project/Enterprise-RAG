# ruff: noqa: E712
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# test_opea_embedding.py

from unittest import mock

import pytest

from comps.embeddings.utils.opea_embedding import OPEAEmbedding


@pytest.fixture
def mock_langchain():
    with mock.patch('comps.embeddings.utils.wrappers.wrapper_langchain.LangchainEmbedding', autospec=True) as MockClass:
        mock_instance = MockClass.return_value
        mock_instance.embed_documents.return_value = 'works'
        mock_instance.embed_query.return_value = 'works'
        yield MockClass

@pytest.fixture
def mock_llamaindex():
    with mock.patch('comps.embeddings.utils.wrappers.wrapper_llamaindex.LlamaIndexEmbedding', autospec=True) as MockClass:
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
