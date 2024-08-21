import configparser
import heapq
import json
import logging
import os
import sys
import time
from typing import List, TypedDict

import requests
from comps import (
    LLMParamsDoc,
    SearchedDoc,
    TextDoc,
    statistics_dict,
)
from comps.reranks.utils import prompt
from docarray import DocList


class RerankScoreItem(TypedDict):
    index: int
    score: float

RerankScoreResponse = List[RerankScoreItem]


class OPEAReranker:
    def __init__(self, config_file: str):
        """
        Sets up the reranker.

        Args:
            config_file (str): The path to the configuration file.

        # Environment variables can override the configuration file settings
        # - RERANKING_SERVICE_URL: Overrides the URL of the reranking service (e.g. TEI Ranker)
        # - RERANKING_HOST: Overrides the host of the microservice
        # - RERANKING_PORT: Overrides the port of the microservice
        # - RERANKING_NAME: Overrides the name of the microservice
        # - RERANKING_LOG_LEVEL: Overrides the log level
        # - RERANKING_LOG_PATH: Overrides the log path
        """
        self.config_file = config_file
        self.name = str
        self.host = str
        self.port = int
        self.service_url: str
        self.log_level: str
        self.log_path: str
        self.logger: logging.Logger

        self._load_config()
        self._setup_logging()
        self._validate_config()
        self.logger.info(
            f"Reranker has been successfully initialized and is running on {self.host}:{self.port}"
        )
        self.logger.info(
            f"Reranker is configured to send requests to service {self.service_url}"
        )

    def _load_config(self):
        """
        Loads the configuration from the specified config file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """

        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"The configuration file {self.config_file} does not exist"
            )

        config = configparser.ConfigParser()
        config.read(self.config_file)

        # base configuration
        self.name = os.getenv(
            "RERANKING_NAME", _sanitize(config.get("OPEA_Microservice", "name"))
        )
        self.host = os.getenv(
            "RERANKING_HOST", _sanitize(config.get("OPEA_Microservice", "host"))
        )
        self.port = os.getenv(
            "RERANKING_PORT", config.getint("OPEA_Microservice", "port")
        )
        self.service_url = os.getenv(
            "RERANKING_SERVICE_URL", _sanitize(config.get("Service", "url"))
        )
        # logging
        self.log_level = os.getenv(
            "RERANKING_LOG_LEVEL", config.get("Logging", "log_level")
        )
        self.log_path = os.getenv(
            "RERANKING_LOG_PATH", config.get("Logging", "log_path")
        )

    def _setup_logging(self):
        """Configure the logger based on the log level and log path."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        log_dir = os.path.dirname(self.log_path)
        try:
            # ensure the log directory exists and is writable
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            elif not os.access(log_dir, os.W_OK):
                raise PermissionError(
                    f"No write permission for the directory '{log_dir}'"
                )
        except (PermissionError, OSError) as e:
            print(f"Failed to create or access the directory '{log_dir}': {e}")
            raise PermissionError(
                f"Failed to create or access the directory '{log_dir}': {e}"
            )

        # Define the log format string
        log_format = "[%(asctime)-15s] [%(levelname)8s] [%(name)s] - %(message)s"

        # Basic logging configuration
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        # Get the logger instance for this class
        self.logger = logging.getLogger(self.name)

        # Create a file handler
        file_handler = logging.FileHandler(self.log_path)
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)

    def _validate_config(self):
        """Validate the configuration values."""
        try:
            if not self.name:
                raise ValueError("The 'name' cannot be empty.")
            if not self.host:
                raise ValueError("The 'host' cannot be empty.")
            if not self.port:
                raise ValueError("The 'port' is required.")
            if not self.service_url:
                raise ValueError("The 'service_url' cannot be empty.")
            if self.log_level.upper() not in logging._nameToLevel:
                raise ValueError(
                    f"The 'log_level' must be one of {list(logging._nameToLevel.keys())}."
                )

        except Exception as err:
            self.logger.error(f"Configuration validation error: {err}")
            raise

    def run(self, input: SearchedDoc) -> LLMParamsDoc:
        """
        Runs the reranking process based on the given input.

        Args:
            input (SearchedDoc): The input document containing the initial query and retrieved documents.

        Returns:
            LLMParamsDoc: The reranked query.

        Raises:
            Exception: If there is an error during the reranking process.
        """
        start = time.time()

        # Although unlikely, ensure that 'initial_query' is provided and not empty before proceeding.
        if not input.initial_query.strip():
            self.logger.error("No initial query provided.")
            raise ValueError("Initial query cannot be empty.")

        # Check if retrieved_docs is not empty and all documents have non-empty 'text' fields
        if input.retrieved_docs and all(doc.text for doc in input.retrieved_docs):
            # Proceed with processing the retrieved documents
            try:
                response_data = self._call_reranker(
                    input.initial_query, input.retrieved_docs
                )
                best_response_list = self._filter_top_n(input.top_n, response_data)
            except Exception as e:
                best_response_list = [] # Set to empty if no scores are available.
                self.logger.error(f"Error during request to reranking service: {e}")
                self.logger.warning(
                    "No scores available to select top documents. Proceeding with all retrieved documents by default."
                )
                
            query = self._generate_query(
                input.initial_query, input.retrieved_docs, best_response_list, prompt
            )

        else:
            self.logger.warning(
                "No retrieved documents found. Using the initial query."
            )
            query = input.initial_query.strip() # Just pass the initial query to the LLM

        latency_sec = time.time() - start
        self.logger.debug(f"Operation latency: {latency_sec} seconds")
        statistics_dict[self.name].append_latency(latency_sec, None)
        return LLMParamsDoc(query=query)

    def _call_reranker(
        self,
        initial_query: str,
        retrieved_docs: DocList[TextDoc],
        max_attempts: int = 3,
    ) -> RerankScoreResponse:
        """
        Calls the reranker service to rerank the retrieved documents based on the initial query.
        Args:
            initial_query (str): The initial query string.
            retrieved_docs (DocList[TextDoc]): The list of retrieved documents.
            max_attempts (int, optional): The maximum number of attempts to reach the service. Defaults to 3.
        Returns:
            RerankScoreResponse: The response from the reranker service.
        Raises:
            requests.exceptions.RequestException: If failed to reach the service after the maximum number of attempts.
        """

        docs = [doc.text for doc in retrieved_docs]
        data = {"query": initial_query, "texts": docs}

        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    self.service_url,
                    data=json.dumps(data),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()  # Raises a HTTPError if the response status is 4xx, 5xx
                return response.json()
            except requests.exceptions.RequestException as e:
                self.logger.error(
                    f"Error during request to the service (attempt {attempt + 1}): {e}"
                )
                time.sleep(3)  # Wait for 3 second before the next attempt

        raise requests.exceptions.RequestException(
            f"Failed {max_attempts} times to reach {self.service_url}."
        )

    def _generate_query(
        self,
        initial_query: str,
        retrieved_docs: DocList[TextDoc],
        best_response_list: RerankScoreResponse,
        prompt_generator=prompt,
    ) -> str:
        """
        Generates a final prompt. This function utilizes documents scored as best responsens for prompt generation. If the scoring is missed, it uses all retrieved documents.

        Args:
            initial_query (str): The initial query string.
            retrieved_docs (DocList[TextDoc]): The list of retrieved documents.
            best_response_list (List[RerankedResponse]): The list of best responses identified by 'index'.
            prompt_generator (function, optional): The prompt generator function. Defaults to prompt.

        Returns:
            str: The final prompt for the query.
        """
        context_str = ""
        if not best_response_list:
            for doc in retrieved_docs:
                context_str += " " + doc.text
        else:
            ## Using only best responses
            for best_response in best_response_list:
                context_str += " " + retrieved_docs[best_response["index"]].text

        final_prompt = prompt_generator.get_prompt(context_str, initial_query)
        return final_prompt


    def _filter_top_n(self, top_n: int, data: RerankScoreResponse) -> RerankScoreResponse:
        """
        Filter and return the top N responses based on their scores.

        Args:
            top_n (int): The number of top responses to filter.
            data (List[Dict[str, float]]): The list of responses with their scores.

        Returns:
            List[Dict[str, float]]: The filtered list of top responses.

        """
        return heapq.nlargest(top_n, data, key=lambda x: x["score"])


def _sanitize(value: str) -> str:
    """Remove quotes from a configuration value if present.

    Args:
        value (str): The configuration value to sanitize.

    Returns:
        str: The sanitized configuration value.

    """
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value
