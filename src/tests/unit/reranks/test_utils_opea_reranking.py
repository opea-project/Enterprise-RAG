# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch  #, AsyncMock

import pytest
import requests
from comps import (
    SearchedDoc,
    TextDoc,
)
from comps.reranks.utils.opea_reranking import OPEAReranker

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/reranks --cov-report=term --cov-report=html tests/unit/reranks/test_utils_opea_reranking.py

Alternatively, to run all tests for the 'reranks' module, execute the following command:
   pytest --disable-warnings --cov=comps/reranks --cov-report=term --cov-report=html tests/unit/reranks
"""

@pytest.fixture
def test_class():
    """Fixture to create OPEAReranker instance."""
    with patch.object(OPEAReranker, '_validate', return_value='Mocked Method'):
        return OPEAReranker(service_endpoint="http:/test:1234", model_server="tei")

@pytest.fixture
def mock_input_data():
    """Fixture to provide mock input data."""
    return SearchedDoc(
        initial_query="This is my sample query?",
        retrieved_docs=[
            TextDoc(text="Document 1"),
            TextDoc(text="Document 2"),
            TextDoc(text="Document 3"),
        ],
        top_n=1,
    )

@pytest.fixture
def mock_response_data():
    """Fixture to provide mock response data."""
    return [
        {"index": 1, "score": 0.9988041},
        {"index": 0, "score": 0.02294873},
        {"index": 2, "score": 0.5294873},
    ]

def test_initialization_succeeds_with_valid_params():
    # Assert that the instance is created successfully
    with patch.object(OPEAReranker, '_validate', return_value='Mocked Method'):
        assert isinstance(OPEAReranker(service_endpoint="http:/test:1234/reranks", model_server="tei"), OPEAReranker), "Instance was not created successfully."


def test_initializaction_raises_exception_when_missing_required_arg():
    # nothing is passed
    with pytest.raises(Exception) as context:
        OPEAReranker()

    assert str(context.value).endswith("missing 2 required positional arguments: 'service_endpoint' and 'model_server'")

    # empty string is passed
    with pytest.raises(Exception) as context:
        OPEAReranker(service_endpoint="",  model_server="tei")

    assert str(context.value) == "The 'RERANKING_SERVICE_ENDPOINT' cannot be empty."

def test_initializaction_raises_exception_when_incorrect_model_server():
    # wrong model server is passed
    with pytest.raises(ValueError) as context:
        OPEAReranker(service_endpoint="http://127.0.0.1:8090",  model_server="te")

    assert "Unsupported model server" in str(context.value)

def test_reranker_filter_top_n(test_class):
    scores = [{"index": 1, "score": 0.9988041}, {"index": 0, "score": 0.02294873}, {"index": 2, "score": 0.5294873}]
    top_n = 1
    output = test_class._filter_top_n(top_n, scores)

    assert len(output) == 1, "The output should contain only 1 element"
    assert output[0]["index"] == 1, "The output should contain the element with the highest score"
    assert output[0]["score"] == 0.9988041, "The output should contain the element with the highest score"

def test_torchserve_retrieve_torchserve_model_name():
    with patch('comps.reranks.utils.opea_reranking.requests.get', autospec=True) as MockClass:
        with patch.object(OPEAReranker, '_validate', return_value='Mocked Method'):
            MockClass.return_value.raise_for_status.return_value = None
            MockClass.return_value.json.return_value = {"models": [{"modelName": "bge-reranker-base", "modelUrl": "bge-reranker-base.tar.gz"}]}
            r = OPEAReranker(service_endpoint="http:/test:1234", model_server="torchserve")

        assert r._service_endpoint == "http:/test:1234/predictions/bge-reranker-base", "The Torchserve service endpoint should be set to the correct value"

def test_torchserve_retrieve_torchserve_model_name_fails():
    with patch('comps.reranks.utils.opea_reranking.requests.get', autospec=True) as MockClass:
        with patch.object(OPEAReranker, '_validate', return_value='Mocked Method'):
            MockClass.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")
            with pytest.raises(Exception) as context:
                OPEAReranker(service_endpoint="http:/test:1234", model_server="torchserve")

                assert "An error occurred while retrieving the model name from the Torchserve model server" in str(context.value)

# TODO: Investigate and fix the test.
# Current issue: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
# @pytest.mark.asyncio
# @patch("comps.reranks.utils.opea_reranking.aiohttp.ClientSession.post")
# async def test_run_succeeds(mock_post, test_class, mock_input_data, mock_response_data):

#     # Mock the response from the reranking service
#     mock_post.return_value.json.return_value = mock_response_data
#     mock_post.return_value.raise_for_status.return_value = None

#     # Call the method being tested
#     result = await test_class.run(mock_input_data)

#     mock_post.assert_called_with(
#         test_class._service_endpoint + "/rerank",
#         data='{"query": "This is my sample query?", "texts": ["Document 1", "Document 2", "Document 3"]}',
#         headers={"Content-Type": "application/json"},
#     )

#     # Assert that result.query is not empty
#     assert result.initial_query, "Query is empty"

#     # Assert that the reranked_docs list has only 1 element
#     assert len(result.reranked_docs) == 1, "The reranked_docs list should have only 1 element as top_n=1 by default"
  
#     # Check the value of the first item in the reranked_docs list
#     assert result.reranked_docs[0].text == "Document 2", "The result reranked_docs should contain only the document with the highest score"
#     # # Assert that the reranked_docs contain "Document 2"
#     assert any(doc.text == "Document 2" for doc in result.reranked_docs), "The reranked_docs should contain 'Document 2'"
    
#     # Assert that the reranked_docs contain only text "Document 2" since it has the highest score
#     assert (
#         result.reranked_docs == ["Documents 2"]
#     ), "The result query should include only the document with the highest score"


# TODO: Investigate and fix the test.
# Current issue: An error occurred while requesting to the reranking service: __aenter__
# @pytest.mark.asyncio
# @patch("comps.reranks.utils.opea_reranking.aiohttp.ClientSession.post", new_callable=AsyncMock)
# async def test_run_succeeds_with_custom_top_N(mock_post, test_class, mock_input_data, mock_response_data):
#     mock_input_data.top_n = 2  # Set top_n to 2

#     # Mock the response from the reranking service
#     mock_post.return_value.json.return_value = mock_response_data
#     mock_post.return_value.raise_for_status.return_value = None

#     # Call the method being tested
#     result = await test_class.run(mock_input_data)

#     mock_post.assert_awaited_with(
#         test_class._service_endpoint + "/rerank",
#         data='{"query": "This is my sample query?", "texts": ["Document 1", "Document 2", "Document 3"]}',
#         headers={"Content-Type": "application/json"},
#     )

#     # Assert that result.query is not empty
#     assert result.initial_query, "Query is empty"

#     # Assert that the reranked_docs list has 2 elements
#     assert len(result.reranked_docs) == 2, "The reranked_docs list should have 2 elements as top_n=2"

#     # Check the values of the items in the reranked_docs list
#     assert result.reranked_docs[0].text == "Document 2", "The first document in reranked_docs should be 'Document 2'"
#     assert result.reranked_docs[1].text == "Document 3", "The second document in reranked_docs should be 'Document 3'"


# TODO: Investigate and fix the test.
# Current issue: An error occurred while requesting to the reranking service: __aenter__
# @pytest.mark.asyncio
# @patch("comps.reranks.utils.opea_reranking.aiohttp.ClientSession.post", new_callable=AsyncMock)
# async def test_run_returns_all_docs_when_server_unavailable(mock_post, test_class, mock_input_data):
#     # Simulate server being unavailable
#     mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")
#     mock_post.return_value.json.return_value = None

#     with pytest.raises(requests.exceptions.RequestException):
#         await test_class.run(mock_input_data)


# TODO: Investigate and fix the test.
# Current issue: An error occurred while requesting to the reranking service: __aenter__
# @pytest.mark.asyncio
# @patch("comps.reranks.utils.opea_reranking.aiohttp.ClientSession.post", new_callable=AsyncMock)
# async def test_call_reranker_raises_exception_when_server_is_unavailable(mock_post, test_class, mock_input_data):
#     initial_query = mock_input_data.initial_query
#     retrieved_docs = [doc.text for doc in mock_input_data.retrieved_docs]

#     # Simulate server unavailability
#     mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")

#     with pytest.raises(requests.exceptions.RequestException):
#         await test_class._call_reranker(initial_query, retrieved_docs)

#     assert mock_post.call_count == 1
#     mock_post.assert_awaited_with(
#         test_class._service_endpoint + "/rerank",
#         data='{"query": "This is my sample query?", "texts": ["Document 1", "Document 2", "Document 3"]}',
#         headers={"Content-Type": "application/json"},
#     )


@pytest.mark.asyncio
async def test_run_fallbacks_to_initial_query_if_no_retrieved_docs(test_class):
    input_data = SearchedDoc(
        initial_query="This is my sample query?", retrieved_docs=[], top_n=1
    )

    result = await test_class.run(input_data)

    assert result.data["initial_query"] == input_data.initial_query, "Query does not match the initial query as expected when no retrieved documents are provided"
    # Assert that the reranked_docs list is empty
    assert not result.data["reranked_docs"], "The reranked_docs list should be empty when no retrieved documents are provided"

@pytest.mark.asyncio
async def test_run_fallbacks_to_initial_query_for_invalid_retrieved_docs(test_class):
    input_data = SearchedDoc(
        initial_query="This is my sample query?",
        retrieved_docs=[
            TextDoc(text=""),  # empty text
            TextDoc(text="  "),  # tab
            TextDoc(text="  "),  # two spaces
        ],
        top_n=1,
    )

    result = await test_class.run(input_data)
    assert result.data["initial_query"] == input_data.initial_query, "Query does not match the initial query as expected when the provided retrieved_docs are empty or invalid"
     # Assert that the reranked_docs list is empty
    assert not result.data["reranked_docs"], "The reranked_docs list should be empty when the provided retrieved_docs are empty or invalid"


@pytest.mark.asyncio
async def test_run_raises_exception_on_empty_initial_query(test_class):
    input_data = SearchedDoc(
        initial_query="",
        retrieved_docs=[
            TextDoc(text="Document 1"),
            TextDoc(text="Document 2"),
            TextDoc(text="Document 3"),
        ],
        top_n=1,
    )

    with pytest.raises(ValueError) as context:
        await test_class.run(input_data)

    assert str(context.value) == "Initial query cannot be empty."


@pytest.mark.asyncio(scope="module")
@patch("comps.reranks.utils.opea_reranking.aiohttp.ClientSession.post")
async def test_run_raises_exception_on_top_N_below_one(mock_post, test_class):
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as context:
        input_data = SearchedDoc(
            initial_query="This is my sample query?",
            retrieved_docs=[
                TextDoc(text="Document 1"),
                TextDoc(text="Document 2"),
                TextDoc(text="Document 3"),
            ],
            top_n=-1,
        )

        await test_class.run(input_data)

    # Invalid query shouldn't be sent to the reranking service, so `post` shouldn't be called."
    mock_post.assert_not_called()

    assert "Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]" in str(context.value)
