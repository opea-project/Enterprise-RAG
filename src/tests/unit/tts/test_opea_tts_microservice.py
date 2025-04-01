from unittest.mock import MagicMock, patch

import pytest


"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/tts --cov-report=term --cov-report=html tests/unit/tts/test_opea_tts_microservice.py

Alternatively, to run all tests for the 'tts' module, execute the following command:
   pytest --disable-warnings --cov=comps/tts --cov-report=term --cov-report=html tests/unit/tts
"""


@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass