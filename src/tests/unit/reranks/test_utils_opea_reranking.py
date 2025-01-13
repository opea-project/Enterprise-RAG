# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
import requests

from comps import (
    SearchedDoc,
    TextDoc,
)
from comps.reranks.utils.opea_reranking import OPEAReranker

# Define the template for the expected result
expected_result_template = """
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results:  {} \n
### Question: This is my sample query? \n
### Answer:
""".strip()

@pytest.fixture
def test_class():
    """Fixture to create OPEAReranker instance."""
    with patch.object(OPEAReranker, '_validate', return_value='Mocked Method'):
        return OPEAReranker(service_endpoint="http:/test:1234")

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
        assert isinstance(OPEAReranker(service_endpoint="http:/test:1234/reranks"), OPEAReranker), "Instance was not created successfully."


def test_initializaction_raises_exception_when_missing_required_arg():
    # nothing is passed
    with pytest.raises(Exception) as context:
        OPEAReranker()

    assert str(context.value).endswith("missing 1 required positional argument: 'service_endpoint'")

    # empty string is passed
    with pytest.raises(Exception) as context:
        OPEAReranker(service_endpoint="")

    assert str(context.value) == "The 'RERANKING_SERVICE_ENDPOINT' cannot be empty."


@patch("comps.reranks.utils.opea_reranking.requests.post")
def test_run_suceeds(mock_post, test_class, mock_input_data, mock_response_data):

    # Mock the response from the reranking service
    mock_post.return_value.json.return_value = mock_response_data
    mock_post.return_value.raise_for_status.return_value = None

    # Call the method being tested
    result = test_class.run(mock_input_data)

    mock_post.assert_called_once_with(
        test_class._service_endpoint + "/rerank",
        data='{"query": "This is my sample query?", "texts": ["Document 1", "Document 2", "Document 3"]}',
        headers={"Content-Type": "application/json"},
    )

    # Assert that result.query is not empty
    assert result.query, "Query is empty"

    # Use the template to create the expected result. It shall contain only text "Document 2"
    # which is under index=1 since it has the highest score
    expected_result_query = expected_result_template.format("Document 2")
    assert (
        result.query == expected_result_query
    ), "The result query should include only the document with the highest score"


@patch("comps.reranks.utils.opea_reranking.requests.post")
def test_run_returns_all_docs_when_server_unavailable(mock_post, test_class, mock_input_data):
    # Simulate server being unavailable
    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")
    mock_post.return_value.json.return_value = None

    with pytest.raises(requests.exceptions.RequestException):
        test_class.run(mock_input_data)


@patch("comps.reranks.utils.opea_reranking.requests.post")
def test_call_reranker_raises_exception_when_server_is_unavailable(mock_post, test_class, mock_input_data):
    initial_query = mock_input_data.initial_query
    retrieved_docs = [doc.text for doc in mock_input_data.retrieved_docs]

    # Simulate server unavailability
    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")

    # Ensure HTTPError is raised when reranker is called
    with pytest.raises(requests.exceptions.RequestException):
        test_class._call_reranker(initial_query, retrieved_docs)

    assert mock_post.call_count == 1
    mock_post.assert_called_with(
        test_class._service_endpoint + "/rerank",
        data='{"query": "This is my sample query?", "texts": ["Document 1", "Document 2", "Document 3"]}',
        headers={"Content-Type": "application/json"},
    )


def test_run_raises_exception_on_empty_initial_query(test_class):
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
        test_class.run(input_data)

    assert str(context.value) == "Initial query cannot be empty."


@patch("comps.reranks.utils.opea_reranking.requests.post")
def test_run_raises_exception_on_top_N_below_one(mock_post, test_class):
    input_data = SearchedDoc(
        initial_query="This is my sample query?",
        retrieved_docs=[
            TextDoc(text="Document 1"),
            TextDoc(text="Document 2"),
            TextDoc(text="Document 3"),
        ],
        top_n=0,
    )

    with pytest.raises(ValueError) as context:
        test_class.run(input_data)

    # Invalid query shouldn't be sent to the reranking service, so `post` shouldn't be called."
    mock_post.assert_not_called()

    assert str(context.value) == "Top N value must be greater than 0, but it is 0"
