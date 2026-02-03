# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import importlib
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from requests.exceptions import ConnectionError, RequestException

from comps import TextDocList, GeneratedDoc

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/docsum --cov-report=term --cov-report=html tests/unit/docsum/test_opea_docsum_microservice.py

Alternatively, to run all tests for the 'docsum' module, execute the following command:
   pytest --disable-warnings --cov=comps/docsum --cov-report=term --cov-report=html tests/unit/docsum
"""


@pytest.fixture()
def clean_env_vars():
    """Clean up environment variables after tests."""
    yield "clean_env_vars"
    # Clean up environment variables after tests.
    try:
        del os.environ['DOCSUM_DEFAULT_SUMMARY_TYPE']
        del os.environ['DOCSUM_LLM_USVC_ENDPOINT']
        del os.environ['DOCSUM_USVC_PORT']
    except Exception:
        pass


@patch('dotenv.load_dotenv')
def test_microservice_declaration_complies_with_guidelines(mock_load_dotenv):
    """Test that the microservice declaration follows OPEA guidelines."""
    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

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


def test_initialization_succeeds_with_defaults():
    """Test that initialization succeeds with default configuration from .env file."""
    # The configuration in the dotenv file shall satisfy all parameters specified as required
    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Assert that default_summary_type is a non-empty string
    assert isinstance(test_module.opea_docsum.default_summary_type, str) and test_module.opea_docsum.default_summary_type, \
        "The default_summary_type is expected to be a non-empty string"

    # Assert that llm_usvc_endpoint is a non-empty string
    assert isinstance(test_module.opea_docsum.llm_usvc_endpoint, str) and test_module.opea_docsum.llm_usvc_endpoint, \
        "The llm_usvc_endpoint is expected to be a non-empty string"


def test_initialization_succeeds_with_env_vars_present(clean_env_vars):
    """Test that initialization succeeds with environment variables set."""
    with patch.dict("os.environ",
        {
            "DOCSUM_DEFAULT_SUMMARY_TYPE": "refine",
            "DOCSUM_LLM_USVC_ENDPOINT": "http://testhost:1234/v1",
            "DOCSUM_USVC_PORT": "9001",
        },
    ):
        try:
            # Import the module here to ensure environment variables are set before use
            import comps.docsum.opea_docsum_microservice as test_module
            importlib.reload(test_module)
        except Exception as e:
            pytest.fail(f"OPEA Docsum Microservice init raised {type(e)} unexpectedly!")

        # Assertions to check the initialized values
        assert test_module.opea_docsum.default_summary_type == "refine", "default_summary_type does not match"
        assert test_module.opea_docsum.llm_usvc_endpoint == "http://testhost:1234/v1", "llm_usvc_endpoint does not match"


def test_initialization_raises_exception_when_config_params_are_missing(clean_env_vars):
    """Test that initialization raises appropriate exceptions when required config params are missing."""
    # Test scenario with failing validation for default_summary_type (empty)
    with patch.dict("os.environ", {"DOCSUM_DEFAULT_SUMMARY_TYPE": ""}):
        with pytest.raises(Exception) as context:
            import comps.docsum.opea_docsum_microservice as test_module
            importlib.reload(test_module)
        # The OPEADocsum class raises ValueError, but could be wrapped
        assert "default_summary_type" in str(context.value).lower() or "cannot be empty" in str(context.value).lower()

    # Test scenario with failing validation for llm_usvc_endpoint (empty)
    with patch.dict("os.environ", {"DOCSUM_LLM_USVC_ENDPOINT": ""}):
        with pytest.raises(Exception) as context:
            import comps.docsum.opea_docsum_microservice as test_module
            importlib.reload(test_module)
        assert "endpoint" in str(context.value).lower() or "cannot be empty" in str(context.value).lower()


def test_initialization_raises_exception_for_invalid_summary_type(clean_env_vars):
    """Test that initialization raises exception for unsupported summary type."""
    with patch.dict("os.environ", {"DOCSUM_DEFAULT_SUMMARY_TYPE": "invalid_type"}):
        with pytest.raises(Exception) as context:
            import comps.docsum.opea_docsum_microservice as test_module
            importlib.reload(test_module)
        assert "Unsupported" in str(context.value) or "invalid" in str(context.value)


@patch('comps.docsum.opea_docsum_microservice.OPEADocsum.run')
def test_microservice_process_succeeds_non_streaming(mock_run):
    """Test that the process function succeeds with non-streaming response."""
    mock_input = MagicMock(spec=TextDocList)
    mock_response = GeneratedDoc(text="Summary text", prompt="")
    mock_run.return_value = mock_response

    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)

        # Manually add the statistics_dict entry after reload
        mock_stat = MagicMock()
        mock_stat.append_latency = MagicMock()
        test_module.statistics_dict[test_module.USVC_NAME] = mock_stat
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function (async)
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(test_module.process(mock_input, None))

    mock_run.assert_called_once_with(mock_input, None)
    assert response == mock_response

    # Check if statistics_dict has an entry for the microservice
    assert test_module.USVC_NAME in test_module.statistics_dict.keys(), \
        f"statistics_dict does not have an entry for the microservice {test_module.USVC_NAME}"


@patch('comps.docsum.opea_docsum_microservice.OPEADocsum.run')
def test_microservice_process_succeeds_streaming(mock_run):
    """Test that the process function succeeds with streaming response."""
    mock_input = MagicMock(spec=TextDocList)
    mock_response = StreamingResponse(iter([b"data: chunk\n\n"]), media_type="text/event-stream")
    mock_run.return_value = mock_response

    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)

        # Manually add the statistics_dict entry after reload
        mock_stat = MagicMock()
        mock_stat.append_latency = MagicMock()
        test_module.statistics_dict[test_module.USVC_NAME] = mock_stat
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function (async)
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(test_module.process(mock_input, None))

    mock_run.assert_called_once_with(mock_input, None)
    assert isinstance(response, StreamingResponse)


@patch('comps.docsum.opea_docsum_microservice.OPEADocsum.run')
def test_microservice_process_handles_value_error(mock_run):
    """Test that the process function handles ValueError correctly."""
    mock_input = MagicMock(spec=TextDocList)
    mock_run.side_effect = ValueError("Invalid summary type")

    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function and assert exception
    loop = asyncio.get_event_loop()
    with pytest.raises(HTTPException) as context:
        loop.run_until_complete(test_module.process(mock_input, None))

    # Assertions
    assert context.value.status_code == 400
    assert "ValueError occurred" in context.value.detail
    assert "Invalid summary type" in context.value.detail
    mock_run.assert_called_once_with(mock_input, None)


@patch('comps.docsum.opea_docsum_microservice.OPEADocsum.run')
def test_microservice_process_handles_connection_error(mock_run):
    """Test that the process function handles ConnectionError correctly."""
    mock_input = MagicMock(spec=TextDocList)
    mock_run.side_effect = ConnectionError("Cannot connect to LLM service")

    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function and assert exception
    loop = asyncio.get_event_loop()
    with pytest.raises(HTTPException) as context:
        loop.run_until_complete(test_module.process(mock_input, None))

    # Assertions
    assert context.value.status_code == 404
    assert "Connection error occurred" in context.value.detail
    assert "Cannot connect to LLM service" in context.value.detail
    mock_run.assert_called_once_with(mock_input, None)


@patch('comps.docsum.opea_docsum_microservice.OPEADocsum.run')
def test_microservice_process_handles_request_exception(mock_run):
    """Test that the process function handles RequestException correctly."""
    mock_input = MagicMock(spec=TextDocList)
    mock_exception = RequestException("Request failed")
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_exception.response = mock_response
    mock_run.side_effect = mock_exception

    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function and assert exception
    loop = asyncio.get_event_loop()
    with pytest.raises(HTTPException) as context:
        loop.run_until_complete(test_module.process(mock_input, None))

    # Assertions
    assert context.value.status_code == 503
    assert "RequestException occurred" in context.value.detail
    mock_run.assert_called_once_with(mock_input, None)


@patch('comps.docsum.opea_docsum_microservice.OPEADocsum.run')
def test_microservice_process_handles_generic_exception(mock_run):
    """Test that the process function handles generic exceptions correctly."""
    mock_input = MagicMock(spec=TextDocList)
    mock_run.side_effect = Exception("Unexpected error")

    try:
        import comps.docsum.opea_docsum_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA Docsum Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function and assert exception
    loop = asyncio.get_event_loop()
    with pytest.raises(HTTPException) as context:
        loop.run_until_complete(test_module.process(mock_input, None))

    # Assertions
    assert context.value.status_code == 500
    assert "An error occurred while processing" in context.value.detail
    assert "Unexpected error" in context.value.detail
    mock_run.assert_called_once_with(mock_input, None)
