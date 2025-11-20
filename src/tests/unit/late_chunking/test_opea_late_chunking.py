# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
import requests

from comps import TextDoc
from comps.cores.proto.docarray import EmbedDocList, LateChunkingInput, TextDocList
from comps.late_chunking.utils.opea_late_chunking import OPEALateChunking, _chunked_pooling


"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/late_chunking/utils/opea_late_chunking --cov-report=term --cov-report=html tests/unit/late_chunking/test_opea_late_chunking.py

Alternatively, to run all tests for the 'late_chunking' module, execute the following command:
   pytest --disable-warnings --cov=comps/late_chunking --cov-report=term --cov-report=html tests/unit/late_chunking
"""


@pytest.fixture
def mock_chunker():
    """Create a mock chunker."""
    mock = MagicMock()
    mock.chunk.return_value = (
        ["First chunk text.", "Second chunk text."],
        [(0, 5), (5, 10)]
    )
    return mock


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for embedding service calls."""
    with patch('requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_chunker_class():
    """Mock the Chunker class."""
    with patch('comps.late_chunking.utils.opea_late_chunking.Chunker') as MockChunker:
        yield MockChunker


class TestOPEALateChunkingInitialization:
    """Test OPEALateChunking initialization."""
    
    def test_initialization_with_valid_parameters(self, mock_chunker_class, mock_requests_post):
        """Test successful initialization with valid parameters."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2, 0.3]]}]
        }
        mock_requests_post.return_value = mock_response
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        assert late_chunking.embedding_endpoint == "http://test-endpoint:6000/v1/embeddings"
        assert late_chunking.chunk_size == 512
        assert late_chunking.chunk_overlap == 0
        mock_chunker_class.assert_called_once_with("fixed", "test-model")
    
    def test_initialization_with_invalid_chunk_size(self, mock_chunker_class):
        """Test initialization fails with invalid chunk size."""
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=-1,
                chunk_overlap=0,
                strategy="fixed"
            )
        assert "chunk_size must be a positive integer" in str(exc_info.value)
    
    def test_initialization_with_invalid_chunk_overlap(self, mock_chunker_class):
        """Test initialization fails with invalid chunk overlap."""
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=512,
                chunk_overlap=-1,
                strategy="fixed"
            )
        assert "chunk_overlap must be a non-negative integer" in str(exc_info.value)
    
    def test_initialization_with_overlap_greater_than_chunk_size(self, mock_chunker_class):
        """Test initialization fails when overlap >= chunk_size."""
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=100,
                chunk_overlap=100,
                strategy="fixed"
            )
        assert "chunk_overlap (100) must be less than chunk_size (100)" in str(exc_info.value)
    
    def test_initialization_with_chunker_failure(self, mock_chunker_class):
        """Test initialization fails when Chunker initialization fails."""
        mock_chunker_class.side_effect = Exception("Chunker init failed")
        
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=512,
                chunk_overlap=0,
                strategy="fixed"
            )
        assert "Chunker initialization failed" in str(exc_info.value)


class TestOPEALateChunkingValidation:
    """Test validation functionality."""
    
    def test_validate_success(self, mock_chunker_class, mock_requests_post):
        """Test successful validation."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2, 0.3]]}]
        }
        mock_requests_post.return_value = mock_response
        
        # Should not raise any exception
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        assert late_chunking is not None
    
    def test_validate_embedding_service_error(self, mock_chunker_class, mock_requests_post):
        """Test validation fails when embedding service returns error."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': 'Service error'}
        mock_requests_post.return_value = mock_response
        
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=512,
                chunk_overlap=0,
                strategy="fixed"
            )
        assert "Embedding service validation failed" in str(exc_info.value)
    
    def test_validate_connection_error(self, mock_chunker_class, mock_requests_post):
        """Test validation fails on connection error."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        mock_requests_post.side_effect = requests.RequestException("Connection error")
        
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=512,
                chunk_overlap=0,
                strategy="fixed"
            )
        # The error message wraps the connection error
        assert "Connection error" in str(exc_info.value) or "Cannot connect" in str(exc_info.value)
    
    def test_validate_no_docs_in_response(self, mock_chunker_class, mock_requests_post):
        """Test validation fails when no documents in response."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'docs': []}
        mock_requests_post.return_value = mock_response
        
        with pytest.raises(ValueError) as exc_info:
            OPEALateChunking(
                embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
                model_name="test-model",
                chunk_size=512,
                chunk_overlap=0,
                strategy="fixed"
            )
        assert "no documents found" in str(exc_info.value)


class TestCallEmbeddingUsvc:
    """Test _call_embedding_usvc method."""
    
    def test_call_embedding_usvc_success(self, mock_chunker_class, mock_requests_post):
        """Test successful call to embedding service."""
        # Setup
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        # Mock actual call
        mock_actual_response = MagicMock()
        mock_actual_response.status_code = 200
        mock_actual_response.json.return_value = {
            'docs': [{'text': 'actual text', 'embedding': [[0.3, 0.4]]}]
        }
        
        mock_requests_post.side_effect = [mock_validation_response, mock_actual_response]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        # Test
        test_doc = TextDoc(text="Test document")
        text_doc_list = TextDocList(docs=[test_doc], return_pooling=True)
        result = late_chunking._call_embedding_usvc(text_doc_list)
        
        assert 'docs' in result
        assert result['docs'][0]['text'] == 'actual text'
    
    def test_call_embedding_usvc_timeout(self, mock_chunker_class, mock_requests_post):
        """Test timeout handling."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation success
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        mock_requests_post.side_effect = [mock_validation_response, requests.Timeout("Timeout")]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        test_doc = TextDoc(text="Test document")
        text_doc_list = TextDocList(docs=[test_doc], return_pooling=True)
        result = late_chunking._call_embedding_usvc(text_doc_list)
        
        assert 'error' in result
        assert 'timed out' in result['error']
    
    def test_call_embedding_usvc_request_exception(self, mock_chunker_class, mock_requests_post):
        """Test RequestException handling."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation success
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        mock_requests_post.side_effect = [
            mock_validation_response,
            requests.RequestException("Connection error")
        ]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        test_doc = TextDoc(text="Test document")
        text_doc_list = TextDocList(docs=[test_doc], return_pooling=True)
        result = late_chunking._call_embedding_usvc(text_doc_list)
        
        assert 'error' in result


class TestRun:
    """Test run method (late chunking processing)."""
    
    def test_run_success(self, mock_chunker_class, mock_requests_post):
        """Test successful run with multiple chunks."""
        # Setup chunker mock
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.chunk.return_value = (
            ["First chunk.", "Second chunk."],
            [(0, 3), (3, 6)]
        )
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation response
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        # Mock actual embedding response with 2D token embeddings
        mock_actual_response = MagicMock()
        mock_actual_response.status_code = 200
        # Token embeddings: 6 tokens x 2 dimensions (matching spans (0,3) and (3,6))
        token_embeddings = [
            [0.1, 0.2],  # token 0
            [0.3, 0.4],  # token 1
            [0.5, 0.6],  # token 2
            [0.7, 0.8],  # token 3
            [0.9, 1.0],  # token 4
            [1.1, 1.2],  # token 5
        ]
        mock_actual_response.json.return_value = {
            'docs': [{
                'text': 'First chunk. Second chunk.',
                'embedding': token_embeddings,
                'metadata': {}
            }]
        }
        
        mock_requests_post.side_effect = [mock_validation_response, mock_actual_response]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="sentences"
        )
        
        # Create input
        test_doc = TextDoc(text="First chunk. Second chunk.")
        input_data = LateChunkingInput(docs=[test_doc], chunk_size=512, chunk_overlap=0)
        
        # Test
        result = late_chunking.run(input_data)
        
        assert isinstance(result, EmbedDocList)
        assert len(result.docs) == 2  # Two chunks
        assert result.docs[0].text == "First chunk."
        assert result.docs[1].text == "Second chunk."
        assert len(result.docs[0].embedding) == 2  # 2D embedding
    
    def test_run_1d_embedding_error(self, mock_chunker_class, mock_requests_post):
        """Test error when embedding is 1D instead of 2D."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        # Mock response with 1D embedding (wrong format)
        mock_actual_response = MagicMock()
        mock_actual_response.status_code = 200
        mock_actual_response.json.return_value = {
            'docs': [{
                'text': 'Test text',
                'embedding': [0.1, 0.2, 0.3],  # 1D instead of 2D
                'metadata': {}
            }]
        }
        
        mock_requests_post.side_effect = [mock_validation_response, mock_actual_response]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        test_doc = TextDoc(text="Test text")
        input_data = LateChunkingInput(docs=[test_doc], chunk_size=512, chunk_overlap=0)
        
        # The error is wrapped in an Exception
        with pytest.raises(Exception) as exc_info:
            late_chunking.run(input_data)
        
        assert "Expected 2D token embeddings but got 1D" in str(exc_info.value) or "Error processing" in str(exc_info.value)
    
    def test_run_service_error(self, mock_chunker_class, mock_requests_post):
        """Test handling of embedding service error."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        # Mock service error
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500
        mock_error_response.json.return_value = {'detail': 'Internal server error'}
        mock_error_response.text = 'Internal server error'
        
        mock_requests_post.side_effect = [mock_validation_response, mock_error_response]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        test_doc = TextDoc(text="Test text")
        input_data = LateChunkingInput(docs=[test_doc], chunk_size=512, chunk_overlap=0)
        
        # The error is wrapped in an Exception
        with pytest.raises(Exception) as exc_info:
            late_chunking.run(input_data)
        
        assert "Embedding service failed with status 500" in str(exc_info.value) or "Error processing" in str(exc_info.value)
    
    def test_run_timeout(self, mock_chunker_class, mock_requests_post):
        """Test timeout handling in run method."""
        mock_chunker_instance = MagicMock()
        mock_chunker_class.return_value = mock_chunker_instance
        
        # Mock validation
        mock_validation_response = MagicMock()
        mock_validation_response.status_code = 200
        mock_validation_response.json.return_value = {
            'docs': [{'text': 'test', 'embedding': [[0.1, 0.2]]}]
        }
        
        mock_requests_post.side_effect = [mock_validation_response, requests.Timeout("Timeout")]
        
        late_chunking = OPEALateChunking(
            embedding_endpoint="http://test-endpoint:6000/v1/embeddings",
            model_name="test-model",
            chunk_size=512,
            chunk_overlap=0,
            strategy="fixed"
        )
        
        test_doc = TextDoc(text="Test text")
        input_data = LateChunkingInput(docs=[test_doc], chunk_size=512, chunk_overlap=0)
        
        with pytest.raises(TimeoutError) as exc_info:
            late_chunking.run(input_data)
        
        assert "Request timed out" in str(exc_info.value)


class TestChunkedPooling:
    """Test _chunked_pooling function."""
    
    def test_chunked_pooling_basic(self):
        """Test basic chunked pooling."""
        # Create token embeddings: 6 tokens x 3 dimensions
        embeddings = np.array([
            [1.0, 2.0, 3.0],
            [2.0, 3.0, 4.0],
            [3.0, 4.0, 5.0],
            [4.0, 5.0, 6.0],
            [5.0, 6.0, 7.0],
            [6.0, 7.0, 8.0],
        ])
        
        # Define span annotations: two chunks
        span_annotations = [(0, 3), (3, 6)]
        
        result = _chunked_pooling([embeddings], [span_annotations])
        
        assert len(result) == 1  # One document
        assert len(result[0]) == 2  # Two chunks
        
        # Verify pooling calculation for first chunk
        expected_chunk1 = embeddings[0:3].mean(axis=0)
        np.testing.assert_array_almost_equal(result[0][0], expected_chunk1)
        
        # Verify pooling calculation for second chunk
        expected_chunk2 = embeddings[3:6].mean(axis=0)
        np.testing.assert_array_almost_equal(result[0][1], expected_chunk2)
    
    def test_chunked_pooling_multiple_docs(self):
        """Test chunked pooling with multiple documents."""
        # Two documents
        embeddings1 = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        embeddings2 = np.array([[7.0, 8.0], [9.0, 10.0]])
        
        span_annotations1 = [(0, 2), (2, 3)]
        span_annotations2 = [(0, 2)]
        
        result = _chunked_pooling(
            [embeddings1, embeddings2],
            [span_annotations1, span_annotations2]
        )
        
        assert len(result) == 2  # Two documents
        assert len(result[0]) == 2  # First doc has 2 chunks
        assert len(result[1]) == 1  # Second doc has 1 chunk
    
    def test_chunked_pooling_with_max_length(self):
        """Test chunked pooling with max_length constraint."""
        embeddings = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0],
            [7.0, 8.0],
        ])
        
        # Span goes beyond max_length
        span_annotations = [(0, 2), (2, 4)]
        max_length = 3
        
        result = _chunked_pooling([embeddings], [span_annotations], max_length=max_length)
        
        assert len(result) == 1
        # Second span should be truncated or removed based on max_length
        assert len(result[0]) >= 1
    
    def test_chunked_pooling_1d_error(self):
        """Test error handling for 1D embeddings."""
        embeddings = np.array([1.0, 2.0, 3.0])  # 1D array
        span_annotations = [(0, 2)]
        
        with pytest.raises(ValueError) as exc_info:
            _chunked_pooling([embeddings], [span_annotations])
        
        assert "1-dimensional" in str(exc_info.value)
    
    def test_chunked_pooling_empty_span(self):
        """Test handling of empty spans."""
        embeddings = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        span_annotations = [(0, 0), (1, 3)]  # First span is empty (start == end)
        
        result = _chunked_pooling([embeddings], [span_annotations])
        
        # Empty spans should be skipped
        assert len(result[0]) == 1  # Only the second span

