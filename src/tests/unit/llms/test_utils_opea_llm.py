# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from comps.llms.utils.opea_llm import OPEALlm

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms/test_utils_opea_llm.py

Alternatively, to run all tests for the 'llms' module, execute the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms
"""

@pytest.fixture
def reset_singleton():
    OPEALlm._instance = None
    yield
    OPEALlm._instance = None

@pytest.fixture
def mock_connector_validate():
    with mock.patch('comps.llms.utils.connectors.connector.LLMConnector._validate', autospec=True) as MockClass:
        MockClass.return_value = MagicMock()
        yield MockClass

@pytest.fixture
def mock_get_connector():
   with patch('comps.llms.utils.opea_llm.OPEALlm._get_connector', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass


def test_initialization_succeeds_with_valid_params(reset_singleton, mock_get_connector):
    # Assert that the instance is created successfully
    assert isinstance(OPEALlm(model_name="model1", model_server="vllm", model_server_endpoint="http://server:1234", disable_streaming=False), OPEALlm), "Instance was not created successfully."

    instance1 = OPEALlm(model_name="model1", model_server="vllm", model_server_endpoint="http://server:1234", disable_streaming=True)
    assert isinstance(instance1, OPEALlm), "Instance was not created successfully."
    assert instance1._model_name == "model1","Is inconsistent with the provided parameters"
    assert instance1._model_server == "vllm","Is inconsistent with the provided parameters"
    assert instance1._model_server_endpoint == "http://server:1234","Is inconsistent with the provided parameters"
    assert instance1._disable_streaming, "Is inconsistent with the provided parameters"

    # Assert that the instance is created successfully when connector_name and disable_streaming is not provided (as it is optional)
    instance2 = OPEALlm("model2", "vllm", "http://server:1234")
    assert isinstance(instance2, OPEALlm), "Instance was not created successfully."
    assert not instance2._disable_streaming, "Disable streaming flag should be unset by default"

    # Assert that the instance is created successfully when connector_name is empty string (as it is optional)
    instance2 = OPEALlm(model_name="model2", model_server="vllm", model_server_endpoint="http://server:1234")
    assert isinstance(instance2, OPEALlm), "Instance was not created successfully."
    # todo: check if the connector handler is the type of generic


def test_initializaction_raises_exception_when_missing_required_args(reset_singleton, mock_get_connector):
    # missing model name
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="", model_server="vllm", model_server_endpoint="http://server:1234")
    assert str(context.value) == "The 'LLM_MODEL_NAME' cannot be empty."

    # missing model server
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="model1", model_server="", model_server_endpoint="http://server:1234")
    assert str(context.value) == "The 'LLM_MODEL_SERVER' cannot be empty."

    # missing model server endpoint
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="model1", model_server="vllm", model_server_endpoint="")
    assert str(context.value) == "The 'LLM_MODEL_SERVER_ENDPOINT' cannot be empty."
