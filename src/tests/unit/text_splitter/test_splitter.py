# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest

from unittest.mock import MagicMock, Mock, patch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from comps.text_splitter.utils.splitter import AbstractSplitter, Splitter, SemanticSplitter

def test_abstract_splitter_initialization_raises_error():
    """Test that AbstractSplitter cannot be instantiated directly."""
    with pytest.raises(NotImplementedError):
        AbstractSplitter()

def test_split_text_calls_text_splitter():
    """Test that split_text method calls the text_splitter's split_text method."""
    # Create a mock implementation of AbstractSplitter
    class MockSplitter(AbstractSplitter):
        def get_text_splitter(self):
            mock_splitter = MagicMock()
            mock_splitter.split_text.return_value = ["chunk1", "chunk2"]
            return mock_splitter

    # Test the split_text method
    splitter = MockSplitter()
    result = splitter.split_text("test text")

    # Verify the text_splitter.split_text was called with the correct argument
    splitter.text_splitter.split_text.assert_called_once_with("test text")
    assert result == ["chunk1", "chunk2"]

def test_init_default_params():
    """Test Splitter initialization with default parameters"""
    splitter = Splitter()
    assert splitter.chunk_size == 100
    assert splitter.chunk_overlap == 10
    assert isinstance(splitter.separators, list)
    assert isinstance(splitter.text_splitter, RecursiveCharacterTextSplitter)

def test_init_custom_params():
    """Test Splitter initialization with custom parameters"""
    splitter = Splitter(chunk_size=200, chunk_overlap=20)
    assert splitter.chunk_size == 200
    assert splitter.chunk_overlap == 20

def test_get_separators():
    """Test get_separators returns appropriate list of separators"""
    splitter = Splitter()
    separators = splitter.get_separators()
    assert isinstance(separators, list)
    assert len(separators) > 0
    assert "\n\n" in separators
    assert "\n" in separators
    assert " " in separators

def test_text_splitter():
    """Test split_text method for Splitter"""
    text = "Marry had a little lamb"
    s = Splitter(chunk_size=5, chunk_overlap=3)
    splitted_text = s.split_text(text)

    assert len(splitted_text) == 6
    assert splitted_text == ['Marry', 'had', 'a', 'litt', 'ittle', 'lamb']

def test_split_text():
    """Test split_text method properly delegates to text_splitter"""
    splitter = Splitter()
    test_text = "This is a sample text for testing the splitter functionality."

    # Create a mock for the text_splitter
    mock_chunks = ["This is a sample", "sample text for testing", "testing the splitter functionality."]
    splitter.text_splitter = Mock()
    splitter.text_splitter.split_text.return_value = mock_chunks

    result = splitter.split_text(test_text)

    # Verify the method was called with correct parameters and returns expected result
    splitter.text_splitter.split_text.assert_called_once_with(test_text)
    assert result == mock_chunks

# Custom embedding class to simulate embeddings for semantic chunking
class CustomEmbeddingModel:
    def __init__(self, embedding_dim=384):
        self.embedding_dim = embedding_dim

    def embed_documents(self, documents):
        # Simulate random embeddings for each document (sentence or chunk)
        np.random.seed(42)
        return [np.random.rand(self.embedding_dim).astype(np.float32) for _ in documents]

def test_semantic_splitter():
    """Test split_text method for SemanticSplitter"""
    text = """
    The world is rapidly changing due to advancements in technology. In particular, artificial intelligence (AI) has become a powerful tool that is reshaping industries across the globe.
    AI is being used in fields ranging from healthcare to finance, transportation, and entertainment.
    As AI systems evolve, they are becoming more capable of performing complex tasks that were once thought to require human intelligence.
    """

    mock_response = Mock()
    mock_response.json.return_value = {"embeddings": [[0.1] * 384, [0.1] * 384]}

    # Avoid actual HTTP requests
    with patch('requests.post') as mock_post:
        mock_post.return_value = mock_response

        # Simulate returning mock embeddings for chunks
        def mock_get_text_splitter(self):
            embeddings = CustomEmbeddingModel(embedding_dim=384)

            return SemanticChunker(
                embeddings=embeddings,
                buffer_size=1,
                add_start_index=False,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=None,
                number_of_chunks=None,
                min_chunk_size=None,
            )

        with patch.object(SemanticSplitter, 'get_text_splitter', mock_get_text_splitter):
            semantic_splitter = SemanticSplitter(
                embedding_model_server="mock",
                embedding_model_server_endpoint="http://mock-endpoint",
                embedding_model_name="mock-model"
            )

            chunks = semantic_splitter.split_text(text)

            assert isinstance(chunks, list), f"Expected 'chunks' to be a list, but got {type(chunks)}"
            assert len(chunks) >= 2, f"Expected at least 2 chunks, but got {len(chunks)}"
            assert chunks[0].strip().startswith("The"), f"First chunk doesn't start with 'The'. First chunk: {chunks[0].strip()}"
            assert chunks[-1].strip().endswith("gence."), f"Last chunk doesn't end with 'gence.'. Last chunk: {chunks[-1].strip()}"

def test_initialization_with_invalid_params():
    """Test SemanticSplitter raises ValueError with invalid parameters."""
    with pytest.raises(ValueError, match="embedding_model_server_endpoint must be provided"):
        SemanticSplitter(embedding_model_server_endpoint="")
