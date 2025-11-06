# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from unittest.mock import MagicMock, patch

import pytest

from comps import TextDoc
from comps.cores.proto.docarray import LateChunkingInput, EmbedDocList
from comps.late_chunking.utils.opea_late_chunking import OPEALateChunking


"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/late_chunking --cov-report=term --cov-report=html tests/unit/late_chunking/test_opea_late_chunking_microservice.py

Alternatively, to run all tests for the 'late_chunking' module, execute the following command:
   pytest --disable-warnings --cov=comps/late_chunking --cov-report=term --cov-report=html tests/unit/late_chunking
"""


@pytest.fixture
def mock_tokenizer():
    """Create a mock tokenizer that mimics tokenizers.Tokenizer behavior."""
    mock = MagicMock()
    
    # Mock encode method
    mock_encoding = MagicMock()
    mock_encoding.ids = [101, 7592, 2088, 1012, 102]
    mock_encoding.offsets = [(0, 0), (0, 5), (6, 11), (11, 12), (0, 0)]
    mock.encode.return_value = mock_encoding
    
    # Mock token_to_id method
    def token_to_id_side_effect(token):
        token_map = {'.': 1012, '[SEP]': 102, '[CLS]': 101}
        return token_map.get(token)
    
    mock.token_to_id.side_effect = token_to_id_side_effect
    
    # Mock decode method
    mock.decode.return_value = "decoded text"
    
    return mock


@pytest.fixture(autouse=True)
def mock_hf_tokenizer(mock_tokenizer):
    """Mock the HuggingFace Tokenizer class for all tests."""
    with patch('tokenizers.Tokenizer') as MockTokenizer:
        MockTokenizer.from_pretrained.return_value = mock_tokenizer
        MockTokenizer.from_file.return_value = mock_tokenizer
        yield MockTokenizer


@pytest.fixture(autouse=True)
def mock_hf_hub():
    """Mock huggingface_hub.hf_hub_download for all tests."""
    with patch('huggingface_hub.hf_hub_download', return_value="/tmp/tokenizer.json"):
        yield


@pytest.fixture(autouse=True)
def mock_requests():
    """Mock requests.post for embedding service calls."""
    with patch('requests.post') as mock_post:
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "docs": [
                {
                    "text": "test",
                    "embedding": [[0.1, 0.2, 0.3]]  # 2D array for late chunking
                }
            ]
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_cores_mega_microservice():
    """Mock the cores mega microservice."""
    with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
        MockClass.return_value = MagicMock()
        yield MockClass


@pytest.fixture
def mock_opea_late_chunking():
    """Mock the OPEALateChunking class."""
    with patch('comps.late_chunking.utils.opea_late_chunking.OPEALateChunking.__init__', autospec=True) as MockClass:
        MockClass.return_value = None
        yield MockClass


@pytest.fixture
def mock_opea_late_chunking_run():
    """Mock the OPEALateChunking.run method."""
    with patch.object(OPEALateChunking, 'run', return_value=EmbedDocList(docs=[])) as mock:
        yield mock


@pytest.fixture()
def clean_env_vars():
    """Clean up environment variables after tests."""
    yield "clean_env_vars"
    # Clean up environment variables after tests.
    env_vars = [
        'EMBEDDING_ENDPOINT',
        'EMBEDDING_MODEL_NAME',
        'CHUNK_SIZE',
        'CHUNK_OVERLAP',
        'LATE_CHUNKING_STRATEGY',
        'LATE_CHUNKING_USVC_PORT',
    ]
    for var in env_vars:
        try:
            del os.environ[var]
        except Exception:
            pass


class TestMicroserviceDeclaration:
    """Test microservice declaration and initialization."""
    
    @patch('dotenv.load_dotenv')
    def test_microservice_declaration_complies_with_guidelines(
        self, mock_load_dotenv, mock_opea_late_chunking, mock_cores_mega_microservice
    ):
        """Test that microservice follows OPEA guidelines."""
        try:
            import comps.late_chunking.opea_late_chunking_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e).__name__} unexpectedly!")

        # Assert that load_dotenv was called once with the expected argument
        mock_load_dotenv.assert_called()
        called_path = mock_load_dotenv.call_args[0][0]  # Get the first argument of the first call
        expected_suffix = '/impl/microservice/.env'

        assert called_path.endswith(expected_suffix), \
            f"Expected load_dotenv to be called with a path ending in '{expected_suffix}', but got '{called_path}'"

        # Check if required elements are declared
        assert hasattr(test_module, 'USVC_NAME'), "USVC_NAME is not declared"
        assert hasattr(test_module, 'logger'), "logger is not declared"
        assert hasattr(test_module, 'register_microservice'), "register_microservice is not declared"
        assert hasattr(test_module, 'statistics_dict'), "statistics_dict is not declared"
        assert hasattr(test_module, 'process'), "process is not declared"


class TestMicroserviceInitialization:
    """Test microservice initialization with various configurations."""
    
    def test_initialization_succeeds_with_defaults(
        self, mock_cores_mega_microservice, mock_opea_late_chunking_run
    ):
        """Test initialization with default configuration from .env file."""
        # The configuration in the dotenv file shall satisfy all parameters specified as required
        try:
            import comps.late_chunking.opea_late_chunking_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e).__name__} unexpectedly!")

        # Assert that opea_late_chunking instance exists
        assert hasattr(test_module, 'opea_late_chunking'), "opea_late_chunking instance not found"
    
    def test_initialization_succeeds_with_env_vars_present(
        self, clean_env_vars, mock_opea_late_chunking_run
    ):
        """Test initialization with environment variables."""
        with patch.dict("os.environ", {
            "EMBEDDING_ENDPOINT": "http://testhost:6000/v1/embeddings",
            "EMBEDDING_MODEL_NAME": "test-model",
            "CHUNK_SIZE": "256",
            "CHUNK_OVERLAP": "10",
            "LATE_CHUNKING_STRATEGY": "sentences",
            "LATE_CHUNKING_USVC_PORT": "8003",
        }):
            try:
                # Import the module here to ensure environment variables are set before use
                import comps.late_chunking.opea_late_chunking_microservice as test_module
                importlib.reload(test_module)
            except Exception as e:
                pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e)} unexpectedly!")

            # Assertions to check the initialized values
            assert test_module.opea_late_chunking is not None, "opea_late_chunking instance not initialized"
    
    def test_initialization_with_custom_chunk_size(
        self, clean_env_vars, mock_opea_late_chunking_run
    ):
        """Test initialization with custom chunk size."""
        with patch.dict("os.environ", {
            "EMBEDDING_ENDPOINT": "http://testhost:6000/v1/embeddings",
            "EMBEDDING_MODEL_NAME": "test-model",
            "CHUNK_SIZE": "1024",
            "CHUNK_OVERLAP": "50",
        }):
            try:
                import comps.late_chunking.opea_late_chunking_microservice as test_module
                importlib.reload(test_module)
            except Exception as e:
                pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e)} unexpectedly!")

            assert test_module.opea_late_chunking is not None


class TestProcessFunction:
    """Test the process function."""
    
    @pytest.mark.asyncio
    async def test_process_succeeds(self, mock_cores_mega_microservice, mock_opea_late_chunking_run):
        """Test successful processing of input."""
        mock_input = LateChunkingInput(
            docs=[TextDoc(text="Test document")],
            chunk_size=512,
            chunk_overlap=0
        )
        mock_response = EmbedDocList(docs=[])
        mock_opea_late_chunking_run.return_value = mock_response

        try:
            import comps.late_chunking.opea_late_chunking_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e).__name__} unexpectedly!")

        # Call the process function
        response = test_module.process(mock_input)
        
        assert response == mock_response
        
        # Check if statistics_dict has an entry for the mock_input
        assert test_module.USVC_NAME in test_module.statistics_dict.keys(), \
            f"statistics_dict does not have an entry for the microservice {test_module.USVC_NAME}"
    
    @pytest.mark.asyncio
    async def test_process_handles_value_error(
        self, mock_cores_mega_microservice, mock_opea_late_chunking_run
    ):
        """Test process handles ValueError correctly."""
        mock_input = LateChunkingInput(
            docs=[TextDoc(text="Test document")],
            chunk_size=512,
            chunk_overlap=0
        )
        
        # Make run raise a ValueError
        mock_opea_late_chunking_run.side_effect = ValueError("Test internal error")

        try:
            import comps.late_chunking.opea_late_chunking_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e).__name__} unexpectedly!")

        # Call the process function and expect HTTPException
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            test_module.process(mock_input)
        
        assert exc_info.value.status_code == 400
        assert "internal error" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_process_handles_general_exception(
        self, mock_cores_mega_microservice, mock_opea_late_chunking_run
    ):
        """Test process handles general exceptions correctly."""
        mock_input = LateChunkingInput(
            docs=[TextDoc(text="Test document")],
            chunk_size=512,
            chunk_overlap=0
        )
        
        # Make run raise a general Exception
        mock_opea_late_chunking_run.side_effect = Exception("Test unknown error")

        try:
            import comps.late_chunking.opea_late_chunking_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA Late Chunking Microservice init raised {type(e).__name__} unexpectedly!")

        # Call the process function and expect HTTPException
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            test_module.process(mock_input)
        
        assert exc_info.value.status_code == 500
        assert "error occurred while processing" in exc_info.value.detail.lower()
