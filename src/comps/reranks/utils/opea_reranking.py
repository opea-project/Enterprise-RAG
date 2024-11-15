# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import heapq
import json
from typing import List, TypedDict

import requests
from docarray import DocList
from requests.exceptions import RequestException

from comps import (
    LLMParamsDoc,
    SearchedDoc,
    TextDoc,
    get_opea_logger,
)
from comps.reranks.utils import prompt


class RerankScoreItem(TypedDict):
    index: int
    score: float

RerankScoreResponse = List[RerankScoreItem]

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class OPEAReranker:
    def __init__(self, service_endpoint: str):
        """
         Initialize the OPEAReranker instance with the given parameter
        Sets up the reranker.

        Args:
            :param service_endpoint: the URL of the reranking service (e.g. TEI Ranker)

        Raises:
            ValueError: If the required param is missing or empty.
        """

        self._service_endpoint = service_endpoint
        self._validate_config()

        self._validate()

        logger.info(
            f"Reranker model server is configured to send requests to service {self._service_endpoint}"
        )

    def _validate_config(self):
        """Validate the configuration values."""
        try:
            if not self._service_endpoint:
                raise ValueError("The 'RERANKING_SERVICE_ENDPOINT' cannot be empty.")
        except Exception as err:
            logger.error(f"Configuration validation error: {err}")
            raise

    def _validate(self):
        initial_query = "What is DL?"
        retrieved_docs = ["DL is not...", "DL is..."]
        _ = self._call_reranker(initial_query, retrieved_docs)
        logger.info("Reranker service is reachable and working.")

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
        # Although unlikely, ensure that 'initial_query' is provided and not empty before proceeding.
        if not input.initial_query.strip():
            logger.error("No initial query provided.")
            raise ValueError("Initial query cannot be empty.")

        if input.top_n < 1:
            logger.error(f"Top N value must be greater than 0, but it is {input.top_n}")
            raise ValueError(f"Top N value must be greater than 0, but it is {input.top_n}")

        # Check if retrieved_docs is not empty and all documents have non-empty 'text' fields
        if input.retrieved_docs and all(doc.text for doc in input.retrieved_docs):
            # Proceed with processing the retrieved documents
            try:
                retrieved_docs = [doc.text for doc in input.retrieved_docs]
                response_data = self._call_reranker(
                    input.initial_query, retrieved_docs
                )
                best_response_list = self._filter_top_n(input.top_n, response_data)
            except RequestException as e:
                logger.error(f"Connection Error during request to reranking service: {e}")
                raise RequestException(f"Connection Error during request to reranking service: {e}")
            except Exception as e:
                logger.error(f"Error during request to reranking service: {e}")
                raise Exception(f"Error during request to reranking service: {e}")

            query = self._generate_query(
                input.initial_query, input.retrieved_docs, best_response_list, prompt
            )
        else:
            logger.warning("No retrieved documents found. Using the initial query.")
            query = self._generate_query(
                input.initial_query
            )

        return LLMParamsDoc(query=query)


    def _call_reranker(
        self,
        initial_query: str,
        retrieved_docs: List[str],
    ) -> RerankScoreResponse:
        """
        Calls the reranker service to rerank the retrieved documents based on the initial query.
        Args:
            initial_query (str): The initial query string.
            retrieved_docs (List[str]): The list of retrieved documents.
        Returns:
            RerankScoreResponse: The response from the reranker service.
        Raises:
            requests.exceptions.RequestException: If failed to reach the service after the maximum number of attempts.
        """

        data = {"query": initial_query, "texts": retrieved_docs}

        try:
            response = requests.post(
                self._service_endpoint + "/rerank",
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()  # Raises a HTTPError if the response status is 4xx, 5xx
            return response.json()

        except RequestException as e:
            error_code = e.response.status_code if e.response else 'No response'
            error_message = f"Failed to send request to reranking service. Unable to connect to '{self._service_endpoint}', status_code: {error_code}. Check if the service url is reachable."
            logger.error(error_message)
            raise RequestException(error_message)
        except Exception as e:
            logger.error(f"An error occurred while requesting to the reranking service: {e}")
            raise Exception(f"An error occurred while requesting to the reranking service: {e}")


    def _generate_query(
        self,
        initial_query: str,
        retrieved_docs: DocList[TextDoc] = None,
        best_response_list: RerankScoreResponse = None,
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
        if not best_response_list and retrieved_docs:
            for doc in retrieved_docs:
                context_str += " " + doc.text
            final_prompt = prompt_generator.get_prompt(initial_query, context_str)
        elif best_response_list and retrieved_docs:
            ## Using only best responses
            for best_response in best_response_list:
                context_str += " " + retrieved_docs[best_response["index"]].text
            final_prompt = prompt_generator.get_prompt(initial_query, context_str)
        else:
            logger.debug("No retrieved documents. Context will be empty.")
            final_prompt = prompt_generator.get_prompt(initial_query)

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
