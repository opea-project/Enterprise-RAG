# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.responses import StreamingResponse

from comps.cores.proto.docarray import TextDocList, TextDoc, GeneratedDoc
from comps.docsum.utils.opea_docsum import OPEADocsum

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/docsum --cov-report=term --cov-report=html tests/unit/docsum/test_utils_opea_docsum.py

Alternatively, to run all tests for the 'docsum' module, execute the following command:
   pytest --disable-warnings --cov=comps/docsum --cov-report=term --cov-report=html tests/unit/docsum
"""


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for validation tests."""
    with patch('comps.docsum.utils.opea_docsum.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_chat_openai():
    """Mock ChatOpenAI for testing run method."""
    with patch('comps.docsum.utils.opea_docsum.ChatOpenAI') as MockChatOpenAI:
        yield MockChatOpenAI


@pytest.fixture
def mock_load_summarize_chain():
    """Mock load_summarize_chain for testing run method."""
    with patch('comps.docsum.utils.opea_docsum.load_summarize_chain') as mock_chain:
        yield mock_chain


def test_initialization_succeeds_with_valid_params(mock_requests_post):
    """Test that OPEADocsum initializes successfully with valid parameters."""
    default_summary_type = "map_reduce"
    llm_usvc_endpoint = "http://localhost:9000/v1"

    instance = OPEADocsum(
        default_summary_type=default_summary_type,
        llm_usvc_endpoint=llm_usvc_endpoint
    )

    assert isinstance(instance, OPEADocsum), "Instance was not created successfully."
    assert instance.default_summary_type == default_summary_type
    assert instance.llm_usvc_endpoint == llm_usvc_endpoint

    # Verify that validation was called
    mock_requests_post.assert_called_once()


def test_initialization_fails_with_invalid_summary_type(mock_requests_post):
    """Test that initialization fails with unsupported summary type."""
    with pytest.raises(ValueError) as exc_info:
        OPEADocsum(
            default_summary_type="invalid_type",
            llm_usvc_endpoint="http://localhost:9000/v1"
        )

    assert "Unsupported default_summary_type: invalid_type" in str(exc_info.value)


def test_initialization_fails_with_empty_endpoint(mock_requests_post):
    """Test that initialization fails with empty LLM endpoint."""
    with pytest.raises(ValueError) as exc_info:
        OPEADocsum(
            default_summary_type="map_reduce",
            llm_usvc_endpoint=""
        )

    assert "LLM microservice endpoint must be provided and non-empty" in str(exc_info.value)


def test_validate_succeeds_with_working_endpoint():
    """Test that validation succeeds when LLM endpoint responds correctly."""
    with patch('comps.docsum.utils.opea_docsum.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        OPEADocsum(
            default_summary_type="refine",
            llm_usvc_endpoint="http://localhost:9000/v1"
        )

        # Verify the request was made with correct parameters
        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:9000/v1/chat/completions"
        assert "messages" in call_args[1]["json"]


def test_validate_fails_with_unreachable_endpoint():
    """Test that validation fails when LLM endpoint is unreachable."""
    with patch('comps.docsum.utils.opea_docsum.requests.post') as mock_post:
        import requests
        mock_post.side_effect = requests.RequestException("Connection error")

        with pytest.raises(ConnectionError) as exc_info:
            OPEADocsum(
                default_summary_type="stuff",
                llm_usvc_endpoint="http://unreachable:9000/v1"
            )

        assert "Failed to connect to LLM microservice" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_with_default_summary_type(mock_requests_post, mock_chat_openai, mock_load_summarize_chain):
    """Test run method with default summary type (non-streaming)."""
    # Setup
    instance = OPEADocsum(
        default_summary_type="map_reduce",
        llm_usvc_endpoint="http://localhost:9000/v1"
    )

    # Mock the chain
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value={
        "output_text": "This is a summary",
        "intermediate_steps": ["step1", "step2"]
    })
    mock_load_summarize_chain.return_value = mock_chain

    # Create input
    input_docs = TextDocList(
        docs=[
            TextDoc(text="Document 1 content"),
            TextDoc(text="Document 2 content")
        ],
        stream=False
    )

    # Execute
    result = await instance.run(input_docs)

    # Verify
    assert isinstance(result, GeneratedDoc)
    assert result.text == "This is a summary"
    mock_load_summarize_chain.assert_called_once()


