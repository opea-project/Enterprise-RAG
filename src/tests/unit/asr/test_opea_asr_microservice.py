from unittest.mock import MagicMock, patch

import pytest


"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/asr --cov-report=term --cov-report=html tests/unit/asr/test_opea_asr_microservice.py

Alternatively, to run all tests for the 'asr' module, execute the following command:
   pytest --disable-warnings --cov=comps/asr --cov-report=term --cov-report=html tests/unit/asr
"""


@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass