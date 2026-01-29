# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from unittest.mock import patch

import pytest

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/asr --cov-report=term --cov-report=html tests/unit/asr/test_opea_asr_microservice.py

Alternatively, to run all tests for the 'asr' module, execute the following command:
   pytest --disable-warnings --cov=comps/asr --cov-report=term --cov-report=html tests/unit/asr

Note: These tests focus on module initialization and structure. Testing the FastAPI endpoint 
directly with mocked Form() parameters is complex and better suited for integration tests.
"""


@pytest.fixture
def mock_validate_model_server():
    """Mock the model server validation to prevent actual HTTP calls."""
    with patch('comps.asr.utils.opea_asr.OPEAAsr._validate_model_server', autospec=True) as mock_validate:
        yield mock_validate


@pytest.fixture
def mock_validate_config():
    """Mock the config validation."""
    with patch('comps.asr.utils.opea_asr.OPEAAsr._validate_config', autospec=True) as mock_validate:
        yield mock_validate


@pytest.fixture
def mock_cores_mega_microservice():
    """Mock the mega microservice decorator and port availability check."""
    with patch('comps.cores.mega.micro_service.check_ports_availability', return_value=True), \
         patch('comps.cores.mega.micro_service.MicroService._async_setup', return_value=None):
        yield


@pytest.fixture
def clean_env_vars():
    """Clean up environment variables after tests."""
    yield "clean_env_vars"
    try:
        del os.environ['ASR_MODEL_NAME']
        del os.environ['ASR_MODEL_SERVER']
        del os.environ['ASR_MODEL_SERVER_ENDPOINT']
        del os.environ['ASR_USVC_PORT']
    except Exception:
        pass


@pytest.fixture
def set_valid_env_vars():
    """Set valid environment variables for testing."""
    with patch.dict("os.environ", {
        "ASR_MODEL_NAME": "test_model",
        "ASR_MODEL_SERVER": "vllm",
        "ASR_MODEL_SERVER_ENDPOINT": "http://localhost:8008",
        "ASR_USVC_PORT": "9009",
    }):
        yield


@patch('dotenv.load_dotenv')
def test_microservice_declaration_complies_with_guidelines(
    mock_load_dotenv, 
    mock_validate_model_server, 
    mock_validate_config, 
    mock_cores_mega_microservice,
    set_valid_env_vars
):
    """Test that the microservice module is properly structured and initialized."""
    try:
        import comps.asr.opea_asr_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA ASR Microservice init raised {type(e).__name__} unexpectedly!")

    # Assert that load_dotenv was called with the expected path
    mock_load_dotenv.assert_called()
    called_path = mock_load_dotenv.call_args[0][0]
    expected_suffix = '/impl/microservice/.env'

    assert called_path.endswith(expected_suffix), \
        f"Expected load_dotenv to be called with a path ending in '{expected_suffix}', but got '{called_path}'"

    # Check if required elements are declared
    assert hasattr(test_module, 'USVC_NAME'), "USVC_NAME is not declared"
    assert hasattr(test_module, 'logger'), "logger is not declared"
    assert hasattr(test_module, 'register_microservice'), "register_microservice is not declared"
    assert hasattr(test_module, 'statistics_dict'), "statistics_dict is not declared"
    assert hasattr(test_module, 'process'), "process is not declared"
    assert hasattr(test_module, 'opea_asr'), "opea_asr is not declared"


def test_initialization_succeeds_with_defaults(mock_validate_model_server, mock_cores_mega_microservice, set_valid_env_vars):
    """Test that the microservice initializes successfully with default environment values."""
    try:
        import comps.asr.opea_asr_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA ASR Microservice init raised {type(e).__name__} unexpectedly!")

    # Assert that model_name is a non-empty string
    assert isinstance(test_module.opea_asr._model_name, str) and test_module.opea_asr._model_name, \
        "The model_name is expected to be a non-empty string"

    # Assert that model_server is a non-empty string
    assert isinstance(test_module.opea_asr._model_server, str) and test_module.opea_asr._model_server, \
        "The model_server is expected to be a non-empty string"

    # Assert that model_server_endpoint is a non-empty string
    assert isinstance(test_module.opea_asr._model_server_endpoint, str) and test_module.opea_asr._model_server_endpoint, \
        "The model_server_endpoint is expected to be a non-empty string"


def test_initialization_succeeds_with_env_vars_present(mock_validate_model_server, clean_env_vars):
    """Test that initialization works correctly when environment variables are set."""
    with patch.dict("os.environ", {
        "ASR_MODEL_NAME": "test_asr_model",
        "ASR_MODEL_SERVER": "vllm",
        "ASR_MODEL_SERVER_ENDPOINT": "http://testhost:8000",
        "ASR_USVC_PORT": "9009",
    }):
        try:
            import comps.asr.opea_asr_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA ASR Microservice init raised {type(e)} unexpectedly!")

        # Assertions to check the initialized values
        assert test_module.opea_asr._model_name == "test_asr_model", "Model name does not match"
        assert test_module.opea_asr._model_server == "vllm", "Model server does not match"
        assert "http://testhost:8000" in test_module.opea_asr._model_server_endpoint, \
            "Model server endpoint does not match"


def test_initialization_raises_exception_when_model_name_is_missing(mock_validate_model_server, clean_env_vars):
    """Test that initialization fails with appropriate error messages when model name is missing."""
    # Test scenario with failing validation for model_name
    with patch.dict("os.environ", {
        "ASR_MODEL_NAME": "",
        "ASR_MODEL_SERVER": "vllm",
        "ASR_MODEL_SERVER_ENDPOINT": "http://testhost:8000",
    }):
        with pytest.raises(Exception) as context:
            import comps.asr.opea_asr_microservice as test_module
            importlib.reload(test_module)
        assert str(context.value) == "The 'ASR_MODEL_NAME' cannot be empty."


def test_initialization_raises_exception_when_model_server_is_missing(mock_validate_model_server, clean_env_vars):
    """Test that initialization fails when model server is missing."""
    # Test scenario with failing validation for model_server
    with patch.dict("os.environ", {
        "ASR_MODEL_NAME": "test_model",
        "ASR_MODEL_SERVER": "",
        "ASR_MODEL_SERVER_ENDPOINT": "http://testhost:8000",
    }):
        with pytest.raises(Exception) as context:
            import comps.asr.opea_asr_microservice as test_module
            importlib.reload(test_module)
        assert str(context.value) == "The 'ASR_MODEL_SERVER' cannot be empty."
