# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import MagicMock, patch

from comps.late_chunking.utils.chunker import Chunker


"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/late_chunking --cov-report=term --cov-report=html tests/unit/late_chunking/test_chunker.py

Alternatively, to run all tests for the 'late_chunking' module, execute the following command:
   pytest --disable-warnings --cov=comps/late_chunking --cov-report=term --cov-report=html tests/unit/late_chunking
"""


@pytest.fixture
def mock_tokenizer():
    """Create a mock tokenizer that mimics tokenizers.Tokenizer behavior."""
    mock = MagicMock()
    
    # Mock encode method
    mock_encoding = MagicMock()
    mock_encoding.offsets = [(0, 0), (0, 5), (6, 11), (11, 12), (0, 0)]  # Character offsets
    mock.encode.return_value = mock_encoding
    
    # Mock token_to_id method
    def token_to_id_side_effect(token):
        token_map = {
            '.': 1012,
            '[SEP]': 102,
            '[CLS]': 101,
        }
        return token_map.get(token)
    
    mock.token_to_id.side_effect = token_to_id_side_effect
    
    return mock


@pytest.fixture(autouse=True)
def mock_hf_tokenizer(mock_tokenizer):
    """Mock the HuggingFace Tokenizer class for all tests."""
    with patch('tokenizers.Tokenizer') as MockTokenizer:
        # Mock from_pretrained to return our mock tokenizer
        MockTokenizer.from_pretrained.return_value = mock_tokenizer
        # Mock from_file as well for the fallback case
        MockTokenizer.from_file.return_value = mock_tokenizer
        yield MockTokenizer


@pytest.fixture(autouse=True)
def mock_hf_hub():
    """Mock huggingface_hub.hf_hub_download for all tests."""
    with patch('huggingface_hub.hf_hub_download', return_value="/tmp/tokenizer.json"):
        yield


class TestChunkerInitialization:
    """Test Chunker initialization."""
    
    def test_initialization_with_valid_strategy_fixed(self, mock_tokenizer):
        """Test initialization with 'fixed' strategy."""
        with patch('tokenizers.Tokenizer') as MockTokenizer:
            MockTokenizer.from_pretrained.return_value = mock_tokenizer
            chunker = Chunker(strategy="fixed", model_name="test-model")
            assert chunker.chunking_strategy == "fixed"
            assert chunker.tokenizer is not None
    
    def test_initialization_with_valid_strategy_sentences(self, mock_tokenizer):
        """Test initialization with 'sentences' strategy."""
        with patch('tokenizers.Tokenizer') as MockTokenizer:
            MockTokenizer.from_pretrained.return_value = mock_tokenizer
            chunker = Chunker(strategy="sentences", model_name="test-model")
            assert chunker.chunking_strategy == "sentences"
    
    def test_initialization_with_strategy_case_insensitive(self, mock_tokenizer):
        """Test that strategy is case-insensitive."""
        with patch('tokenizers.Tokenizer') as MockTokenizer:
            MockTokenizer.from_pretrained.return_value = mock_tokenizer
            chunker = Chunker(strategy="FIXED  ", model_name="test-model")
            assert chunker.chunking_strategy == "fixed"
    
    def test_initialization_with_invalid_strategy(self):
        """Test initialization with unsupported strategy."""
        with pytest.raises(ValueError) as exc_info:
            Chunker(strategy="invalid_strategy", model_name="test-model")
        assert "Unsupported chunking strategy" in str(exc_info.value)
        assert "invalid_strategy" in str(exc_info.value)
    
    def test_initialization_tokenizer_fallback(self, mock_tokenizer):
        """Test tokenizer loading with fallback mechanism."""
        with patch('tokenizers.Tokenizer.from_pretrained', side_effect=Exception("Primary load failed")):
            with patch('huggingface_hub.hf_hub_download', return_value="/tmp/tokenizer.json"):
                with patch('tokenizers.Tokenizer.from_file', return_value=mock_tokenizer):
                    chunker = Chunker(strategy="fixed", model_name="test-model")
                    assert chunker.tokenizer is not None
    
    def test_initialization_tokenizer_failure(self):
        """Test initialization fails when tokenizer cannot be loaded."""
        with patch('tokenizers.Tokenizer.from_pretrained', side_effect=Exception("Load failed")):
            with patch('huggingface_hub.hf_hub_download', side_effect=Exception("Download failed")):
                with pytest.raises(ValueError) as exc_info:
                    Chunker(strategy="fixed", model_name="invalid-model")
                assert "Invalid model name or unable to load tokenizer" in str(exc_info.value)


class TestChunkByTokens:
    """Test _chunk_by_tokens method."""
    
    def test_chunk_by_tokens_basic(self, mock_tokenizer):
        """Test basic token-based chunking."""
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            # Test with small chunk size
            text = "This is a test sentence."
            chunks, span_annotations = chunker._chunk_by_tokens(text, chunk_size=3, chunk_overlap=0)
            
            assert len(chunks) > 0
            assert len(chunks) == len(span_annotations)
            # Verify span annotations are tuples of (start, end)
            for span in span_annotations:
                assert len(span) == 2
                assert span[0] < span[1]  # start < end
    
    def test_chunk_by_tokens_with_overlap(self, mock_tokenizer):
        """Test token-based chunking with overlap."""
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            text = "This is a test sentence."
            chunks_no_overlap, _ = chunker._chunk_by_tokens(text, chunk_size=3, chunk_overlap=0)
            chunks_with_overlap, _ = chunker._chunk_by_tokens(text, chunk_size=3, chunk_overlap=1)
            
            # With overlap, we should get more chunks
            assert len(chunks_with_overlap) >= len(chunks_no_overlap)
    
    def test_chunk_by_tokens_single_chunk(self, mock_tokenizer):
        """Test when text fits in a single chunk."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 5), (6, 10), (10, 11)]  # Character offsets for each token
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            text = "Short text."
            chunks, span_annotations = chunker._chunk_by_tokens(text, chunk_size=10, chunk_overlap=0)
            
            assert len(chunks) == 1
            assert len(span_annotations) == 1
            assert span_annotations[0] == (0, 3)
            assert chunks[0] == "Short text."


