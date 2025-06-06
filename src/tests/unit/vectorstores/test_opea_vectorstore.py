# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import pytest
from unittest import mock
from unittest.mock import patch
from comps.cores.proto.docarray import DocList,EmbedDoc, SearchedDoc, TextDoc
from comps.vectorstores.utils.opea_vectorstore import OPEAVectorStore

@pytest.fixture
def reset_singleton():
    OPEAVectorStore._instance = None
    yield
    OPEAVectorStore._instance = None

@pytest.fixture
def vectorstore_instance(vector_store_name="redis"):
    OPEAVectorStore._instance = None
    return OPEAVectorStore(vector_store_name=vector_store_name)

@pytest.fixture
def mock_redis_vectorstore():
    with mock.patch('comps.vectorstores.utils.connectors.connector_redis.ConnectorRedis', autospec=True) as MockClass:
        mock_instance = MockClass.return_value
        #mock_instance.add_texts = ['a', 'b', 'c']
        mock_instance.search = SearchedDoc(
            user_prompt='Hello?',
            retrieved_docs=DocList(docs=[
                TextDoc(text='Hello, how are you?'),
                TextDoc(text='Hello, I am fine.')
            ])
        )
        yield MockClass

def test_singleton_behavior(mock_redis_vectorstore):
    instance1 = OPEAVectorStore("redis")
    instance2 = OPEAVectorStore("redis")
    assert instance1 is instance2
    OPEAVectorStore._instance = None

def test_initialize_method(mock_redis_vectorstore):
    stores = OPEAVectorStore("redis")._SUPPORTED_VECTOR_STORES.keys()
    for store in stores:
        vectorstore = OPEAVectorStore(store)
        assert vectorstore._vector_store_name is not None
        assert isinstance(vectorstore.vector_store, mock_redis_vectorstore.return_value.__class__)

# def test_initialize_method_with_unsupported_store(vectorstore_instance, caplog):
#     with caplog.at_level(logging.ERROR):
#             vectorstore_instance._initialize(vector_store_name="unsupported")
#             assert "Unsupported vector store" in caplog.text

@patch('comps.vectorstores.utils.opea_vectorstore.OPEAVectorStore.add_texts')
def test_add_texts_method(mock_add_texts):
    vectorstore = OPEAVectorStore("redis")
    input_texts = [
        EmbedDoc(text='Hello, how are you?', embedding=[0.1, 0.2, 0.3]),
        EmbedDoc(text='Hello, I am fine', embedding=[0.4, 0.5, 0.6]),
    ]
    vectorstore.add_texts(input=input_texts)
    mock_add_texts.assert_called_once_with(input=input_texts)

@patch('comps.vectorstores.utils.opea_vectorstore.OPEAVectorStore.search')
def test_search_method(mock_search):
    vectorstore = OPEAVectorStore("redis")
    search_text = EmbedDoc(text='Hello, how are you?', embedding=[0.1, 0.2, 0.3])
    vectorstore.search(input=search_text)
    mock_search.assert_called_once_with(input=search_text)

def test_search_types(mock_redis_vectorstore):
    types = ['similarity', 'similarity_distance_threshold', 'mmr']
    search_text = EmbedDoc(text='Hello, how are you?', embedding=[0.1, 0.2, 0.3])

    for type in types:
        search_text.search_type = type
        if type == 'similarity_distance_threshold':
            search_text.distance_threshold = 0.5

def test_import_redis_success():
    vectorstore_instance = OPEAVectorStore("redis")
    with mock.patch('comps.vectorstores.utils.connectors.connector_redis.ConnectorRedis', autospec=True) as MockConnectorRedis:
        vectorstore_instance._import_redis()
        assert isinstance(vectorstore_instance.vector_store, MockConnectorRedis.__class__)

def test_import_redis_failure(caplog):
    with mock.patch('comps.vectorstores.utils.connectors.connector_redis', side_effect=ModuleNotFoundError) as MockConnectorRedis:
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ModuleNotFoundError):
                MockConnectorRedis("redis")
                assert "exception when loading ConnectorRedis" in caplog.text
                assert MockConnectorRedis.vector_store is None
