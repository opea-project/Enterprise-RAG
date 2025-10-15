# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from requests.exceptions import ConnectionError, ReadTimeout

from fastapi.responses import StreamingResponse
from comps import LLMParamsDoc, GeneratedDoc
from comps.llms.utils.connectors.langchain_connector import LangchainLLMConnector, VLLMConnector

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms/test_langchain_connector.py

Alternatively, to run all tests for the 'llms' module, execute the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms
"""


@pytest.fixture
def reset_singleton():
    """Reset singleton instance before each test"""
    LangchainLLMConnector._instance = None
    yield
    LangchainLLMConnector._instance = None


@pytest.fixture
def mock_validate():
    """Mock the _validate method to avoid actual validation"""
    with patch('comps.llms.utils.connectors.langchain_connector.LangchainLLMConnector._validate', new_callable=AsyncMock) as mock:
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


# VLLMConnector Tests (Langchain variant)

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

    # Mock VLLMOpenAI
    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.ainvoke = AsyncMock(return_value="This is a test response")

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

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.ainvoke = AsyncMock(return_value="Response")

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

    # Mock streaming response - need to return the generator itself, not wrapped in AsyncMock
    async def mock_stream():
        chunks = ["Hello", " ", "world"]
        for chunk_text in chunks:
            yield chunk_text

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.astream.return_value = mock_stream()

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

    # Mock streaming response - need to return the generator itself, not wrapped in AsyncMock
    async def mock_stream():
        chunks = ["Hello", " ", "world"]
        for chunk_text in chunks:
            yield chunk_text

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.astream.return_value = mock_stream()

        result = await connector.generate(sample_llm_params)

        # Without guard, should return StreamingResponse
        assert isinstance(result, StreamingResponse)





@pytest.mark.asyncio
async def test_vllm_connector_non_streaming_read_timeout(sample_llm_params):
    """Test VLLMConnector handles ReadTimeout in non-streaming"""
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

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.ainvoke = AsyncMock(side_effect=timeout_error)

        with pytest.raises(ReadTimeout) as exc_info:
            await connector.generate(sample_llm_params)

        assert "Failed to invoke the Langchain VLLM Connector" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_connector_non_streaming_connection_error(sample_llm_params):
    """Test VLLMConnector handles ConnectionError in non-streaming"""
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

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.ainvoke = AsyncMock(side_effect=conn_error)

        with pytest.raises(ConnectionError) as exc_info:
            await connector.generate(sample_llm_params)

        assert "Failed to invoke the Langchain VLLM Connector" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_connector_general_exception_in_init(sample_llm_params):
    """Test VLLMConnector handles general exception during initialization"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        MockVLLM.side_effect = Exception("Initialization failed")

        with pytest.raises(Exception) as exc_info:
            await connector.generate(sample_llm_params)

        assert "Failed to invoke the Langchain VLLM Connector" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_connector_no_user_prompt(sample_llm_params):
    """Test VLLMConnector raises error when no user prompt found"""
    sample_llm_params.messages = [{"role": "system", "content": "System message only"}]

    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.ainvoke = AsyncMock(return_value="Response")

        with pytest.raises(ValueError) as exc_info:
            await connector.generate(sample_llm_params)

        assert "No user prompt found in messages" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_connector_non_streaming_general_exception(sample_llm_params):
    """Test VLLMConnector handles general exception in non-streaming"""
    connector = VLLMConnector(
        model_name="test-model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    with patch('comps.llms.utils.connectors.langchain_connector.VLLMOpenAI') as MockVLLM:
        mock_llm = MockVLLM.return_value
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Unknown error"))

        with pytest.raises(Exception) as exc_info:
            await connector.generate(sample_llm_params)

        assert "Error invoking VLLM" in str(exc_info.value)


# LangchainLLMConnector Tests

def test_langchain_connector_singleton(reset_singleton):
    """Test LangchainLLMConnector singleton behavior"""
    # Mock _validate to avoid async run issues
    with patch.object(LangchainLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.langchain_connector.asyncio.run', side_effect=lambda coro: None):
            connector1 = LangchainLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            connector2 = LangchainLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            assert connector1 is connector2


def test_langchain_connector_singleton_different_params(reset_singleton):
    """Test LangchainLLMConnector warns when singleton has different params"""
    # Mock _validate to avoid async run issues
    with patch.object(LangchainLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.langchain_connector.asyncio.run', side_effect=lambda coro: None):
            connector1 = LangchainLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            with patch('comps.llms.utils.connectors.langchain_connector.logger') as mock_logger:
                connector2 = LangchainLLMConnector(
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


def test_langchain_connector_invalid_model_server(reset_singleton):
    """Test LangchainLLMConnector raises error for invalid model server"""
    with pytest.raises(ValueError) as exc_info:
        LangchainLLMConnector(
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
async def test_langchain_connector_generate(reset_singleton, sample_llm_params):
    """Test LangchainLLMConnector generate method delegates to VLLMConnector"""
    # Mock _validate to avoid async run issues
    with patch.object(LangchainLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.langchain_connector.asyncio.run', side_effect=lambda coro: None):
            connector = LangchainLLMConnector(
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


def test_langchain_connector_change_configuration_not_implemented(reset_singleton):
    """Test LangchainLLMConnector change_configuration raises NotImplementedError"""
    # Mock _validate to avoid async run issues
    with patch.object(LangchainLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.langchain_connector.asyncio.run', side_effect=lambda coro: None):
            connector = LangchainLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers={}
            )

            with pytest.raises(NotImplementedError):
                connector.change_configuration(some_param="value")


def test_langchain_connector_with_headers(reset_singleton):
    """Test LangchainLLMConnector initialization with headers"""
    headers = {"Authorization": "Bearer token123"}

    # Mock _validate to avoid async run issues
    with patch.object(LangchainLLMConnector, '_validate', new_callable=AsyncMock):
        with patch('comps.llms.utils.connectors.langchain_connector.asyncio.run', side_effect=lambda coro: None):
            connector = LangchainLLMConnector(
                model_name="test-model",
                model_server="vllm",
                endpoint="http://localhost:8000",
                disable_streaming=False,
                llm_output_guard_exists=True,
                headers=headers
            )

            assert connector._headers == headers
