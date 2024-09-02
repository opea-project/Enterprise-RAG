import unittest
from unittest.mock import MagicMock, patch

import requests

from comps import (
    SearchedDoc,
    TextDoc,
)
from comps.reranks.utils import opea_reranking

default_config = "comps/reranks/config.ini"

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


class TestOPEARerankerSetup(unittest.TestCase):
    def test_init_with_defaults(self):
        """
        Test the setup method of the OPEAReranker class with default configuration.

        This test verifies that the setup method correctly initializes the attributes
        of the OPEAReranker class when provided with default configuration.

        Args:
            self: The test case instance.

        Raises:
            AssertionError: If any of the assertions fail.

        Returns:
            None
        """
        try:
            self.test_class = opea_reranking.OPEAReranker(default_config)
        except Exception as e:
            self.fail(f"OPEAReranker init raised {type(e)} unexpectedly!")

        assert (
            isinstance(self.test_class.name, str) and self.test_class.name
        ), "The name is expected to be a non-empty string"
        assert (
            isinstance(self.test_class.host, str) and self.test_class.host
        ), "The host is expected to be a non-empty string"
        assert isinstance(
            self.test_class.port, int
        ), "The port is expected to be an integer"
        assert (
            isinstance(self.test_class.service_url, str) and self.test_class.service_url
        ), "The service_url is expected to be a non-empty string"

    def test_init_with_invalid_path_to_config(self):
        nonexistent_config_file = (
            "/path/not/exists/config.ini"  # Nonexistent config file
        )

        with self.assertRaises(FileNotFoundError) as context:
            opea_reranking.OPEAReranker(nonexistent_config_file)

        assert str(context.exception).startswith(
            f"The configuration file {nonexistent_config_file} does not exist"
        )

    @patch.dict(
        "os.environ",
        {
            "RERANKING_NAME": "test_name_env",
            "RERANKING_HOST": "test_host_env",
            "RERANKING_PORT": "8001",
            "RERANKING_SERVICE_URL": "test_url_env:6061/api/v2",
        },
    )

    def test_init_with_env_vars(self):
        """
        Test case to verify the setup method when environment variables are used.

        This test case checks if the attributes of the test_class object are correctly set
        from the environment variables.

        Returns:
            None
        """
        self.test_class = opea_reranking.OPEAReranker(default_config)
        # Check if the attributes were correctly set from the environment variables
        assert (
            self.test_class.name == "test_name_env"
        ), "Name should be taken from env variable"
        assert (
            self.test_class.host == "test_host_env"
        ), "Host should be taken from env variable"
        assert (
            int(self.test_class.port) == 8001
        ), "Port should be taken from env variable"
        assert (
            self.test_class.service_url == "test_url_env:6061/api/v2"
        ), "Service URL should be taken from env variable"


class TestOPEARerankerValidateConfig(unittest.TestCase):
    def test_validate_config(self):
        """
        Test case for validating the configuration settings.

        This method tests the `_validate_config` method of the class. It verifies that the configuration settings are
        validated correctly and that the appropriate exceptions are raised when required fields are missing or have
        invalid values.

        """
        self.test_class = opea_reranking.OPEAReranker.__new__(
            opea_reranking.OPEAReranker
        )
        # overwrite with mock data for testing
        self.test_class.name = "test_name"
        self.test_class.host = "test_host"
        self.test_class.port = 1234
        self.test_class.service_url = "test_url:6060/api"

        # when all config values are provided correctly
        try:
            self.test_class._validate_config()
        except Exception as e:
            self.fail(f"_validate_config raised {type(e)} unexpectedly!")

        # when missing name
        self.test_class.name = None
        with self.assertRaises(ValueError) as context:
            self.test_class._validate_config()
        assert str(context.exception) == "The 'name' cannot be empty."

        # when missing host
        self.test_class.name = "test_name"
        self.test_class.host = None
        with self.assertRaises(ValueError) as context:
            self.test_class._validate_config()
        assert str(context.exception) == "The 'host' cannot be empty."

        # when missing port
        self.test_class.host = "test_host"
        self.test_class.port = None
        with self.assertRaises(ValueError) as context:
            self.test_class._validate_config()
        assert str(context.exception) == "The 'port' is required."

        # when missing service_url
        self.test_class.port = 1234
        self.test_class.service_url = None
        with self.assertRaises(ValueError) as context:
            self.test_class._validate_config()
        assert str(context.exception) == "The 'service_url' cannot be empty."

        self.test_class.service_url = "test_url:6060/api"


