from unittest.mock import patch, AsyncMock
import pytest
from fastapi import HTTPException
from comps.tts.utils.opea_tts import OPEATTS

@pytest.fixture
def mock_huggingface_hub():
    with patch('comps.tts.utils.opea_tts.AsyncInferenceClient', autospec=True) as MockClass:
        mock_instance = MockClass.return_value
        mock_instance.post = AsyncMock(return_value=b'[0.1, 0.2, 0.3]')
        yield MockClass

@pytest.fixture
def teardown():
    yield
    OPEATTS._instance = None

def test_singleton_behavior(teardown):
    instance1 = OPEATTS("model1", "model_server", "http://test-endpoint")
    instance2 = OPEATTS("model1", "model_server", "http://test-endpoint")
    assert instance1 is instance2

def test_singleton_behavior_different_params(teardown):
    instance1 = OPEATTS("model1", "model_server", "http://test-endpoint")
    with pytest.raises(Exception) as exc_info:
        OPEATTS("model2", "model_server", "http://test-endpoint")
        assert "OPEATTS instance already exists with different model name or model server." in exc_info.value.args[0]

def test_initialization(teardown):
    model_name = "test_model"
    model_server = "test_server"
    endpoint = "http://test-endpoint"
    tts_instance = OPEATTS(model_name, model_server, endpoint)

    assert tts_instance._model_name == model_name.split('/')[-1].lower()
    assert tts_instance._model_server == model_server.lower()
    assert tts_instance._endpoint == endpoint

@pytest.mark.asyncio
async def test_tts_success(mock_huggingface_hub, teardown):
    opea_tts = OPEATTS("microsoft/speecht5_tts", "model_server", "http://test-endpoint")
    response = await opea_tts.tts("Hello world", "default", "wav")
    assert response.status_code == 200
    assert response.media_type == "audio/wav"

@pytest.mark.asyncio
async def test_run_success(mock_huggingface_hub, teardown):
    opea_tts = OPEATTS("microsoft/speecht5_tts", "model_server", "http://test-endpoint")
    request_data = {
        "model": "microsoft/speecht5_tts",
        "voice": "default",
        "format": "wav",
        "input_data": "Hello world"
    }
    response = await opea_tts.run(request_data)
    assert response.status_code == 200
    assert response.media_type == "audio/wav"

@pytest.mark.asyncio
async def test_run_model_mismatch(teardown):
    opea_tts = OPEATTS("microsoft/speecht5_tts", "model_server", "http://test-endpoint")
    request_data = {
        "model": "unknown_model",
        "voice": "default",
        "format": "wav",
        "input_data": "Hello world"
    }
    with pytest.raises(Exception, match="TTS model mismatch!"):
        await opea_tts.run(request_data)

@pytest.mark.asyncio
async def test_run_voice_warning(mock_huggingface_hub, teardown, caplog):
    opea_tts = OPEATTS("microsoft/speecht5_tts", "model_server", "http://test-endpoint")
    request_data = {
        "model": "microsoft/speecht5_tts",
        "voice": "female",
        "format": "wav",
        "input_data": "Hello world"
    }
    with pytest.raises(Exception, match="Currently parameter 'voice' can only be default or male!"):
        await opea_tts.run(request_data)

@pytest.mark.asyncio
async def test_run_internal_server_error(mock_huggingface_hub, teardown):
    mock_huggingface_hub.return_value.post.side_effect = Exception("Test error")
    opea_tts = OPEATTS("microsoft/speecht5_tts", "model_server", "http://test-endpoint")
    request_data = {
        "model": "microsoft/speecht5_tts",
        "voice": "default",
        "format": "wav",
        "input_data": "Hello world"
    }
    with pytest.raises(HTTPException, match="Internal Server Error"):
        await opea_tts.run(request_data)
