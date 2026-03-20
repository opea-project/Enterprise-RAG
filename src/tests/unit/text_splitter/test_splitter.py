# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest

from unittest.mock import MagicMock, Mock, patch
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from comps.text_splitter.utils.splitter import AbstractSplitter, Splitter, SemanticSplitter, TableAwareSplitter

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
    s = Splitter(chunk_size=10, chunk_overlap=3)
    splitted_text = s.split_text(text)

    print(splitted_text)

    assert len(splitted_text) == 3
    assert splitted_text == [
        Document(metadata={'start_index': 0}, page_content='Marry had'),
        Document(metadata={'start_index': 10}, page_content='a little'),
        Document(metadata={'start_index': 19}, page_content='lamb')
        ]

def test_split_text():
    """Test split_text method properly delegates to text_splitter"""
    splitter = Splitter()
    test_text = "This is a sample text for testing the splitter functionality."

    # Create a mock for the text_splitter
    mock_chunks = [Document(metadata={}, page_content='This is a sample text for testing the splitter functionality.')]
    splitter.text_splitter = Mock()
    splitter.text_splitter.split_documents.return_value = mock_chunks

    result = splitter.split_text(test_text)

    # Verify the method was called with correct parameters and returns expected result
    splitter.text_splitter.split_documents.assert_called_once_with(mock_chunks)
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
                embedding_service_endpoint="http://mock-endpoint:1234/v1/embeddings",
            )

            chunks = semantic_splitter.split_text(text)

            assert isinstance(chunks, list), f"Expected 'chunks' to be a list, but got {type(chunks)}"
            assert len(chunks) >= 2, f"Expected at least 2 chunks, but got {len(chunks)}"
            assert chunks[0].strip().startswith("The"), f"First chunk doesn't start with 'The'. First chunk: {chunks[0].strip()}"
            assert chunks[-1].strip().endswith("gence."), f"Last chunk doesn't end with 'gence.'. Last chunk: {chunks[-1].strip()}"

def test_initialization_with_invalid_chunk_params():
    """Test SemanticSplitter raises ValueError with invalid parameters."""
    with pytest.raises(ValueError, match="Invalid semantic_chunk_params format"):
        SemanticSplitter(semantic_chunk_params_str="expected json not string")


# --- TableAwareSplitter tests ---

def test_table_aware_splitter_init():
    """Test TableAwareSplitter initialization with custom parameters."""
    splitter = TableAwareSplitter(chunk_size=500, chunk_overlap=50)
    assert splitter.chunk_size == 500
    assert splitter.chunk_overlap == 50
    assert isinstance(splitter.text_splitter, RecursiveCharacterTextSplitter)


def test_table_aware_splitter_text_only():
    """Test TableAwareSplitter with text that contains no tables."""
    text = "This is some plain text without any tables."
    splitter = TableAwareSplitter(chunk_size=100, chunk_overlap=10)
    chunks = splitter.split_text(text)

    assert len(chunks) == 1
    assert isinstance(chunks[0], Document)
    assert chunks[0].page_content == text
    assert "start_index" in chunks[0].metadata


def test_table_aware_splitter_small_table_kept_whole():
    """Test that a table fitting within chunk_size is kept as a single chunk."""
    table = (
        "| Name | Age |\n"
        "| --- | --- |\n"
        "| Alice | 30 |\n"
        "| Bob | 25 |"
    )
    splitter = TableAwareSplitter(chunk_size=1500, chunk_overlap=100)
    chunks = splitter.split_text(table)

    assert len(chunks) == 1
    assert isinstance(chunks[0], Document)
    assert chunks[0].page_content == table
    assert chunks[0].metadata["start_index"] == 0


def test_table_aware_splitter_large_table_header_propagation():
    """Test that a table exceeding chunk_size is split with header propagated."""
    header = "| Product | Price | Category |"
    separator = "| --- | --- | --- |"
    rows = [f"| Product{i} | {i}.99 | Cat{i} |" for i in range(20)]
    table = "\n".join([header, separator] + rows)

    splitter = TableAwareSplitter(chunk_size=200, chunk_overlap=10)
    chunks = splitter.split_text(table)

    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"

    # Every chunk must start with the header and separator
    for i, chunk in enumerate(chunks):
        lines = chunk.page_content.split('\n')
        assert lines[0] == header, f"Chunk {i} missing header row"
        assert lines[1] == separator, f"Chunk {i} missing separator row"
        assert len(lines) > 2, f"Chunk {i} has no data rows"


