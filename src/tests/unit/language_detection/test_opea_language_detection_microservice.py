# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from comps import (
   GeneratedDoc,
   LLMParamsDoc,
)

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/language_detection --cov-report=term --cov-report=html tests/unit/language_detection/test_opea_language_detection_microservice.py

Alternatively, to run all tests for the 'language_detection' module, execute the following command:
   pytest --disable-warnings --cov=comps/language_detection --cov-report=term --cov-report=html tests/unit/language_detection
"""

@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass

@pytest.fixture
def mock_OPEALanguageDetector():
   with patch('comps.language_detection.utils.opea_language_detection.OPEALanguageDetector.__init__', autospec=True) as MockClass:
      MockClass.return_value = None
      yield MockClass


@patch('dotenv.load_dotenv')
def test_microservice_declaration_complies_with_guidelines(mock_load_dotenv, mock_OPEALanguageDetector, mock_cores_mega_microservice):
   try:
      import comps.language_detection.opea_language_detection_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Language Detection Microservice init raised {type(e).__name__} unexpectedly!")

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

@patch('comps.language_detection.utils.opea_language_detection.OPEALanguageDetector.run')
def test_microservice_process_succeeds(mock_run, mock_cores_mega_microservice):
   mock_input = MagicMock(spec=GeneratedDoc)
   mock_response = MagicMock(spec=LLMParamsDoc)
   mock_run.return_value = mock_response

   try:
      import comps.language_detection.opea_language_detection_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Language Detection Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function
   response = test_module.process(mock_input)
   mock_run.assert_called_once_with(mock_input)
   assert response == mock_response

   # Check if statistics_dict has an entry for the mock_input
   assert test_module.USVC_NAME in test_module.statistics_dict.keys(), f"statistics_dict does not have an entry for the microservice {test_module.USVC_NAME}"

@patch('comps.language_detection.utils.opea_language_detection.OPEALanguageDetector.run')
def test_microservice_process_failure(mock_run, mock_cores_mega_microservice):
   mock_input = MagicMock(spec=GeneratedDoc)
   mock_run.side_effect = Exception("Test Exception")

   try:
      import comps.language_detection.opea_language_detection_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Language Detection Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function and assert exception
   with pytest.raises(HTTPException) as context:
      test_module.process(mock_input)

   # Assertions
   assert context.value.status_code == 500
   assert "An error occurred while processing: Test Exception" in context.value.detail
   mock_run.assert_called_once_with(mock_input)