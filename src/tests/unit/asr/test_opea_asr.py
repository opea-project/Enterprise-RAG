# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import requests

from comps.asr.utils.opea_asr import OPEAAsr
from comps.cores.proto.api_protocol import AudioTranscriptionResponse
from comps.cores.proto.docarray import Audio2TextDoc

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/asr --cov-report=term --cov-report=html tests/unit/asr/test_opea_asr.py

Alternatively, to run all tests for the 'asr' module, execute the following command:
   pytest --disable-warnings --cov=comps/asr --cov-report=term --cov-report=html tests/unit/asr
"""


@pytest.fixture
def mock_validate_model_server():
    """Mock the model server validation to prevent actual HTTP calls during initialization."""
    with patch.object(OPEAAsr, '_validate_model_server', autospec=True) as mock_validate:
        yield mock_validate


def test_initialization_succeeds_with_valid_params(mock_validate_model_server):
    """Test that OPEAAsr initializes successfully with valid parameters."""
    model_name = "test_model"
    model_server = "vllm"
    endpoint = "http://test-endpoint:8000"
    
    asr = OPEAAsr(
        model_name=model_name,
        model_server=model_server,
        model_server_endpoint=endpoint
    )
    
    assert asr._model_name == model_name
    assert asr._model_server == model_server
    assert asr._model_server_endpoint == "http://test-endpoint:8000/v1"
    mock_validate_model_server.assert_called_once()


def test_initialization_adds_v1_suffix_to_endpoint(mock_validate_model_server):
    """Test that the /v1 suffix is added to endpoint if not present."""
    endpoint_without_v1 = "http://test-endpoint:8000"
    
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint=endpoint_without_v1
    )
    
    assert asr._model_server_endpoint == "http://test-endpoint:8000/v1"


def test_initialization_preserves_v1_suffix(mock_validate_model_server):
    """Test that existing /v1 suffix is preserved."""
    endpoint_with_v1 = "http://test-endpoint:8000/v1"
    
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint=endpoint_with_v1
    )
    
    assert asr._model_server_endpoint == "http://test-endpoint:8000/v1"


def test_initialization_raises_exception_when_model_name_empty(mock_validate_model_server):
    """Test that initialization raises ValueError when model name is empty."""
    with pytest.raises(ValueError) as exc_info:
        OPEAAsr(
            model_name="",
            model_server="vllm",
            model_server_endpoint="http://test-endpoint:8000"
        )
    assert "The 'ASR_MODEL_NAME' cannot be empty." in str(exc_info.value)


def test_initialization_raises_exception_when_model_server_empty(mock_validate_model_server):
    """Test that initialization raises ValueError when model server is empty."""
    with pytest.raises(ValueError) as exc_info:
        OPEAAsr(
            model_name="test_model",
            model_server="",
            model_server_endpoint="http://test-endpoint:8000"
        )
    assert "The 'ASR_MODEL_SERVER' cannot be empty." in str(exc_info.value)


def test_initialization_raises_exception_for_unsupported_model_server(mock_validate_model_server):
    """Test that initialization raises ValueError for unsupported model server."""
    with pytest.raises(ValueError) as exc_info:
        OPEAAsr(
            model_name="test_model",
            model_server="unsupported_server",
            model_server_endpoint="http://test-endpoint:8000"
        )
    assert "Unsupported ASR model server 'unsupported_server'" in str(exc_info.value)
    assert "only 'vllm' is supported" in str(exc_info.value)


def test_make_silence_wav_bytes(mock_validate_model_server):
    """Test that _make_silence_wav_bytes generates valid WAV data."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    wav_bytes = asr._make_silence_wav_bytes(duration_sec=0.5, sample_rate=16000)
    
    # Check that we get bytes
    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 0
    
    # Verify WAV file structure by checking header
    assert wav_bytes[:4] == b'RIFF'
    assert wav_bytes[8:12] == b'WAVE'


