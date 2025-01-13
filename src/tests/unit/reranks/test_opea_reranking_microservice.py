# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from requests.exceptions import RequestException

from comps import (
   LLMParamsDoc,
   SearchedDoc,
)
from comps.reranks.utils.opea_reranking import OPEAReranker

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/reranks --cov-report=term --cov-report=html tests/unit/reranks/test_opea_reranking_microservice.py

Alternatively, to run all tests for the 'reranks' module, execute the following command:
   pytest --disable-warnings --cov=comps/reranks --cov-report=term --cov-report=html tests/unit/reranks
"""

@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass


@pytest.fixture
def mock_call_reranker():
    with patch.object(OPEAReranker, '_call_reranker', return_value='Mocked Method') as mock:
        yield mock


@pytest.fixture()
def clean_env_vars():
   yield "clean_env_vars"
   # Clean up environment variables after tests.
   try:
      del os.environ['RERANKING_SERVICE_ENDPOINT']
   except Exception:
      pass

@pytest.fixture
def mock_OPEAReranker():
   with patch('comps.reranks.utils.opea_reranking.OPEAReranker.__init__', autospec=True) as MockClass:
      MockClass.return_value = None
      yield MockClass


@patch('dotenv.load_dotenv')
def test_microservice_declaration_complies_with_guidelines(mock_load_dotenv, mock_OPEAReranker, mock_cores_mega_microservice):
   try:
      import comps.reranks.opea_reranking_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Reranking Microservice init raised {type(e).__name__} unexpectedly!")

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


def test_initialization_succeeds_with_defaults(mock_cores_mega_microservice, mock_call_reranker):
   # The configuration in the dotenv file shall satisfy all parameters specified as required
   try:
      import comps.reranks.opea_reranking_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Reranking Microservice init raised {type(e).__name__} unexpectedly!")

   # Assert that _model_name is a non-empty string
   assert isinstance(test_module.opea_reranker._service_endpoint, str) and test_module.opea_reranker._service_endpoint, "The service_endpoint is expected to be a non-empty string"


def test_initialization_succeeds_with_env_vars_present(clean_env_vars, mock_call_reranker):
   with patch.dict("os.environ",
      {
         "RERANKING_SERVICE_ENDPOINT": "http://testhost:1234",
      },
   ):
      try:
         # Import the module here to ensure environment variables are set before use
         import comps.reranks.opea_reranking_microservice as test_module
         importlib.reload(test_module)
      except Exception as e:
         pytest.fail(f"OPEA Reranking Microservice init raised {type(e)} unexpectedly!")

      # Assertions to check the initialized values
      assert test_module.opea_reranker._service_endpoint == "http://testhost:1234", "service url does not match"


def test_initialization_raises_exception_when_config_params_are_missing(clean_env_vars):
    # Test scenario with failing validation for service_endpoint
   with patch.dict("os.environ", {"RERANKING_SERVICE_ENDPOINT": ""}):
      with pytest.raises(Exception) as context:
         import comps.reranks.opea_reranking_microservice as test_module
         importlib.reload(test_module)
      assert str(context.value) == "The 'RERANKING_SERVICE_ENDPOINT' cannot be empty."


@patch('comps.reranks.opea_reranking_microservice.OPEAReranker.run')
def test_microservice_process_succeeds(mock_run, mock_cores_mega_microservice, mock_call_reranker):
   mock_input = MagicMock(spec=SearchedDoc)
   mock_response = MagicMock(spec=LLMParamsDoc)
   mock_run.return_value = mock_response

   try:
      import comps.reranks.opea_reranking_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Reranking Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function
   response = test_module.process(mock_input)
   mock_run.assert_called_once_with(mock_input)
   assert response == mock_response

   # Check if statistics_dict has an entry for the mock_input
   assert test_module.USVC_NAME in test_module.statistics_dict.keys(), f"statistics_dict does not have an entry for the microservice {test_module.USVC_NAME}"


@pytest.mark.parametrize("side_effect, expected_status_code, expected_detail", [
   (ValueError("Test Internal Error"), 400, "An internal error occurred while processing: Test Internal Error"),
   (RequestException("Test Connection Error"), 500, "An error occurred while processing: Test Connection Error"),
   (Exception("Test Unknown Error"), 500, "An error occurred while processing: Test Unknown Error"),
])
@patch('comps.reranks.opea_reranking_microservice.OPEAReranker.run')
def test_microservice_process_failure(mock_run, mock_cores_mega_microservice, side_effect, expected_status_code, expected_detail, mock_call_reranker):
   mock_input = MagicMock(spec=SearchedDoc)
   mock_run.side_effect = side_effect

   try:
     import comps.reranks.opea_reranking_microservice as test_module
     importlib.reload(test_module)
   except Exception as e:
     pytest.fail(f"OPEA Reranking Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function and assert exception
   with pytest.raises(HTTPException) as context:
     test_module.process(mock_input)

   mock_run.assert_called_once_with(mock_input)

   assert context.value.status_code == expected_status_code
   assert expected_detail in context.value.detail

@pytest.mark.parametrize("side_effect, expected_status_code, expected_detail", [
   (ValueError("Test Invalid Value Error"), 400, "An internal error occurred while processing: Test Invalid Value Error"),
   (RequestException("Test Connection Error"), 500, "An error occurred while processing: Test Connection Error"),
   (Exception("Test Unknown Error"), 500, "An error occurred while processing: Test Unknown Error"),
])
@patch('comps.reranks.opea_reranking_microservice.OPEAReranker.run')
def test_microservice_process_failure4(mock_run, mock_cores_mega_microservice, side_effect, expected_status_code, expected_detail, mock_call_reranker):
   mock_input = MagicMock(spec=SearchedDoc)
   mock_run.side_effect = side_effect

   try:
      import comps.reranks.opea_reranking_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA Reranking Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function and assert exception
   with pytest.raises(HTTPException) as context:
      test_module.process(mock_input)

   # Assertions
   mock_run.assert_called_once_with(mock_input)
   assert context.value.status_code == expected_status_code
   assert expected_detail in context.value.detail

def test_request_to_reranker_service_succeeds():
   with patch('requests.post') as mock_post:
      with patch.object(OPEAReranker, '_validate', return_value='Mocked Method'):
         reranker = OPEAReranker("http://testhost:1234")

         # Call the _call_reranker method
         reranker._call_reranker("Test Query", ["Test Doc 1", "Test Doc 2"])
         mock_post.assert_called_once_with('http://testhost:1234/rerank',
                                           data='{"query": "Test Query", "texts": ["Test Doc 1", "Test Doc 2"]}',
                                           headers={'Content-Type': 'application/json'})