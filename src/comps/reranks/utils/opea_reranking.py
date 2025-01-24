# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import heapq
import json
import requests
from typing import List, TypedDict
import aiohttp

from asyncio import TimeoutError
from aiohttp.client_exceptions import ClientResponseError
from requests.exceptions import HTTPError, RequestException, Timeout

from comps import (
    SearchedDoc,
    PromptTemplateInput,
    get_opea_logger,
)

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

    async def run(self, input: SearchedDoc) -> PromptTemplateInput:
        """
        Asynchronously runs the reranking process based on the given input.
        Args:
            input (SearchedDoc): The input document containing the initial query and retrieved documents.
        Returns:
            PromptTemplateInput: The output document after reranking processing, cointaining the initial query and reranked documents.
        Raises:
            ValueError: If the initial query is empty or if top_n is less than 1.
            RequestException: If there is a connection error during the request to the reranking service.
            Exception: If there is any other error during the request to the reranking service.
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
                response_data = await self._async_call_reranker(
                    input.initial_query, retrieved_docs
                )
                best_response_list = self._filter_top_n(input.top_n, response_data)
            except TimeoutError as e:
                raise TimeoutError(e)
            except Timeout as e:
                raise Timeout(e)
            except RequestException as e:
                raise RequestException(e)
            except HTTPError as e:
                raise HTTPError(e)
            except ClientResponseError:
                raise
            except Exception as e:
                logger.error(f"Error during request to reranking service: {e}")
                raise Exception(f"Error during request to reranking service: {e}")

            if not best_response_list:
                logger.warning("No best responses found. Using all retrieved documents.")
                reranked_docs = input.retrieved_docs
            else:
                reranked_docs = [input.retrieved_docs[best_response["index"]] for best_response in best_response_list]
        else:
            logger.warning("No retrieved documents found")
            reranked_docs = []

        return PromptTemplateInput(data={"initial_query": input.initial_query.strip(), "reranked_docs": reranked_docs})


    async def _async_call_reranker(
        self,
        initial_query: str,
        retrieved_docs: List[str],
    ) -> RerankScoreResponse:
        """
        Async calls the reranker service to rerank the retrieved documents based on the initial query.
        Args:
            initial_query (str): The initial query string.
            retrieved_docs (List[str]): The list of retrieved documents.
        Returns:
            RerankScoreResponse: The response from the reranker service.
        Raises:
            Timeout: If the request to the reranking service times out.
            RequestException: If there is an issue with the request to the reranking service.
            Exception: For any other exceptions that occur during the request.
        """

        data = {"query": initial_query, "texts": retrieved_docs}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._service_endpoint + "/rerank",
                    data=json.dumps(data),
                    headers={"Content-Type": "application/json"},
                    timeout=180
                ) as response:
                    response_data = await response.json()
                    response.raise_for_status()  # Raises a HTTPError if the response status is 4xx, 5xx
                    return response_data

        except TimeoutError:
            error_message = f"Request to reranking service timed out. Check if the service is running and reachable at '{self._service_endpoint}'."
            logger.error(error_message)
            raise TimeoutError(error_message)
        except RequestException as e:
            error_code = e.response.status_code if e.response else 'No response'
            error_message = f"Failed to send request to reranking service. Unable to connect to '{self._service_endpoint}', status_code: {error_code}. Check if the service url is reachable."
            logger.error(error_message)
            raise RequestException(error_message)
        except ClientResponseError as e:
            logger.error(f"A ClientResponseError error occurred while sending a request to the reranking service: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while requesting to the reranking service: {e}")
            raise Exception(f"An error occurred while requesting to the reranking service: {e}")

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
            Timeout: If the request to the reranking service times out.
            RequestException: If there is an issue with the request to the reranking service.
            Exception: For any other exceptions that occur during the request.
        """

        data = {"query": initial_query, "texts": retrieved_docs}

        try:
            response = requests.post(self._service_endpoint + "/rerank",
                                     data=json.dumps(data),
                                     headers={"Content-Type": "application/json"},
                                     timeout=180)
            response.raise_for_status()  # Raises a HTTPError if the response status is 4xx, 5xx
            return response.json()
        except Timeout:
            error_message = f"Request to reranking service timed out. Check if the service is running and reachable at '{self._service_endpoint}'."
            logger.error(error_message)
            raise Timeout(error_message)
        except HTTPError as e:
            logger.error(f"A HTTPError error occurred while requesting to the reranking service: {e}")
            raise HTTPError(e)
        except RequestException as e:
            error_code = e.response.status_code if e.response else 'No response'
            error_message = f"Failed to send request to reranking service. Unable to connect to '{self._service_endpoint}', status_code: {error_code}. Check if the service url is reachable."
            logger.error(error_message)
            raise RequestException(error_message)
        except Exception as e:
            logger.error(f"An error occurred while requesting to the reranking service: {e}")
            raise Exception(f"An error occurred while requesting to the reranking service: {e}")

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
