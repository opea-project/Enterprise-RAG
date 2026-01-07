# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import heapq
import json
from docarray import DocList
from typing import List, TypedDict, Dict
import aiohttp

from asyncio import TimeoutError
from aiohttp.client_exceptions import ClientResponseError
from requests.exceptions import HTTPError, RequestException, Timeout

from comps import (
    SearchedDoc,
    TextDoc,
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
    def __init__(self, service_endpoint: str, model_server: str, model_name: str = None, late_chunking_enabled: bool = True):
        """
         Initialize the OPEAReranker instance with the given parameter
        Sets up the reranker.

        Args:
            :param service_endpoint: the URL of the reranking service (e.g. TEI)
            :param model_server: the model server type (e.g., 'torchserve', 'tei')
            :param model_name: the model name (required for torchserve)
            :param late_chunking_enabled: if True, bypass reranker and use vector distances

        Raises:
            ValueError: If the required param is missing or empty.
        """

        self._service_endpoint = service_endpoint
        self._model_server = model_server.lower()
        self.late_chunking_enabled = late_chunking_enabled
        self._validate_config()

        if not self.late_chunking_enabled:
            if self._model_server == "torchserve":
                if not model_name:
                    raise ValueError("The 'RERANKING_MODEL_NAME' cannot be empty when using 'torchserve' as the model server.")
                self._service_endpoint = self._service_endpoint + f"/predictions/{model_name.split('/')[-1]}"
            elif self._model_server == "tei":
                self._service_endpoint = self._service_endpoint + "/rerank"

        self._validate()

        logger.info(
            f"Reranker model server is configured to send requests to service {self._service_endpoint}"
        )

    def _validate_config(self):
        """Validate the configuration values."""
        if not self.late_chunking_enabled:
            if not self._service_endpoint:
                raise ValueError("The 'RERANKING_SERVICE_ENDPOINT' cannot be empty.")

        if self._model_server not in SUPPORTED_MODEL_SERVERS:
            raise ValueError(f"Unsupported model server: {self._model_server}. Supported model servers: {SUPPORTED_MODEL_SERVERS}")

    def _validate(self):
        if self.late_chunking_enabled:
            logger.info("Late chunking enabled. Skipping reranker service validation.")
            return
        
        initial_query = "What is DL?"
        retrieved_docs = ["DL is not...", "DL is..."]
        asyncio.run(self._async_call_reranker(initial_query, retrieved_docs))
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

        # Although unlikely, ensure that 'user_prompt' is provided and not empty before proceeding.

        if not input.user_prompt.strip():
            logger.error("No initial query provided.")
            raise ValueError("Initial query cannot be empty.")

        # Check if retrieved_docs is not empty and all documents have non-empty 'text' fields
        if input.retrieved_docs and all(doc.text for doc in input.retrieved_docs):
            # If late chunking is enabled, bypass reranker and use vector distances
            if self.late_chunking_enabled:
                logger.info("Late chunking enabled. Using vector distances for filtering instead of reranker.")
                logger.info(f"Retrieved documents: {input.retrieved_docs}")
                reranked_docs = self._filter_top_n_by_vector_distance(
                    input.retrieved_docs, 
                    input.top_n
                )
                logger.info(f"Filtered documents by vector distance: {reranked_docs}")
            else:
                # Proceed with processing the retrieved documents
                try:
                    retrieved_texts = [doc.text for doc in input.retrieved_docs]
                    response_data = await self._async_call_reranker(
                        input.user_prompt, retrieved_texts
                    )
                    logger.debug(f"Received response from reranking service: {response_data}")
                    best_response_list = self._filter_top_n(input.top_n, response_data, score_threshold=input.rerank_score_threshold)
                    if len(best_response_list) != len(retrieved_texts):
                        logger.warning(f"Limiting the number of best responses to {len(best_response_list)} based on {len(retrieved_texts)} retrieved documents using max score of {input.rerank_score_threshold}.")
                    logger.debug(f"Best responses after filtering: {best_response_list}")

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
                    reranked_docs = DocList[TextDoc]()
                    for best_response in best_response_list:
                        doc = input.retrieved_docs[best_response["index"]]
                        doc.metadata['reranker_score'] = best_response["score"]
                        reranked_docs.append(doc)
                    logger.debug(f"Retrieved documents: {input.retrieved_docs}")
                    logger.debug(f"Reranked documents via best responses: {reranked_docs}")
        else:
            logger.warning("No retrieved documents found")
            reranked_docs = DocList[TextDoc]()

        if input.sibling_docs:
            final_reranked_docs = self._combine_sibling_docs(reranked_docs, input.sibling_docs)
        else:
            final_reranked_docs = reranked_docs

        # Assign unique citation IDs to file and link citations
        # This assigns unique ID similarly to file_id/link_id but with an integer rather than UUID
        next_citation_id = 1
        citations = {}

        for doc in final_reranked_docs:
            if not hasattr(doc, 'metadata'):
                continue
            doc_id = doc.metadata.get('file_id') or doc.metadata.get('link_id')
            if doc_id not in citations:
                citations[doc_id] = next_citation_id
                next_citation_id += 1
            doc.metadata['citation_id'] = citations[doc_id]

        logger.debug(f"Citations: {citations}")
        logger.debug(f"Final reranked docs: {final_reranked_docs}")
        return PromptTemplateInput(data={"user_prompt": input.user_prompt.strip(), "reranked_docs": final_reranked_docs})

    def _combine_sibling_docs(self, reranked_docs: DocList[TextDoc], sibling_docs: Dict[str, DocList[TextDoc]]) -> List[SearchedDoc]:
        """
        Combines reranked documents with their sibling documents.
        Args:
            reranked_docs (List[str]): The list of reranked document texts.
            sibling_docs (List[SearchedDoc]): The list of sibling documents.
        Returns:
            List[SearchedDoc]: The combined list of reranked documents with their siblings.
        """
        all_combined_docs = []
        for doc in reranked_docs:
            combined_docs = [doc]
            doc_id = doc.metadata.get("id")
            if doc_id and doc_id in sibling_docs:
                siblings = sibling_docs[doc_id]
                combined_docs.extend(siblings)
                combined_docs = sorted(combined_docs, key=lambda x: int(x.metadata.get("start_index", 0)))
                # Combine all texts
                combined_text = " ".join(e.text for e in combined_docs)

                found = any(combined_text == d.text for d in all_combined_docs)
                if found:
                    continue

                # Final result
                combined_element = TextDoc(
                    text=combined_text,
                    metadata=doc.metadata.copy() # Copy metadata from the original document
                )
                all_combined_docs.append(combined_element)
            else:
                all_combined_docs.append(doc)
        return all_combined_docs

    async def _async_call_reranker(
        self,
        user_prompt: str,
        retrieved_docs: List[str],
    ) -> RerankScoreResponse:
        """
        Async calls the reranker service to rerank the retrieved documents based on the initial query.
        Args:
            user_prompt (str): The initial query string.
            retrieved_docs (List[str]): The list of retrieved documents.
        Returns:
            RerankScoreResponse: The response from the reranker service.
        Raises:
            Timeout: If the request to the reranking service times out.
            RequestException: If there is an issue with the request to the reranking service.
            Exception: For any other exceptions that occur during the request.
        """

        data = {"query": user_prompt, "texts": retrieved_docs}

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

    def _filter_top_n_by_vector_distance(self, retrieved_docs: DocList[TextDoc], top_n: int) -> DocList[TextDoc]:
        """
        Filter and return the top N documents based on their vector distances.
        Lower vector distance means higher similarity.

        Args:
            retrieved_docs (DocList[TextDoc]): The list of retrieved documents with vector distances.
            top_n (int): The number of top documents to filter.

        Returns:
            DocList[TextDoc]: The filtered list of top documents sorted by vector distance (ascending).
        """
        # Extract vector_distance from metadata, use a large default if not present
        docs_with_distances = []
        for doc in retrieved_docs:
            vector_distance = doc.metadata.get('vector_distance', float('inf'))
            docs_with_distances.append((doc, vector_distance))
        
        # Sort by vector_distance (ascending - lower is better)
        # Use heapq.nsmallest for efficiency
        top_docs_with_distances = heapq.nsmallest(top_n, docs_with_distances, key=lambda x: x[1])
        
        # Extract just the documents and return as DocList
        top_docs = DocList[TextDoc]()
        for doc, distance in top_docs_with_distances:
            # For late chunking, we use vector_distance as the score
            # Note: vector distance is already in metadata, no need to add reranker_score
            top_docs.append(doc)
        
        return top_docs