@patch('comps.asr.utils.opea_asr.requests.post')
def test_validate_model_server_succeeds_with_valid_response(mock_post):
    """Test that _validate_model_server succeeds when server responds correctly."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    # Should not raise any exception
    OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    # Verify the request was made
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert "http://test-endpoint:8000/v1/audio/transcriptions" in call_args[0]


@patch('comps.asr.utils.opea_asr.requests.post')
def test_validate_model_server_raises_connection_error_on_failure(mock_post):
    """Test that _validate_model_server raises ConnectionError when server is unreachable."""
    mock_post.side_effect = requests.RequestException("Connection failed")
    
    with pytest.raises(ConnectionError) as exc_info:
        OPEAAsr(
            model_name="test_model",
            model_server="vllm",
            model_server_endpoint="http://test-endpoint:8000"
        )
    
    assert "Failed to connect to ASR microservice" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_succeeds_with_valid_json_response(mock_validate_model_server):
    """Test that run() processes audio and returns transcription with JSON format."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    # Mock the OpenAI client
    mock_transcription = MagicMock()
    mock_transcription.text = "Hello world"
    
    with patch('comps.asr.utils.opea_asr.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
        mock_openai.return_value = mock_client
        
        input_doc = Audio2TextDoc(
            file=b"fake_audio_data",
            model="test_model",
            language="en",
            response_format="json"
        )
        
        result = await asr.run(input_doc)
        
        assert isinstance(result, AudioTranscriptionResponse)
        assert result.text == "Hello world"
        
        # Verify the OpenAI client was called correctly
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "test_model"
        assert call_kwargs["language"] == "en"
        assert call_kwargs["response_format"] == "json"


@pytest.mark.asyncio
async def test_run_succeeds_with_text_response_format(mock_validate_model_server):
    """Test that run() handles text response format correctly."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    # For text format, the response is a string that needs to be JSON parsed
    mock_response_text = '{"text": "Hello world in text format"}'
    
    with patch('comps.asr.utils.opea_asr.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response_text)
        mock_openai.return_value = mock_client
        
        input_doc = Audio2TextDoc(
            file=b"fake_audio_data",
            model="test_model",
            language="en",
            response_format="text"
        )
        
        result = await asr.run(input_doc)
        
        assert isinstance(result, AudioTranscriptionResponse)
        assert result.text == "Hello world in text format"


@pytest.mark.asyncio
async def test_run_raises_error_on_model_name_mismatch(mock_validate_model_server):
    """Test that run() raises ValueError when input model doesn't match configured model."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    input_doc = Audio2TextDoc(
        file=b"fake_audio_data",
        model="different_model",
        language="en",
        response_format="json"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await asr.run(input_doc)
    
    assert "Model name mismatch" in str(exc_info.value)
    assert "different_model" in str(exc_info.value)
    assert "test_model" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_raises_error_on_unsupported_language(mock_validate_model_server):
    """Test that run() raises ValueError for unsupported languages."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    input_doc = Audio2TextDoc(
        file=b"fake_audio_data",
        model="test_model",
        language="unsupported_lang",
        response_format="json"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await asr.run(input_doc)
    
    assert "Unsupported language 'unsupported_lang'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_accepts_supported_languages(mock_validate_model_server):
    """Test that run() accepts validated languages (en, pl)."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    mock_transcription = MagicMock()
    mock_transcription.text = "Cześć świat"
    
    with patch('comps.asr.utils.opea_asr.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
        mock_openai.return_value = mock_client
        
        # Test Polish language
        input_doc = Audio2TextDoc(
            file=b"fake_audio_data",
            model="test_model",
            language="pl",
            response_format="json"
        )
        
        result = await asr.run(input_doc)
        assert result.text == "Cześć świat"
        
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["language"] == "pl"


@pytest.mark.asyncio
async def test_run_defaults_to_english_for_auto_language(mock_validate_model_server):
    """Test that run() defaults to 'en' when language is 'auto' or empty."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    mock_transcription = MagicMock()
    mock_transcription.text = "Test"
    
    with patch('comps.asr.utils.opea_asr.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
        mock_openai.return_value = mock_client
        
        # Test with 'auto'
        input_doc = Audio2TextDoc(
            file=b"fake_audio_data",
            model="test_model",
            language="auto",
            response_format="json"
        )
        
        await asr.run(input_doc)
        
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["language"] == "en"


@pytest.mark.asyncio
async def test_run_raises_error_on_unsupported_response_format(mock_validate_model_server):
    """Test that run() raises ValueError for unsupported response formats."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    input_doc = Audio2TextDoc(
        file=b"fake_audio_data",
        model="test_model",
        language="en",
        response_format="invalid_format"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await asr.run(input_doc)
    
    assert "Unsupported response format 'invalid_format'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_accepts_verbose_json_format(mock_validate_model_server):
    """Test that run() accepts verbose_json as a valid response format."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    mock_transcription = MagicMock()
    mock_transcription.text = "Verbose response"
    
    with patch('comps.asr.utils.opea_asr.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
        mock_openai.return_value = mock_client
        
        input_doc = Audio2TextDoc(
            file=b"fake_audio_data",
            model="test_model",
            language="en",
            response_format="verbose_json"
        )
        
        result = await asr.run(input_doc)
        
        assert result.text == "Verbose response"
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["response_format"] == "verbose_json"


@pytest.mark.asyncio
async def test_run_handles_exception_during_transcription(mock_validate_model_server):
    """Test that run() properly propagates exceptions during transcription."""
    asr = OPEAAsr(
        model_name="test_model",
        model_server="vllm",
        model_server_endpoint="http://test-endpoint:8000"
    )
    
    with patch('comps.asr.utils.opea_asr.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("Transcription failed"))
        mock_openai.return_value = mock_client
        
        input_doc = Audio2TextDoc(
            file=b"fake_audio_data",
            model="test_model",
            language="en",
            response_format="json"
        )
        
        with pytest.raises(Exception) as exc_info:
            await asr.run(input_doc)
        
        assert "Transcription failed" in str(exc_info.value)
