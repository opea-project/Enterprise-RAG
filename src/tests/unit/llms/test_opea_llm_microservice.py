# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import Response

from comps import (
   LLMParamsDoc,
)

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms/test_opea_llm_microservice.py

Alternatively, to run all tests for the 'llms' module, execute the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms
"""

@pytest.fixture
def mock_get_connector():
   with patch('comps.llms.utils.opea_llm.OPEALlm._get_connector', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass

@pytest.fixture
def mock_validate_config():
   with patch('comps.llms.utils.opea_llm.OPEALlm._validate_config', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass

@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass

@pytest.fixture()
def clean_env_vars():
   yield "clean_env_vars"
   # Clean up environment variables after tests.
   try:
      del os.environ['LLM_MODEL_NAME']
      del os.environ['LLM_MODEL_SERVER']
      del os.environ['LLM_MODEL_SERVER_ENDPOINT']
      del os.environ['LLM_CONNECTOR']
   except Exception:
      pass

@pytest.fixture
def mock_OPEALlm():
   with patch('comps.llms.utils.opea_llm.OPEALlm.__init__', autospec=True) as MockClass:
      MockClass.return_value = None
      yield MockClass

@patch('dotenv.load_dotenv')
def test_microservice_declaration_complies_with_guidelines(mock_load_dotenv, mock_get_connector, mock_validate_config, mock_cores_mega_microservice):
   try:
      import comps.llms.opea_llm_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA LLM Microservice init raised {type(e).__name__} unexpectedly!")

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


def test_initialization_succeeds_with_defaults(mock_get_connector, mock_cores_mega_microservice):
   # The configuration in the dotenv file shall satisfy all parameters specified as required
   try:
      import comps.llms.opea_llm_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA LLM Microservice init raised {type(e).__name__} unexpectedly!")

   # Assert that _model_name is a non-empty string
   assert isinstance(test_module.opea_llm._model_name, str) and test_module.opea_llm._model_name, "The model_name is expected to be a non-empty string"

   # Assert that _model_server is a non-empty string
   assert isinstance(test_module.opea_llm._model_server, str) and test_module.opea_llm._model_server, "The _model_server is expected to be a non-empty string"

   # Assert that _model_server_endpoint is a non-empty string
   assert isinstance(test_module.opea_llm._model_server_endpoint, str) and test_module.opea_llm._model_server_endpoint, "The _model_server_endpoint is expected to be a non-empty string"


def test_initialization_succeeds_with_env_vars_present(mock_get_connector, clean_env_vars):
   with patch.dict("os.environ",
      {
         "LLM_MODEL_NAME": "test_model_name",
         "LLM_MODEL_SERVER": "test_model_server",
         "LLM_MODEL_SERVER_ENDPOINT": "http://testhost:1234",
         "LLM_CONNECTOR": "",
      },
   ):
      try:
         # Import the module here to ensure environment variables are set before use
         import comps.llms.opea_llm_microservice as test_module
         importlib.reload(test_module)
      except Exception as e:
         pytest.fail(f"OPEA LLM Microservice init raised {type(e)} unexpectedly!")

      # Assertions to check the initialized values
      assert test_module.opea_llm._model_name == "test_model_name", "Model name does not match"
      assert test_module.opea_llm._model_server == "test_model_server", "Model server does not match"
      assert test_module.opea_llm._model_server_endpoint == "http://testhost:1234", "Model server endpoint does not match"
      assert test_module.opea_llm._connector_name == "", "Connector name should be empty"


def test_initialization_raises_exception_when_config_params_are_missing(mock_get_connector, clean_env_vars):
   # Test scenario with failing validation for model_name
   with patch.dict("os.environ", {"LLM_MODEL_NAME": ""}):
      with pytest.raises(Exception) as context:
         import comps.llms.opea_llm_microservice as test_module
         importlib.reload(test_module)
      assert str(context.value) == "The 'LLM_MODEL_NAME' cannot be empty."

   # Test scenario with failing validation for model_server
   with patch.dict("os.environ", {"LLM_MODEL_SERVER": ""}):
      with pytest.raises(Exception) as context:
         import comps.llms.opea_llm_microservice as test_module
         importlib.reload(test_module)
      assert str(context.value) == "The 'LLM_MODEL_SERVER' cannot be empty."

   # Test scenario with failing validation for model_server_endpoint
   with patch.dict("os.environ", {"LLM_MODEL_SERVER_ENDPOINT": ""}):
      with pytest.raises(Exception) as context:
         import comps.llms.opea_llm_microservice as test_module
         importlib.reload(test_module)
      assert str(context.value) == "The 'LLM_MODEL_SERVER_ENDPOINT' cannot be empty."


@patch('comps.llms.opea_llm_microservice.OPEALlm.run')
def test_microservice_process_succeeds(mock_run, mock_cores_mega_microservice, mock_get_connector):
   mock_input = MagicMock(spec=LLMParamsDoc)
   mock_response = MagicMock(spec=Response)
   mock_run.return_value = mock_response

   try:
      import comps.llms.opea_llm_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA LLM Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function
   response = test_module.process(mock_input)
   mock_run.assert_called_once_with(mock_input)
   assert response == mock_response

   # Check if statistics_dict has an entry for the mock_input
   assert test_module.USVC_NAME in test_module.statistics_dict.keys(), f"statistics_dict does not have an entry for the microservice {test_module.USVC_NAME}"


@patch('comps.llms.opea_llm_microservice.OPEALlm.run')
def test_microservice_process_failure(mock_run, mock_cores_mega_microservice, mock_get_connector):
   mock_input = MagicMock(spec=LLMParamsDoc)
   mock_run.side_effect = Exception("Test Exception")

   try:
      import comps.llms.opea_llm_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA LLM Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function and assert exception
   with pytest.raises(HTTPException) as context:
      test_module.process(mock_input)

   # Assertions
   assert context.value.status_code == 500
   assert "An error occurred while processing: Test Exception" in context.value.detail
   mock_run.assert_called_once_with(mock_input)
