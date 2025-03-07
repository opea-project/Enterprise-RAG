# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from unittest.mock import MagicMock, patch
from unittest import mock
from unittest.mock import MagicMock
import pytest
from comps.retrievers.utils.opea_retriever import OPEARetriever
from comps import (
  EmbedDoc,
  SearchedDoc,
  TextDoc
)
from requests.exceptions import HTTPError, RequestException, Timeout
from fastapi import HTTPException

@pytest.fixture(autouse=True)
def mock_asyncio_run():
    with mock.patch("asyncio.run") as mock_run:
        yield mock_run

@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ['VECTOR_STORE'] = 'redis'
    yield
    if 'VECTOR_STORE' in os.environ:
        del os.environ['VECTOR_STORE']

@pytest.fixture
def mock_cores_mega_microservice():
   with patch('comps.cores.mega.micro_service', autospec=True) as MockClass:
      MockClass.return_value = MagicMock()
      yield MockClass

@pytest.fixture()
def clean_env_vars():
   yield "clean_env_vars"
   # Clean up environment variables after tests.
   if 'VECTOR_STORE' in os.environ:
       del os.environ['VECTOR_STORE']

@pytest.fixture
def mock_OPEARetriever():
   with patch('comps.retrievers.utils.opea_retriever.OPEARetriever.__init__', autospec=True) as MockClass:
      MockClass.return_value = None
      yield MockClass

@patch('dotenv.load_dotenv')
def test_microservice_declaration_complies_with_guidelines(mock_load_dotenv, mock_OPEARetriever, mock_cores_mega_microservice):
   try:
      import comps.retrievers.opea_retriever_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA OPEARetriever Microservice init raised {type(e).__name__} unexpectedly!")

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


def test_initialization_succeeds_with_defaults(mock_cores_mega_microservice,mock_OPEARetriever ):
   # The configuration in the dotenv file shall satisfy all parameters specified as required
   try:
      import comps.retrievers.opea_retriever_microservice as test_module
      importlib.reload(test_module)
   except Exception as e:
      pytest.fail(f"OPEA OPEARetriever Microservice init raised {type(e).__name__} unexpectedly!")

   # Assert that _model_name is a non-empty string
   assert test_module.retriever.vector_store is not None, "The vector is expected"

@pytest.mark.asyncio
@patch('comps.retrievers.opea_retriever_microservice.OPEARetriever.retrieve')
async def test_microservice_process_succeeds(mock_retrieve, mock_cores_mega_microservice, mock_OPEARetriever):
    mock_input = MagicMock(spec=EmbedDoc)
    mock_response = SearchedDoc(
        initial_query="This is my sample query?",
        retrieved_docs=[
            TextDoc(text=""),
            TextDoc(text="  "),  
        ])
    mock_retrieve.return_value = mock_response

    try:
        import comps.retrievers.opea_retriever_microservice as test_module
        importlib.reload(test_module)
    except Exception as e:
        pytest.fail(f"OPEA OPEARetriever Microservice init raised {type(e).__name__} unexpectedly!")

    # Call the process function
    response = await test_module.process(mock_input)
    mock_retrieve.assert_called_once_with(mock_input)
    assert response == mock_response

    # Check if statistics_dict has an entry for the mock_input
    assert test_module.USVC_NAME in test_module.statistics_dict.keys(), f"statistics_dict does not have an entry for the microservice {test_module.USVC_NAME}"


@pytest.mark.asyncio
@pytest.mark.parametrize("side_effect, expected_status_code, expected_detail", [
   (ValueError("Test Internal Error"), 400, "A ValueError occured while validating the input in retriever: Test Internal Error"),
   (NotImplementedError("Test Not Implemented Error"), 501, "A NotImplementedError occured in retriever: Test Not Implemented Error"),
   (Exception("Test Unknown Error"), 500, "An Error while retrieving documents. Test Unknown Error"),
])
@patch('comps.retrievers.opea_retriever_microservice.OPEARetriever.retrieve')
async def test_microservice_process_failure(mock_retrieve, mock_cores_mega_microservice, side_effect, expected_status_code, expected_detail, mock_OPEARetriever):
   mock_input = MagicMock(spec=EmbedDoc)
   mock_retrieve.side_effect = side_effect

   try:
        import comps.retrievers.opea_retriever_microservice as test_module
        importlib.reload(test_module)
   except Exception as e:
        pytest.fail(f"OPEA OPEARetriever Microservice init raised {type(e).__name__} unexpectedly!")

   # Call the process function and assert exception
   with pytest.raises(HTTPException) as context:
     await test_module.process(mock_input)

   mock_retrieve.assert_called_once_with(mock_input)

   assert context.value.status_code == expected_status_code
   assert expected_detail in context.value.detail
