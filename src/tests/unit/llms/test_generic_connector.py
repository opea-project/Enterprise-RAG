# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from requests.exceptions import ConnectionError, ReadTimeout
import openai
from fastapi.responses import StreamingResponse

from comps import LLMParamsDoc, GeneratedDoc
from comps.llms.utils.connectors.generic_connector import GenericLLMConnector, VLLMConnector

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms/test_generic_connector.py

Alternatively, to run all tests for the 'llms' module, execute the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms
"""


@pytest.fixture
def reset_singleton():
    """Reset singleton instance before each test"""
    GenericLLMConnector._instance = None
    yield
    GenericLLMConnector._instance = None


@pytest.fixture
def mock_validate():
    """Mock the _validate method to avoid actual validation"""
    with patch('comps.llms.utils.connectors.generic_connector.GenericLLMConnector._validate', new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def sample_llm_params():
    """Create sample LLM parameters for testing"""
    return LLMParamsDoc(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        max_new_tokens=100,
        temperature=0.7,
        top_p=0.9,
        stream=False
    )


@pytest.fixture
def sample_llm_params_with_reranked_docs():
    """Create sample LLM parameters with reranked docs"""
    return LLMParamsDoc(
        messages=[
            {"role": "user", "content": "Test query"}
        ],
        max_new_tokens=50,
        stream=False,
        data={
            "reranked_docs": [
                {"text": "doc1", "score": 0.9, "metadata": {"url": "http://example.com/doc1"}},
                {"text": "doc2", "score": 0.8, "metadata": {"url": "http://example.com/doc2"}}
            ]
        }
    )


# VLLMConnector Tests

def test_vllm_connector_initialization():
    """Test VLLMConnector initialization"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True,
        headers={"Authorization": "Bearer token"}
    )

    assert connector._model_name == "test-model"
    assert connector._endpoint == "http://localhost:8000/v1"
    assert connector._disable_streaming is False
    assert connector._llm_output_guard_exists is True
    assert connector._headers == {"Authorization": "Bearer token"}


@pytest.mark.asyncio
async def test_vllm_connector_generate_non_streaming_success(sample_llm_params):
    """Test VLLMConnector generate method in non-streaming mode"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    # Mock the OpenAI client
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a test response"
    mock_choice.dict.return_value = {
        "message": {"content": "This is a test response", "role": "assistant"},
        "finish_reason": "stop",
        "index": 0
    }

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        result = await connector.generate(sample_llm_params)

        assert isinstance(result, GeneratedDoc)
        assert result.text == "This is a test response"
        assert result.prompt == "Hello, how are you?"
        assert result.stream is False


@pytest.mark.asyncio
async def test_vllm_connector_generate_with_reranked_docs(sample_llm_params_with_reranked_docs):
    """Test VLLMConnector generate with reranked documents"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    mock_choice = MagicMock()
    mock_choice.message.content = "Response"
    mock_choice.dict.return_value = {
        "message": {"content": "Response", "role": "assistant"},
        "finish_reason": "stop",
        "index": 0
    }

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        result = await connector.generate(sample_llm_params_with_reranked_docs)

        assert isinstance(result, GeneratedDoc)
        assert "reranked_docs" in result.data


@pytest.mark.asyncio
async def test_vllm_connector_generate_streaming_with_guard(sample_llm_params):
    """Test VLLMConnector streaming mode with output guard"""
    sample_llm_params.stream = True

    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True  # Guard enabled
    )

    # Mock streaming response
    async def mock_stream():
        chunks = ["Hello", " ", "world"]
        for chunk_text in chunks:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = chunk_text
            yield mock_chunk

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_stream()

        result = await connector.generate(sample_llm_params)

        # When guard exists, should return GeneratedDoc with full text
        assert isinstance(result, GeneratedDoc)
        assert result.text == "Hello world"


@pytest.mark.asyncio
async def test_vllm_connector_generate_streaming_without_guard(sample_llm_params):
    """Test VLLMConnector streaming mode without output guard"""
    sample_llm_params.stream = True

    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=False  # Guard disabled
    )

    # Mock streaming response
    async def mock_stream():
        chunks = ["Hello", " ", "world"]
        for chunk_text in chunks:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = chunk_text
            yield mock_chunk

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_stream()

        result = await connector.generate(sample_llm_params)

        # Without guard, should return StreamingResponse
        assert isinstance(result, StreamingResponse)