@pytest.mark.asyncio
async def test_run_with_custom_summary_type(mock_requests_post, mock_chat_openai, mock_load_summarize_chain):
    """Test run method with custom summary type specified in input."""
    # Setup
    instance = OPEADocsum(
        default_summary_type="map_reduce",
        llm_usvc_endpoint="http://localhost:9000/v1"
    )

    # Mock the chain
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value={
        "output_text": "This is a refined summary",
        "intermediate_steps": ["step1"]
    })
    mock_load_summarize_chain.return_value = mock_chain

    # Create input with custom summary_type
    input_docs = TextDocList(
        docs=[TextDoc(text="Document content")],
        summary_type="refine",
        stream=False
    )

    # Execute
    result = await instance.run(input_docs)

    # Verify
    assert isinstance(result, GeneratedDoc)
    mock_load_summarize_chain.assert_called_once()
    call_kwargs = mock_load_summarize_chain.call_args[1]
    assert call_kwargs["chain_type"] == "refine"


@pytest.mark.asyncio
async def test_run_with_streaming_enabled(mock_requests_post, mock_chat_openai, mock_load_summarize_chain):
    """Test run method with streaming response enabled."""
    # Setup
    instance = OPEADocsum(
        default_summary_type="stuff",
        llm_usvc_endpoint="http://localhost:9000/v1"
    )

    # Mock the chain with streaming support
    mock_chain = MagicMock()

    async def mock_astream_log(docs):
        # Simulate streaming chunks
        yield MagicMock(ops=[{"op": "add", "path": "/chunk1"}])
        yield MagicMock(ops=[{"op": "add", "path": "/chunk2"}])

    mock_chain.astream_log = mock_astream_log
    mock_load_summarize_chain.return_value = mock_chain

    # Create input with streaming enabled
    input_docs = TextDocList(
        docs=[TextDoc(text="Document content")],
        stream=True
    )

    # Execute
    result = await instance.run(input_docs)

    # Verify
    assert isinstance(result, StreamingResponse)
    assert result.media_type == "text/event-stream"


@pytest.mark.asyncio
async def test_run_with_invalid_summary_type_in_input(mock_requests_post, mock_chat_openai):
    """Test that run method raises error for invalid summary type in input."""
    # Setup
    instance = OPEADocsum(
        default_summary_type="map_reduce",
        llm_usvc_endpoint="http://localhost:9000/v1"
    )

    # Create input with invalid summary_type
    input_docs = TextDocList(
        docs=[TextDoc(text="Document content")],
        summary_type="invalid_type"
    )

    # Execute and verify
    with pytest.raises(ValueError) as exc_info:
        await instance.run(input_docs)

    assert "Unsupported summary_type: invalid_type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_with_stuff_chain_type(mock_requests_post, mock_chat_openai, mock_load_summarize_chain):
    """Test run method with 'stuff' chain type."""
    # Setup
    instance = OPEADocsum(
        default_summary_type="stuff",
        llm_usvc_endpoint="http://localhost:9000/v1"
    )

    # Mock the chain - 'stuff' chain type doesn't return intermediate_steps
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value={
        "output_text": "Stuff summary"
    })
    mock_load_summarize_chain.return_value = mock_chain

    # Create input
    input_docs = TextDocList(
        docs=[TextDoc(text="Short document")],
        stream=False
    )

    # Execute
    result = await instance.run(input_docs)

    # Verify
    assert isinstance(result, GeneratedDoc)
    assert result.text == "Stuff summary"
    call_kwargs = mock_load_summarize_chain.call_args[1]
    assert call_kwargs["chain_type"] == "stuff"
    assert "prompt" in call_kwargs