class TestChunkBySentences:
    """Test _chunk_by_sentences method."""
    
    def test_chunk_by_sentences_single_sentence(self, mock_tokenizer):
        """Test chunking with a single sentence."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 0), (0, 5), (6, 11), (11, 12), (0, 0)]
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="sentences", model_name="test-model")
            
            text = "Hello world."
            chunks, span_annotations = chunker._chunk_by_sentences(text, chunk_size=512, overlap=0)
            
            assert len(chunks) >= 1
            assert len(chunks) == len(span_annotations)
    
    def test_chunk_by_sentences_multiple_sentences(self, mock_tokenizer):
        """Test chunking with multiple sentences."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 0), (0, 5), (6, 10), (10, 11), (12, 17), (18, 22), (22, 23), (0, 0)]
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="sentences", model_name="test-model")
            
            text = "First sentence. Second sentence."
            chunks, span_annotations = chunker._chunk_by_sentences(text, chunk_size=512, overlap=0)
            
            # Should have at least one chunk
            assert len(chunks) >= 1
            assert len(chunks) == len(span_annotations)
    
    def test_chunk_by_sentences_no_punctuation(self, mock_tokenizer):
        """Test chunking when no sentence boundaries are found."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 0), (0, 5), (6, 10), (11, 15), (0, 0)]
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="sentences", model_name="test-model")
            
            text = "No punctuation here"
            chunks, span_annotations = chunker._chunk_by_sentences(text, chunk_size=512, overlap=0)
            
            # When there's no punctuation, entire text is returned as one chunk
            assert len(chunks) == 1
            assert len(span_annotations) == 1
            assert chunks[0] == text
    
    def test_chunk_by_sentences_with_overlap(self, mock_tokenizer):
        """Test sentence-based chunking with overlap."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 0)] + [(i, i+1) for i in range(23)] + [(0, 0)]
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="sentences", model_name="test-model")
            
            text = "Short sentence one. Short sentence two."
            chunks, span_annotations = chunker._chunk_by_sentences(text, chunk_size=8, overlap=2)
            
            # With small chunk size and overlap, should create multiple chunks
            assert len(chunks) >= 1
            assert len(chunks) == len(span_annotations)
    
    def test_chunk_by_sentences_tokenization_error(self, mock_tokenizer):
        """Test error handling when tokenization fails."""
        mock_tokenizer.encode.side_effect = Exception("Tokenization failed")
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="sentences", model_name="test-model")
            
            with pytest.raises(ValueError) as exc_info:
                chunker._chunk_by_sentences("Some text", chunk_size=512, overlap=0)
            
            assert "Tokenization failed" in str(exc_info.value)