@pytest.mark.asyncio
async def test_vllm_connector_generate_read_timeout(sample_llm_params):
    """Test VLLMConnector handles ReadTimeout"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    # Create a mock request object with url attribute
    mock_request = MagicMock()
    mock_request.url = "http://localhost:8000"
    timeout_error = ReadTimeout("Timeout occurred")
    timeout_error.request = mock_request

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = timeout_error

        with pytest.raises(ReadTimeout) as exc_info:
            await connector.generate(sample_llm_params)

        assert "Failed to stream from the Generic VLLM Connector" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_connector_generate_connection_error(sample_llm_params):
    """Test VLLMConnector handles ConnectionError"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    # Create a mock request object with url attribute
    mock_request = MagicMock()
    mock_request.url = "http://localhost:8000"
    conn_error = ConnectionError("Connection failed")
    conn_error.request = mock_request

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = conn_error

        with pytest.raises(ConnectionError) as exc_info:
            await connector.generate(sample_llm_params)

        assert "Failed to stream from the Generic VLLM Connector" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_connector_generate_bad_request_error(sample_llm_params):
    """Test VLLMConnector handles BadRequestError"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = openai.BadRequestError("Bad request", response=MagicMock(), body=None)

        with pytest.raises(openai.BadRequestError):
            await connector.generate(sample_llm_params)


@pytest.mark.asyncio
async def test_vllm_connector_generate_no_user_prompt(sample_llm_params):
    """Test VLLMConnector raises error when no user prompt found"""
    sample_llm_params.messages = [{"role": "system", "content": "System message only"}]

    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    mock_response = MagicMock()
    mock_response.choices = []

    with patch.object(connector._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            await connector.generate(sample_llm_params)

        assert "No user prompt found in messages" in str(exc_info.value)


# GenericLLMConnector Tests

def test_generic_connector_singleton(reset_singleton):
    """Test GenericLLMConnector singleton behavior"""
    # Mock _validate to avoid async run issues
    with patch.object(GenericLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.generic_connector.asyncio.run', side_effect=lambda coro: None):
            connector1 = GenericLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            connector2 = GenericLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            assert connector1 is connector2


def test_generic_connector_singleton_different_params(reset_singleton):
    """Test GenericLLMConnector warns when singleton has different params"""
    # Mock _validate to avoid async run issues
    with patch.object(GenericLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.generic_connector.asyncio.run', side_effect=lambda coro: None):
            connector1 = GenericLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            with patch('comps.llms.utils.connectors.generic_connector.logger') as mock_logger:
                connector2 = GenericLLMConnector(
                    model_name="different-model",
                    model_server="vllm",
                    endpoint="http://different:8000",
                    disable_streaming=True,
                    llm_output_guard_exists=False,
                    headers={}
                )

                # Should return same instance and log warning
                assert connector1 is connector2
                mock_logger.warning.assert_called_once()


def test_generic_connector_invalid_model_server(reset_singleton):
    """Test GenericLLMConnector raises error for invalid model server"""
    with pytest.raises(ValueError) as exc_info:
        GenericLLMConnector(
            model_name="test-model",
            model_server="invalid_server",
            endpoint="http://localhost:8000",
            disable_streaming=False,
            llm_output_guard_exists=True,
            headers={}
        )

    assert "Invalid model server" in str(exc_info.value)
    assert "invalid_server" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generic_connector_generate(reset_singleton, sample_llm_params):
    """Test GenericLLMConnector generate method delegates to VLLMConnector"""
    # Mock _validate to avoid async run issues
    with patch.object(GenericLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.generic_connector.asyncio.run', side_effect=lambda coro: None):
            connector = GenericLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            mock_result = GeneratedDoc(text="test response", prompt="test prompt", stream=False)

            with patch.object(connector._connector, 'generate', new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = mock_result

                result = await connector.generate(sample_llm_params)

                assert result == mock_result
                mock_gen.assert_called_once_with(sample_llm_params)


def test_generic_connector_change_configuration_not_implemented(reset_singleton):
    """Test GenericLLMConnector change_configuration raises NotImplementedError"""
    # Mock _validate to avoid async run issues
    with patch.object(GenericLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.generic_connector.asyncio.run', side_effect=lambda coro: None):
            connector = GenericLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            with pytest.raises(NotImplementedError):
                connector.change_configuration(some_param="value")


def test_generic_connector_with_headers(reset_singleton):
    """Test GenericLLMConnector initialization with headers"""
    headers = {"Authorization": "Bearer token123"}

    # Mock _validate to avoid async run issues
    with patch.object(GenericLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.generic_connector.asyncio.run', side_effect=lambda coro: None):
            connector = GenericLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers=headers
            )

            assert connector._headers == headers
