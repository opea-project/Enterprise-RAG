# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import requests

from comps.tts.utils.opea_tts import OPEATTS

# Set up environment variables
os.environ.setdefault('TTS_MODEL_SERVER', 'fastapi')
os.environ.setdefault('TTS_MODEL_SERVER_ENDPOINT', 'http://localhost:8008')
os.environ.setdefault('TTS_USVC_PORT', '9009')

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/tts --cov-report=term --cov-report=html tests/unit/tts/test_utils_opea_tts.py

Alternatively, to run all tests for the 'tts' module, execute the following command:
   pytest --disable-warnings --cov=comps/tts --cov-report=term --cov-report=html tests/unit/tts
"""


def test_initialization_raises_exception_when_missing_required_args():
    """Test that initialization raises exception when required parameters are missing."""
    with pytest.raises(ValueError) as context:
        instance = object.__new__(OPEATTS)
        instance._model_server = "fastapi"
        instance._model_server_endpoint = ""
        instance._validate_config()
    assert "TTS_MODEL_SERVER_ENDPOINT" in str(context.value) or "cannot be empty" in str(context.value)

    with pytest.raises(ValueError) as context:
        instance = object.__new__(OPEATTS)
        instance._model_server = ""
        instance._model_server_endpoint = "http://server:1234"
        instance._validate_config()
    assert "TTS_MODEL_SERVER" in str(context.value) or "cannot be empty" in str(context.value)


def test_initialization_raises_exception_for_unsupported_model_server():
    """Test that initialization raises exception for unsupported model server."""
    with pytest.raises(Exception) as context:
        OPEATTS(model_server="unsupported_server", model_server_endpoint="http://server:1234")
    assert "Unsupported TTS model server" in str(context.value) or "fastapi" in str(context.value)


def test_validate_model_server_success():
    """Test that _validate_model_server succeeds when server is reachable."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_audio_content'
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        OPEATTS(
            model_server="fastapi",
            model_server_endpoint="http://server:1234"
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/audio/speech" in call_args[0][0]


def test_validate_model_server_fails_on_connection_error():
    """Test that _validate_model_server fails when connection fails."""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(ConnectionError) as context:
            OPEATTS(
                model_server="fastapi",
                model_server_endpoint="http://server:1234"
            )
        assert "Failed to connect" in str(context.value)


@pytest.mark.asyncio
async def test_generate_speech_success():
    """Test that generate_speech successfully generates audio."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_validation_audio'
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        instance = OPEATTS(
            model_server="fastapi",
            model_server_endpoint="http://server:1234"
        )

    # Mock the actual aiohttp call
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b'fake_audio_data')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_post_context = MagicMock()
        mock_post_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_context.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = MagicMock()
        mock_session_instance.post = MagicMock(return_value=mock_post_context)
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)

        mock_session.return_value = mock_session_instance

        result = await instance.generate_speech(
            text="Hello world",
            voice="default",
            response_format="mp3"
        )

        assert result == b'fake_audio_data'


@pytest.mark.asyncio
async def test_generate_speech_handles_http_error():
    """Test that generate_speech handles HTTP errors properly."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_validation_audio'
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        instance = OPEATTS(
            model_server="fastapi",
            model_server_endpoint="http://server:1234"
        )

    import aiohttp
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='{"detail": "Bad Request"}')
        mock_response.request_info = MagicMock()
        mock_response.history = []
        mock_response.headers = {}
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_post_context = MagicMock()
        mock_post_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_context.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = MagicMock()
        mock_session_instance.post = MagicMock(return_value=mock_post_context)
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)

        mock_session.return_value = mock_session_instance

        with pytest.raises(aiohttp.ClientResponseError):
            await instance.generate_speech(
                text="Hello world",
                voice="default",
                response_format="mp3"
            )


@pytest.mark.asyncio
async def test_generate_speech_for_chunks_success():
    """Test that generate_speech_for_chunks successfully generates audio for multiple chunks."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_validation_audio'
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        instance = OPEATTS(
            model_server="fastapi",
            model_server_endpoint="http://server:1234"
        )

    with patch.object(instance, 'generate_speech', new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = [b'chunk1_audio', b'chunk2_audio', b'chunk3_audio']

        text_chunks = ["First chunk", "Second chunk", "Third chunk"]
        results = []

        async for audio_bytes in instance.generate_speech_for_chunks(
            text_chunks=text_chunks,
            voice="default",
            response_format="mp3"
        ):
            results.append(audio_bytes)

        assert len(results) == 3
        assert results[0] == b'chunk1_audio'
        assert results[1] == b'chunk2_audio'
        assert results[2] == b'chunk3_audio'
        assert mock_generate.call_count == 3