class TestChunkMethod:
    """Test the main chunk method."""
    
    def test_chunk_with_fixed_strategy(self, mock_tokenizer):
        """Test chunk method with 'fixed' strategy."""
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            text = "This is a test."
            chunks, span_annotations = chunker.chunk(text, chunk_size=5, chunk_overlap=0)
            
            assert len(chunks) > 0
            assert len(chunks) == len(span_annotations)
    
    def test_chunk_with_sentences_strategy(self, mock_tokenizer):
        """Test chunk method with 'sentences' strategy."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 0), (0, 5), (6, 10), (10, 11), (0, 0)]
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="sentences", model_name="test-model")
            
            text = "Test sentence."
            chunks, span_annotations = chunker.chunk(text, chunk_size=512, chunk_overlap=0)
            
            assert len(chunks) > 0
            assert len(chunks) == len(span_annotations)
    
    def test_chunk_override_strategy(self, mock_tokenizer):
        """Test overriding the default chunking strategy."""
        mock_encoding = MagicMock()
        mock_encoding.offsets = [(0, 0), (0, 5), (6, 10), (10, 11), (0, 0)]
        mock_tokenizer.encode.return_value = mock_encoding
        
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            # Initialize with 'fixed' but use 'sentences'
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            text = "Test sentence."
            chunks, span_annotations = chunker.chunk(
                text, 
                chunking_strategy="sentences", 
                chunk_size=512, 
                chunk_overlap=0
            )
            
            assert len(chunks) > 0
    
    def test_chunk_invalid_chunk_size(self, mock_tokenizer):
        """Test chunk method with invalid chunk size for fixed strategy."""
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            with pytest.raises(ValueError) as exc_info:
                chunker.chunk("Some text", chunk_size=2, chunk_overlap=0)
            
            assert "Chunk size must be >= 4" in str(exc_info.value)
    
    def test_chunk_unsupported_strategy_at_runtime(self, mock_tokenizer):
        """Test chunk method with unsupported strategy at runtime."""
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            with pytest.raises(ValueError) as exc_info:
                chunker.chunk("Some text", chunking_strategy="unsupported", chunk_size=10, chunk_overlap=0)
            
            assert "Unsupported chunking strategy" in str(exc_info.value)
    
    def test_chunk_with_default_parameters(self, mock_tokenizer):
        """Test chunk method with default parameters."""
        with patch('tokenizers.Tokenizer.from_pretrained', return_value=mock_tokenizer):
            chunker = Chunker(strategy="fixed", model_name="test-model")
            
            text = "This is a test."
            # Use defaults from method signature (512, 0)
            chunks, span_annotations = chunker.chunk(text, chunk_size=512, chunk_overlap=0)
            
            assert len(chunks) > 0
            assert len(chunks) == len(span_annotations)
