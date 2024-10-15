# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from comps.llms.utils.connectors.generic_connector import GenericLLMConnector
from comps.llms.utils.connectors.langchain_connector import LangchainLLMConnector
from comps.llms.utils.opea_llm import OPEALlm


@pytest.fixture
def mock_connector_validate():
    with mock.patch('comps.llms.utils.connectors.connector.LLMConnector._validate', autospec=True) as MockClass:
        MockClass.return_value = MagicMock()
        yield MockClass


@pytest.fixture
def reset_singleton():
    # Reset singleton instance to prevent residual state between tests
    GenericLLMConnector._instance= None
    LangchainLLMConnector._instance = None

@pytest.fixture
def mock_get_connector():
   with patch('comps.llms.utils.opea_llm.OPEALlm._get_connector', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass


def test_initialization_succeeds_with_valid_params(reset_singleton, mock_get_connector):
    # Assert that the instance is created successfully
    assert isinstance(OPEALlm(model_name="model1", model_server="vllm", model_server_endpoint="http://server:1234", connector_name="langchain"), OPEALlm), "Instance was not created successfully."
    assert isinstance(OPEALlm(model_name="model2", model_server="tgi", model_server_endpoint="http://server:1234", connector_name="langchain"), OPEALlm), "Instance was not created successfully."

    instance1 = OPEALlm(model_name="model1", model_server="vllm", model_server_endpoint="http://server:1234", connector_name="langchain")
    assert isinstance(instance1, OPEALlm), "Instance was not created successfully."
    assert instance1._model_name == "model1","Is inconsistent with the provided parameters"
    assert instance1._model_server == "vllm","Is inconsistent with the provided parameters"
    assert instance1._model_server_endpoint == "http://server:1234","Is inconsistent with the provided parameters"
    assert instance1._connector_name.upper() == "LANGCHAIN", "Is inconsistent with the provided parameters"

    # Assert that the instance is created successfully when connector_name is not provided (as it is optional)
    instance2 = OPEALlm("model2", "tgi", "http://server:1234")
    assert isinstance(instance2, OPEALlm), "Instance was not created successfully."
    assert instance2._connector_name.upper() == "GENERIC", "Connector name should be 'generic' by default."

    # Assert that the instance is created successfully when connector_name is empty string (as it is optional)
    instance2 = OPEALlm(model_name="model2", model_server="tgi", model_server_endpoint="http://server:1234", connector_name=" ")
    assert isinstance(instance2, OPEALlm), "Instance was not created successfully."
    # todo: check if the connector handler is the type of generic


def test_initializaction_raises_exception_when_missing_required_args(reset_singleton, mock_get_connector):
    # missing model name
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="", model_server="vllm", model_server_endpoint="http://server:1234", connector_name="langchain")
    assert str(context.value) == "The 'LLM_MODEL_NAME' cannot be empty."

    # missing model server
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="model1", model_server="", model_server_endpoint="http://server:1234", connector_name="langchain")
    assert str(context.value) == "The 'LLM_MODEL_SERVER' cannot be empty."

    # missing model server endpoint
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="model1", model_server="tgi", model_server_endpoint="", connector_name="langchain")
    assert str(context.value) == "The 'LLM_MODEL_SERVER_ENDPOINT' cannot be empty."


def test_initialization_raises_exception_when_request_unsupported_connector(reset_singleton):
    # request explicitly for an unsupported connector
    with pytest.raises(Exception) as context:
        OPEALlm(model_name="model1", model_server="tgi", model_server_endpoint="http://server:1234", connector_name="invalid")

    assert str(context.value) == "Invalid connector name: invalid. Expected to be either 'langchain', 'generic', or unset."


@pytest.mark.parametrize("sut_model_server_name", ["vllm", "tgi"])
@patch('comps.llms.utils.connectors.langchain_connector.LangchainLLMConnector')
def test_get_connector_succeeds_for_langchain(MockLangchainLLMConnector, sut_model_server_name, reset_singleton, mock_connector_validate):
    sut_connector = "langchain"
    try:
        sut_instance = OPEALlm(model_name="model1", model_server=sut_model_server_name, model_server_endpoint="http://server:1234", connector_name=sut_connector)
    except Exception as e:
        pytest.fail(f"OPEA LLM init raised {type(e)} unexpectedly!")

    MockLangchainLLMConnector.assert_called_once_with(sut_instance._model_name, sut_instance._model_server, sut_instance._model_server_endpoint)


@pytest.mark.parametrize("sut_model_server_name", ["vllm", "tgi"])
@patch('comps.llms.utils.connectors.generic_connector.GenericLLMConnector')
def test_get_connector_succeeds_for_generic(MockGenericLLMConnector, sut_model_server_name, reset_singleton, mock_connector_validate):
    sut_connector="generic"
    try:
        sut_instance = OPEALlm(model_name="model1", model_server=sut_model_server_name, model_server_endpoint="http://server:1234", connector_name=sut_connector)
    except Exception as e:
        pytest.fail(f"OPEA LLM init raised {type(e)} unexpectedly!")

    MockGenericLLMConnector.assert_called_once_with(sut_instance._model_name, sut_instance._model_server, sut_instance._model_server_endpoint)
