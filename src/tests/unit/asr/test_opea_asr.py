from unittest.mock import patch, AsyncMock
import pytest
from fastapi import HTTPException
from comps.asr.utils.opea_asr import OPEAASR

@pytest.fixture
def mock_huggingface_hub():
    with patch('comps.asr.utils.opea_asr.AsyncInferenceClient', autospec=True) as MockClass:
        mock_instance = MockClass.return_value
        mock_instance.post = AsyncMock(return_value=b'["test transcription"]')
        yield MockClass

@pytest.fixture
def teardown():
    yield
    OPEAASR._instance = None

def test_singleton_behavior(teardown):
    instance1 = OPEAASR("model1", "model_server", "http://test-endpoint")
    instance2 = OPEAASR("model1", "model_server", "http://test-endpoint")
    assert instance1 is instance2

def test_singleton_behavior_different_params(teardown):
    instance1 = OPEAASR("model1", "model_server", "http://test-endpoint")
    with pytest.raises(Exception) as exc_info:
        OPEAASR("model2", "model_server", "http://test-endpoint")
        assert "OPEAASR instance already exists with different model name or model server." in exc_info.value.args[0]

def test_initialization(teardown):
    model_name = "test_model"
    model_server = "test_server"
    endpoint = "http://test-endpoint"
    asr_instance = OPEAASR(model_name, model_server, endpoint)
    assert asr_instance._model_name == model_name.split('/')[-1].lower()
    assert asr_instance._model_server == model_server.lower()
    assert asr_instance._endpoint == endpoint

@pytest.mark.asyncio
async def test_asr_success(mock_huggingface_hub, teardown):
    opea_asr = OPEAASR("openai/whisper-small", "model_server", "http://test-endpoint")
    response = await opea_asr.asr(b"audio data")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_run_success(mock_huggingface_hub, teardown):
    opea_asr = OPEAASR("openai/whisper-small", "model_server", "http://test-endpoint")
    request_data = b"audio data"
    response = await opea_asr.run(request_data)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_run_internal_server_error(mock_huggingface_hub, teardown):
    mock_huggingface_hub.return_value.post.side_effect = Exception("Test error")
    opea_asr = OPEAASR("openai/whisper-small", "model_server", "http://test-endpoint")
    request_data = b"audio data"
    with pytest.raises(HTTPException, match="Internal Server Error"):
        await opea_asr.run(request_data)