def test_table_aware_splitter_mixed_content():
    """Test splitting text with both prose and a table."""
    text = (
        "Introduction paragraph.\n\n"
        "| Col1 | Col2 |\n"
        "| --- | --- |\n"
        "| A | B |\n"
        "| C | D |\n"
        "\nConclusion paragraph."
    )
    splitter = TableAwareSplitter(chunk_size=1500, chunk_overlap=10)
    chunks = splitter.split_text(text)

    contents = [c.page_content for c in chunks]

    # Should have text chunk, table chunk, and text chunk
    assert any("Introduction" in c for c in contents)
    assert any("| Col1 | Col2 |" in c for c in contents)
    assert any("Conclusion" in c for c in contents)


def test_table_aware_splitter_segment_text():
    """Test _segment_text correctly identifies table and text regions."""
    text = (
        "Some text\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| 1 | 2 |\n"
        "More text"
    )
    splitter = TableAwareSplitter(chunk_size=1500, chunk_overlap=10)
    segments = splitter._segment_text(text)

    assert len(segments) == 3
    assert segments[0][0] == 'text'
    assert segments[1][0] == 'table'
    assert segments[2][0] == 'text'


def test_table_aware_splitter_empty_text():
    """Test TableAwareSplitter with empty text delegates to RecursiveCharacterTextSplitter."""
    splitter = TableAwareSplitter(chunk_size=100, chunk_overlap=10)
    chunks = splitter.split_text("")

    assert len(chunks) == 0


def test_table_aware_splitter_returns_documents():
    """Test that split_text returns list of Document objects."""
    text = "Simple text for splitting."
    splitter = TableAwareSplitter(chunk_size=100, chunk_overlap=10)
    chunks = splitter.split_text(text)

    assert isinstance(chunks, list)
    for chunk in chunks:
        assert isinstance(chunk, Document)


def test_table_aware_splitter_start_index():
    """Test that start_index metadata is set correctly for all chunks."""
    text = (
        "Introduction paragraph.\n\n"
        "| Col1 | Col2 |\n"
        "| --- | --- |\n"
        "| A | B |\n"
        "| C | D |\n"
        "\nConclusion paragraph."
    )
    splitter = TableAwareSplitter(chunk_size=1500, chunk_overlap=10)
    chunks = splitter.split_text(text)

    for chunk in chunks:
        assert "start_index" in chunk.metadata, f"Missing start_index in chunk: {chunk.page_content[:50]}"
        idx = chunk.metadata["start_index"]
        assert isinstance(idx, int)
        assert idx >= 0

    # Verify start_index values are monotonically non-decreasing
    indices = [c.metadata["start_index"] for c in chunks]
    assert indices == sorted(indices), f"start_index values not sorted: {indices}"


def test_table_aware_splitter_start_index_split_table():
    """Test that start_index is set correctly when a table is split into multiple chunks."""
    header = "| Product | Price |"
    separator = "| --- | --- |"
    rows = [f"| Product{i} | {i}.99 |" for i in range(20)]
    table = "\n".join([header, separator] + rows)

    splitter = TableAwareSplitter(chunk_size=150, chunk_overlap=10)
    chunks = splitter.split_text(table)

    assert len(chunks) > 1

    for chunk in chunks:
        assert "start_index" in chunk.metadata
        idx = chunk.metadata["start_index"]
        # The start_index should point to a position where the first data row exists
        assert idx >= 0

    # Each chunk's start_index should be unique and increasing
    indices = [c.metadata["start_index"] for c in chunks]
    assert indices == sorted(indices), f"start_index values not sorted: {indices}"
    assert len(set(indices)) == len(indices), f"Duplicate start_index values: {indices}"
