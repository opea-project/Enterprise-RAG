# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import pytest


"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/prompt_template --cov-report=term --cov-report=html tests/unit/prompt_template/test_opea_prompt_template_microservice.py

Alternatively, to run all tests for the 'prompt_template' module, execute the following command:
   pytest --disable-warnings --cov=comps/prompt_template --cov-report=term --cov-report=html tests/unit/prompt_template
"""


@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass

# TODO: Investigate and fix the test.
# Current issue: Task was destroyed but it is pending.
# NOTE: The error does not occur every time, on average every 3rd run, and only when running all the tests
# @patch('dotenv.load_dotenv')
# def test_microservice_declaration_complies_with_guidelines(mock_load_dotenv,mock_cores_mega_microservice):
#    try:
#       import comps.prompt_template.opea_prompt_template_microservice as test_module
#       importlib.reload(test_module)
#    except Exception as e:
#       pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e).__name__} unexpectedly!")

#    # Assert that load_dotenv was called once with the expected argument
#    mock_load_dotenv.assert_called()
#    called_path = mock_load_dotenv.call_args[0][0]  # Get the first argument of the first call
#    expected_suffix = '/impl/microservice/.env'

#    assert called_path.endswith(expected_suffix), \
#       f"Expected load_dotenv to be called with a path ending in '{expected_suffix}', but got '{called_path}'"

#    # Check if required elements are declared
#    assert hasattr(test_module, 'USVC_NAME'), "USVC_NAME is not declared"
#    assert hasattr(test_module, 'logger'), "logger is not declared"
#    assert hasattr(test_module, 'register_microservice'), "register_microservice is not declared"
#    assert hasattr(test_module, 'statistics_dict'), "statistics_dict is not declared"
#    assert hasattr(test_module, 'process'), "process is not declared"


# TODO: Investigate and fix the test.
# Current issue: Task was destroyed but it is pending.
# NOTE: The error does not occur every time, on average every 3rd run, and only when running all the tests
# def test_initialization_succeeds(mock_cores_mega_microservice):
#    # The configuration in the dotenv file shall satisfy all parameters specified as required
#    try:
#       import comps.prompt_template.opea_prompt_template_microservice as test_module
#       importlib.reload(test_module)
#    except Exception as e:
#       pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e).__name__} unexpectedly!")

#    # Assert that prompt_template is not empty
#    assert isinstance(test_module.opea_prompt_template.prompt_template, str) and test_module.opea_prompt_template.prompt_template, "The prompt_template is expected to be a non-empty string"