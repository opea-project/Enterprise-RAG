# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import patch
import os
from comps.cores.proto.docarray import TextDoc
from comps.text_splitter.utils.opea_textsplitter import OPEATextSplitter


@pytest.fixture
def reset_singleton():
    """Reset the singleton instance before each test."""
    OPEATextSplitter._instance = None
    yield


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "SEMANTIC_CHUNK_PARAMS": "{}",
        "EMBEDDING_MODEL_NAME": "test-model",
        "EMBEDDING_MODEL_SERVER": "test-server",
        "EMBEDDING_MODEL_SERVER_ENDPOINT": "test-endpoint"
    }):
        yield


def test_singleton_instance(reset_singleton):
    """Test that OPEATextSplitter is a singleton."""
    splitter1 = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=False)
    splitter2 = OPEATextSplitter(chunk_size=200, chunk_overlap=20, use_semantic_chunking=True)

    # Should return the same instance with original parameters
    assert splitter1 is splitter2
    assert splitter1.chunk_size == 100
    assert splitter1.chunk_overlap == 10
    assert splitter1.use_semantic_chunking == False # noqa: E712


def test_empty_docs_raises_error(reset_singleton):
    """Test that passing empty documents raises a ValueError."""
    splitter = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=False)

    # Empty list
    with pytest.raises(ValueError, match="No documents passed for data preparation"):
        splitter.split_docs([])

    # List with empty documents
    docs = [TextDoc(text="", metadata={}), TextDoc(text="  ", metadata={})]
    with pytest.raises(ValueError, match="No documents passed for data preparation"):
        splitter.split_docs(docs)


@patch('comps.text_splitter.utils.opea_textsplitter.Splitter')
def test_regular_split_docs(MockSplitter, reset_singleton, mock_env_vars):
    """Test splitting documents with regular Splitter."""
    mock_splitter_instance = MockSplitter.return_value
    mock_splitter_instance.split_text.return_value = ["chunk1", "chunk2"]

    splitter = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=False)

    docs = [
        TextDoc(text="document1", metadata={"source": "source1"}),
        TextDoc(text="document2", metadata={"source": "source2"})
    ]

    result = splitter.split_docs(docs)

    # Check Splitter was initialized correctly
    MockSplitter.assert_called_once_with(chunk_size=100, chunk_overlap=10)

    # Check split was called for each document
    assert mock_splitter_instance.split_text.call_count == 2

    # Check results
    assert len(result) == 4  # 2 docs x 2 chunks each
    assert all(isinstance(doc, TextDoc) for doc in result)

    # Check metadata was preserved
    assert result[0].metadata == {"source": "source1"}
    assert result[1].metadata == {"source": "source1"}
    assert result[2].metadata == {"source": "source2"}
    assert result[3].metadata == {"source": "source2"}


@patch('comps.text_splitter.utils.opea_textsplitter.SemanticSplitter')
def test_semantic_split_docs(MockSemanticSplitter, reset_singleton, mock_env_vars):
    """Test splitting documents with SemanticSplitter."""
    mock_splitter_instance = MockSemanticSplitter.return_value
    mock_splitter_instance.split_text.return_value = ["semantic_chunk1", "semantic_chunk2"]

    splitter = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=True)

    docs = [TextDoc(text="document1", metadata={"source": "source1"})]

    result = splitter.split_docs(docs)

    # Check SemanticSplitter was initialized correctly
    MockSemanticSplitter.assert_called_once()
    
    # Check split was called
    mock_splitter_instance.split_text.assert_called_once_with("document1")

    # Check results
    assert len(result) == 2
    assert result[0].text == "semantic_chunk1"
    assert result[1].text == "semantic_chunk2"
    assert result[0].metadata == {"source": "source1"}


def test_parameter_override(reset_singleton):
    """Test overriding chunk_size and chunk_overlap parameters."""
    with patch('comps.text_splitter.utils.opea_textsplitter.Splitter') as MockSplitter:
        mock_splitter_instance = MockSplitter.return_value
        mock_splitter_instance.split_text.return_value = ["chunk"]

        splitter = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=False)

        docs = [TextDoc(text="document", metadata={})]

        # Override parameters
        splitter.split_docs(docs, chunk_size=200, chunk_overlap=20)

        # Check Splitter was initialized with overridden parameters
        MockSplitter.assert_called_once_with(chunk_size=200, chunk_overlap=20)


@patch('comps.text_splitter.utils.opea_textsplitter.sanitize_env')
def test_semantic_chunk_params_handling(mock_sanitize_env, reset_singleton):
    """Test handling of different semantic_chunk_params values."""
    # Test valid JSON parameters
    mock_sanitize_env.side_effect = ['http://mock-endpoint:1234/v1/embeddings', '{"param1": "value1"}']

    with patch('comps.text_splitter.utils.opea_textsplitter.SemanticSplitter') as MockSemanticSplitter:
        mock_splitter = MockSemanticSplitter.return_value
        mock_splitter.split_text.return_value = ["chunk"]

        splitter = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=True)
        splitter.split_docs([TextDoc(text="document", metadata={})])

        MockSemanticSplitter.assert_called_once_with(
            embedding_service_endpoint='http://mock-endpoint:1234/v1/embeddings',
            semantic_chunk_params_str='{"param1": "value1"}'
        )

    # Reset mock
    mock_sanitize_env.reset_mock()

    # Test empty dict
    mock_sanitize_env.side_effect = ['http://mock-endpoint:1234/v1/embeddings', "{}"]

    with patch('comps.text_splitter.utils.opea_textsplitter.SemanticSplitter') as MockSemanticSplitter:
        OPEATextSplitter._instance = None  # Reset singleton
        mock_splitter = MockSemanticSplitter.return_value
        mock_splitter.split_text.return_value = ["chunk"]

        splitter = OPEATextSplitter(chunk_size=100, chunk_overlap=10, use_semantic_chunking=True)
        splitter.split_docs([TextDoc(text="document", metadata={})])

        MockSemanticSplitter.assert_called_once_with(
            embedding_service_endpoint='http://mock-endpoint:1234/v1/embeddings',
            semantic_chunk_params_str="{}"
        )

    # Reset mock
    mock_sanitize_env.reset_mock()

