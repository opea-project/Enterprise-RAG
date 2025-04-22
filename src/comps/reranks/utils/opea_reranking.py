# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
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

SUPPORTED_MODEL_SERVERS = ["torchserve", "tei"]

class OPEAReranker:
    def __init__(self, service_endpoint: str, model_server: str):
        """
         Initialize the OPEAReranker instance with the given parameter
        Sets up the reranker.

        Args:
            :param service_endpoint: the URL of the reranking service (e.g. TEI)

        Raises:
            ValueError: If the required param is missing or empty.
        """

        self._service_endpoint = service_endpoint
        self._model_server = model_server.lower()
        self._validate_config()

        if self._model_server == "torchserve":
            model_name = self._retrieve_torchserve_model_name()
            self._service_endpoint = self._service_endpoint + f"/predictions/{model_name}"
        elif self._model_server == "tei":
            self._service_endpoint = self._service_endpoint + "/rerank"

        self._validate()

        logger.info(
            f"Reranker model server is configured to send requests to service {self._service_endpoint}"
        )

    def _validate_config(self):
        """Validate the configuration values."""
        if not self._service_endpoint:
            raise ValueError("The 'RERANKING_SERVICE_ENDPOINT' cannot be empty.")

        if self._model_server not in SUPPORTED_MODEL_SERVERS:
            raise ValueError(f"Unsupported model server: {self._model_server}. Supported model servers: {SUPPORTED_MODEL_SERVERS}")

    def _validate(self):
        initial_query = "What is DL?"
        retrieved_docs = ["DL is not...", "DL is..."]
        asyncio.run(self._async_call_reranker(initial_query, retrieved_docs))
        logger.info("Reranker service is reachable and working.")

    def _retrieve_torchserve_model_name(self):
        try:
            mgnt_port = int(self._service_endpoint.split(":")[-1]) + 1
            mgnt_service_endpoint = ":".join(self._service_endpoint.split(":")[:-1]) + ":" + str(mgnt_port) + "/models"

            response = requests.get(mgnt_service_endpoint, timeout=20)
            response.raise_for_status()

            # FIXME: Attention! The code assumes only 1 model is registered in Torchserve.
            # Should be changed if Torchserve implementation would be modified.
            return response.json()["models"][0]["modelName"]
        except Exception as e:
            err_msg = f"An error occurred while retrieving the model name from the Torchserve: {e}. " \
                f"Check if management port is correct. Assumed management endpoint: {mgnt_service_endpoint}"
            logger.error(err_msg)
            raise Exception(err_msg)

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

        # Check if retrieved_docs is not empty and all documents have non-empty 'text' fields
        if input.retrieved_docs and all(doc.text for doc in input.retrieved_docs):
            # Proceed with processing the retrieved documents
            try:
                retrieved_docs = [doc.text for doc in input.retrieved_docs]
                response_data = await self._async_call_reranker(
                    input.initial_query, retrieved_docs
                )
                logger.debug(f"Received response from reranking service: {response_data}")
                best_response_list = self._filter_top_n(input.top_n, response_data, score_threshold=input.rerank_score_threshold)
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

            if not response_data:
                logger.warning("No best responses found. Using all retrieved documents.")
                reranked_docs = input.retrieved_docs
            else:
                reranked_docs = [input.retrieved_docs[best_response["index"]] for best_response in best_response_list]
        else:
            logger.warning("No retrieved documents found")
            reranked_docs = []

        cleaned_reranked_docs = [doc.text for doc in reranked_docs]
        return PromptTemplateInput(data={"initial_query": input.initial_query.strip(), "reranked_docs": cleaned_reranked_docs})


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
                    self._service_endpoint,
                    data=json.dumps(data),
                    headers={"Content-Type": "application/json"},
                    timeout=180
                ) as response:
                    response_data = await response.json(content_type=None)
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

    def _filter_top_n(self, top_n: int, data: RerankScoreResponse, score_threshold: float=None) -> RerankScoreResponse:
        """
        Filter and return the top N responses based on their scores.

        Args:
            top_n (int): The number of top responses to filter.
            data (List[Dict[str, float]]): The list of responses with their scores.

        Returns:
            List[Dict[str, float]]: The filtered list of top responses.

        """
        top_n_outputs = heapq.nlargest(top_n, data, key=lambda x: x["score"])
        if score_threshold is not None:
            out = [s for s in top_n_outputs if s["score"] > score_threshold]
            return out
        return top_n_outputs