@patch.dict(
    "comps.reranks.utils.opea_reranking.statistics_dict",
    {"opea_service@reranking": MagicMock()},
    clear=False,
)
class TestOPEARerankerRun(unittest.TestCase):
    """
    Test case for the `run` method of the `OPEAReranker` class.

    Methods:
    - `test_run_successful_execution`: Tests the successful execution of the `run` method.
    - `test_run_execution_when_server_unavailable`: Tests execution when the Ranker Model-Server is unavailable. All documents should be returned in the final query due to unavailable scores.
    - `test_run_call_reranker_when_server_is_unavailable`: Extends the previous test, focusing on the `call_reranker` method with additional assertion checks.
    - `test_run_execution_with_empty_retrieved_docs`: Tests execution when retrieved documents are empty. Expected outcome: the initial query is returned as the final query.
    - `test_run_execution_with_invalid_retrieved_docs`: Tests execution in case when all retrieved_docs have empty 'text' field. Expected outcome: the initial query is returned as the final query.
    - `test_run_execution_with_empty_query`: Tests that an empty query raises a `ValueError` to stop the pipeline.
    """

    def setUp(self):
        self.test_class = opea_reranking.OPEAReranker(default_config)
        self.mock_input_data = SearchedDoc(
            initial_query="This is my sample query?",
            retrieved_docs=[
                TextDoc(text="Document 1"),
                TextDoc(text="Document 2"),
                TextDoc(text="Document 3"),
            ],
            top_n=1,
        )
        self.mock_response_data = [
            {"index": 1, "score": 0.9988041},
            {"index": 0, "score": 0.02294873},
            {"index": 2, "score": 0.5294873},
        ]

    # positive
    @patch("comps.reranks.utils.opea_reranking.requests.post")
    def test_run_successful_execution(self, mock_post):
        input_data = self.mock_input_data
        response_data = self.mock_response_data

        # Mock the response from the reranking service
        mock_post.return_value.json.return_value = response_data
        mock_post.return_value.raise_for_status.return_value = None

        # Call the method being tested
        result = self.test_class.run(input_data)

        mock_post.assert_called_once_with(
            self.test_class.service_url,
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

    # negative 1a
    @patch("comps.reranks.utils.opea_reranking.requests.post")
    def test_run_execution_when_server_unavailable(self, mock_post):
        input_data = self.mock_input_data

        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("404 Client Error: Not Found")
        )
        mock_post.return_value.json.return_value = None
        mock_post.return_value.raise_for_status.return_value = None

        try:
            # Call the method being tested
            result = self.test_class.run(input_data)
        except Exception as e:
            self.fail(f"Run raised {type(e)} unexpectedly!")

        # Assert that result.query is not empty
        assert result.query, "Query is empty"

        # All documents should be in the query since the reranking scores are not available
        expected_result_query = expected_result_template.format(
            "Document 1 Document 2 Document 3"
        )
        assert result.query == expected_result_query

    # negative 1b
    @patch("comps.reranks.utils.opea_reranking.requests.post")
    def test_run_call_reranker_when_server_is_unavailable(self, mock_post):
        # the test includes additional assert checks specific for _call_reranker method

        # Define the input parameters
        initial_query = self.mock_input_data.initial_query
        retrieved_docs = self.mock_input_data.retrieved_docs

        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("404 Client Error: Not Found")
        )
        mock_post.return_value.json.return_value = None
        mock_post.return_value.raise_for_status.return_value = None

        # Call the tested method and assert it raises an HTTPError
        with self.assertRaises(requests.exceptions.RequestException):
            self.test_class._call_reranker(initial_query, retrieved_docs)

        # Assert that requests.post was called 3 times with the correct arguments
        self.assertEqual(mock_post.call_count, 3)
        mock_post.assert_called_with(
            self.test_class.service_url,
            data='{"query": "This is my sample query?", "texts": ["Document 1", "Document 2", "Document 3"]}',
            headers={"Content-Type": "application/json"},
        )

    # negative 2
    def test_run_execution_with_empty_retrieved_docs(self):
        input_data = SearchedDoc(
            initial_query="This is my sample query?", retrieved_docs=[], top_n=1
        )

        # Call the method being tested
        result = self.test_class.run(input_data)

        # Assert that result.query is not empty
        assert result.query, "Query is empty"
        # Assert that the query is equal to the initial query since there are no retrieved docs
        assert (
            result.query == input_data.initial_query.strip()
        ), "Query is not equal to initial query"

    # negative 3
    def test_run_execution_with_invalid_retrieved_docs(self):
        input_data = SearchedDoc(
            initial_query="This is my sample query?",
            retrieved_docs=[
                TextDoc(text=""),  # empty text
                TextDoc(text="  "),  # tab
                TextDoc(text="  "),  # two spaces
            ],
            top_n=1,
        )

        # Call the method being tested
        result = self.test_class.run(input_data)

        # Assert that result.query is not empty
        assert result.query, "Query is empty"
        # Assert that the query is equal to the initial query since there are no retrieved docs
        assert (
            result.query == input_data.initial_query.strip()
        ), "Query is not equal to initial query"

    # negative 4
    def test_run_execution_with_empty_query(self):
        input_data = SearchedDoc(
            initial_query="",
            retrieved_docs=[
                TextDoc(text="Document 1"),
                TextDoc(text="Document 2"),
                TextDoc(text="Document 3"),
            ],
            top_n=1,
        )

        # Call the method being tested and assert it raises an ValueError
        with self.assertRaises(ValueError):
            self.test_class.run(input_data)


