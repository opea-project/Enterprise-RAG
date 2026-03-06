# ruff: noqa: E711, E712
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# test_embedding_connectors.py

from typing import List
from unittest import mock
from unittest.mock import MagicMock

import pytest
from docarray import BaseDoc

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from comps.embeddings.utils.connectors.connector import EmbeddingConnector
from comps.embeddings.utils.connectors.tei_connector import TEIConnector
from comps.embeddings.utils.connectors.torchserve_connector import TorchServeConnector
from comps.embeddings.utils.connectors.mosec_connector import MosecConnector
from comps.embeddings.utils.connectors.ovms_connector import OVMSConnector, OVMSEndpointEmbeddings

@pytest.fixture
def teardown():
    yield
    clean_singleton()

def clean_singleton():
    TEIConnector._instance = None
    TorchServeConnector._instance = None
    MosecConnector._instance = None
    OVMSConnector._instance = None

class MockEmbeddingConnector(EmbeddingConnector):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, input_text: str) -> BaseDoc:
        mock_doc = MagicMock(spec=BaseDoc)
        mock_doc.embedding = [0.1, 0.2, 0.3]
        return mock_doc

def test_embed_query_valid_input():
    connector = MockEmbeddingConnector("model", "endpoint")
    result = connector.embed_query("test query")
    assert isinstance(result, BaseDoc)
    assert result.embedding == [0.1, 0.2, 0.3]

def test_embed_query_empty_string():
    connector = MockEmbeddingConnector("model", "endpoint")
    result = connector.embed_query("")
    assert isinstance(result, BaseDoc)
    assert result.embedding == [0.1, 0.2, 0.3]

def test_EmbeddingConnector_not_implemented():
    with pytest.raises(TypeError):
        EmbeddingConnector("model", "endpoint")

# TODO: Fix the tests below. 
# Currently, they are skipped because the configuration option asyncio_default_fixture_loop_scope is unset
async def test_connector_initialization(teardown):
    model_name = "test_model"
    endpoint = "http://test-endpoint"
    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_query', lambda self, text: [3]):
        embedding = TEIConnector(model_name, endpoint)

    assert embedding._model_name == model_name
    assert embedding._endpoint == endpoint
    assert embedding._embedder is not None


async def test_connector_singleton_behavior(teardown):
    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_query', lambda self, text: [3]):
        instance1 = MosecConnector("model1", "http://endpoint1")
        instance2 = MosecConnector("model1", "http://endpoint1")

        assert instance1 is instance2


async def test_connector_singleton_behavior_wrong_model(teardown):
    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_query', lambda self, text: [3]):
        instance1 = MosecConnector("model1", "http://endpoint1")
        instance2 = MosecConnector("model2", "http://endpoint1")  # different model — reuses existing instance with a warning

        assert instance1 is instance2


async def test_connector_embedder_types(teardown):
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_query', lambda self, text: [3]):
        tei = TEIConnector(model_name, endpoint)
        assert isinstance(tei._embedder, HuggingFaceEndpointEmbeddings)
        clean_singleton()

        mosec = MosecConnector(model_name, endpoint)
        assert isinstance(mosec._embedder, HuggingFaceEndpointEmbeddings)
        clean_singleton()

        ovms = OVMSConnector(model_name, endpoint)
        assert isinstance(ovms._embedder, OVMSEndpointEmbeddings)
        clean_singleton()

async def test_tei_connector_embed_documents(teardown):
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_query', lambda self, text: [3]):
        embedding = TEIConnector(model_name, endpoint)

    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_documents', lambda self, texts: [[2]]):
        texts = ["document1", "document2"]
        output = await embedding.embed_documents(texts)
        assert output == [[2]]


async def test_tei_connector_embed_query(teardown):
    model_name = "test_model"
    endpoint = "http://test-endpoint"

    with mock.patch.object(HuggingFaceEndpointEmbeddings, 'aembed_query', lambda self, text: [3]):
        embedding = TEIConnector(model_name, endpoint)

        query = "query text"
        output = await embedding.embed_query(query)
        assert output == [3]