class TestFilterTopN(unittest.TestCase):
    def setUp(self):
        self.test_class = opea_reranking.OPEAReranker.__new__(
            opea_reranking.OPEAReranker
        )

    def test_filter_top_n(self):
        test_data = [
            {"score": 1, "other_key": "a"},
            {"score": 3, "other_key": "b"},
            {"score": 2, "other_key": "c"},
            {"score": 5, "other_key": "d"},
            {"score": 4, "other_key": "e"},
        ]
        result = self.test_class._filter_top_n(3, test_data)
        expected_result = [
            {"score": 5, "other_key": "d"},
            {"score": 4, "other_key": "e"},
            {"score": 3, "other_key": "b"},
        ]
        self.assertEqual(
            result, expected_result, "Should return top 3 items based on score"
        )

        # Test with top 1
        result = self.test_class._filter_top_n(1, test_data)
        expected_result = [{"score": 5, "other_key": "d"}]
        self.assertEqual(
            result, expected_result, "Should return top 1 item based on score"
        )

        # Test with top 6. Extected all items to be returned
        result = self.test_class._filter_top_n(6, test_data)
        expected_result = [
            {"score": 5, "other_key": "d"},
            {"score": 4, "other_key": "e"},
            {"score": 3, "other_key": "b"},
            {"score": 2, "other_key": "c"},
            {"score": 1, "other_key": "a"},
        ]
        self.assertEqual(
            result,
            expected_result,
            "All items should be returned because 6 is greater than the length of test_data",
        )


class TestSanitizeConfiguration(unittest.TestCase):
    def test_sanitize(self):
        # Test with a string that has quotes at the start and end
        value = '"test_string"'
        result = opea_reranking._sanitize(value)
        self.assertEqual(result, "test_string", "Quotes should be removed")

        # Test with a string that does not have quotes at the start and end
        value = "test_string"
        result = opea_reranking._sanitize(value)
        self.assertEqual(result, "test_string", "String should be unchanged")

        # Test with a string that has only one quote at the start
        value = '"test_string'
        result = opea_reranking._sanitize(value)
        self.assertEqual(result, '"test_string', "String should be unchanged")

        # Test with a string that has only one quote at the end
        value = 'test_string"'
        result = opea_reranking._sanitize(value)
        self.assertEqual(result, 'test_string"', "String should be unchanged")


if __name__ == "__main__":
    unittest.main()
