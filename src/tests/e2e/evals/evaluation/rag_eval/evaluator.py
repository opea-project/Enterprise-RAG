# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import requests
import time
import uuid
from datetime import datetime

from comps import (
    change_opea_logger_level,
    get_opea_logger,
)

from tests.e2e.evals.metrics import bleu_score, rougeL_score
from tests.e2e.evals.metrics.retrieval import RetrievalBaseMetric

from tests.e2e.helpers.chatqa_api_helper import ChatQaApiHelper
from tests.e2e.helpers.k8s_helper import K8sHelper
from tests.e2e.helpers.keycloak_helper import KeycloakHelper
from tests.e2e.helpers.edp_helper import EdpHelper
from tests.e2e.helpers.fingerprint_api_helper import FingerprintApiHelper

# Initialize the logger for the microservice
logger = get_opea_logger("RAG Evaluator")
change_opea_logger_level(
    logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


class Evaluator:
    def __init__(
            self, dataset: list[dict] = None, output_dir: str = None) -> None:
        """Args:
        dataset (list[dict]): The dataset for evaluation.
        output_dir (str): The directory to save results.
        """

        current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        # this file is created after the evaluation is completed and overall metrics are computed
        self.output_file = os.path.join(
            output_dir, f"multihop_{current_time}.json")

        # each result is appended to this file during the evaluation
        self.output_checkpoint_file = os.path.join(
            output_dir, f"multihop_{current_time}.checkpoint.jsonl")

        self.dataset = dataset
        self.system_args = None

        self.keycloak_helper = KeycloakHelper(k8s_helper=K8sHelper(), credentials_file=None)
        self.chatqa_api_helper = ChatQaApiHelper(keycloak_helper=self.keycloak_helper)
        self.edp_helper = EdpHelper(
            keycloak_helper=self.keycloak_helper, bucket_name="default")
        self.fingerprint_api_helper = FingerprintApiHelper(
            self.keycloak_helper)

        self.GENERATION_METRICS_LIST = [
            "bleu-avg",
            "bleu-1",
            "bleu-2",
            "bleu-3",
            "bleu-4",
            "rouge-L",
            "LLM-score",
            "length",
        ]

        self.RETRIEVAL_METRICS_LIST = [
            "Hits@10",
            "Hits@4",
            "MAP@10",
            "MRR@10",
            "Hits@10_retrieved",
            "Hits@4_retrieved",
            "MAP@10_retrieved",
            "MRR@10_retrieved",
            "gain_Hits@10",
            "gain_Hits@4",
            "gain_MAP@10",
            "gain_MRR@10",
        ]

    def validate_connections_to_rag_services(self) -> None:
        """
        Validate connections to EDP and ChatQA services.
        """
        if not self._check_connection_to_edp() or not self._check_connection_to_chatqa():
            raise ConnectionError("Failed to connect to required services.")

    def fetch_system_args(self) -> None:
        try:
            system_args = self.fingerprint_api_helper.append_arguments("")
            system_args = system_args.json().get("parameters")
            self.system_args = system_args
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to fetch RAG system configuration from the fingerprint API, err={e}")
            raise ConnectionError(
                f"Failed to fetch RAG system configuration  from the fingerprint API, err={e}")

    # TODO: Ingest all 609 items as separate documents using parallel uploads.
    # Previous attempt failed on document '079_israel-s-defense-undone-by-reliance.txt'.
    # Requires further investigation.

    def ingest_docs(self, document_path: str) -> None:
        """Args:
        document_path (str): The path to document
        """

        presigned_url = self.edp_helper.generate_presigned_url(
            document_path).json().get("url")
        response = self.edp_helper.upload_file(document_path, presigned_url)

        if response.status_code == 200:
            logger.info(
                f"File {document_path} uploaded successfully. Waiting for ingestion...")
            # The file is 6.1 MB and splits into 17,508 chunks.
            # The full process (uploading, text extracting, embedding, ingesting) usually takes around 3 minutes and 46 seconds,
            # so 4 minutes should be sufficient timeout only for being in status ingested.
            file = self.edp_helper.wait_for_file_upload(
                document_path, "ingested", timeout=240)
            logger.info(f"Successfully ingested {file['object_name']}.")
        else:
            logger.error(
                f"Error encountered while ingestion document {document_path}: {response.text}")
            raise Exception(
                f"Error encountered while ingestion document {document_path}: {response.text}")

    def get_uuid(self, question: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, question))

    def get_ground_truth_text(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_golden_context(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_query(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_document(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def scoring(self, data: dict) -> dict:
        generated_text = data["generated_text"]
        ground_truth_text = self.get_ground_truth_text(data)
        data["ground_truth_text"] = ground_truth_text

        bleu_avg, bleu1, bleu2, bleu3, bleu4 = bleu_score(
            generated_text, ground_truth_text)

        return {
            "metrics": {
                "bleu-avg": bleu_avg or 0.0,
                "bleu-1": bleu1 or 0.0,
                "bleu-2": bleu2 or 0.0,
                "bleu-3": bleu3 or 0.0,
                "bleu-4": bleu4 or 0.0,
                "rouge-L": rougeL_score(generated_text, ground_truth_text) or 0.0,
                "LLM-score": 0.0,
                "length": len(generated_text),
            },
            "log": {
                "query": self.get_query(data),
                "generated_text": generated_text,
                "ground_truth_text": ground_truth_text,
                "evaluateDatetime": str(datetime.now()),
            },
            "valid": len(generated_text.strip()) != 0,
        }

    def scoring_retrieval(self, data: dict) -> dict:
        metric = RetrievalBaseMetric()
        query = self.get_query(data)
        golden_context = self.get_golden_context(data)

        retrieved_documents = self.get_retrieved_documents(query)
        reranked_documents = self.get_reranked_documents(query)

        # Measure metrics using documents after reranking
        results = metric.measure({
            "input": query,
            "golden_context": golden_context,
            "retrieval_context": reranked_documents,
        })
        logger.info(f"Results after reranking for query '{query}': {results}")

        # Additionally measure metrics using documents retrieved by the retriever only
        results_retrieved = metric.measure({
            "input": query,
            "golden_context": golden_context,
            "retrieval_context": retrieved_documents,
        })
        logger.info(f"Results for query '{query}': {results_retrieved}")

        return {
            "retrieval_metrics": {
                "Hits@10": results["Hits@10"] or 0.0,
                "Hits@4": results["Hits@4"] or 0.0,
                "MAP@10": results["MAP@10"] or 0.0,
                "MRR@10": results["MRR@10"] or 0.0,
                "Hits@10_retrieved": results_retrieved["Hits@10"] or 0.0,
                "Hits@4_retrieved": results_retrieved["Hits@4"] or 0.0,
                "MAP@10_retrieved": results_retrieved["MAP@10"] or 0.0,
                "MRR@10_retrieved": results_retrieved["MRR@10"] or 0.0,
                "gain_Hits@10": (results["Hits@10"]-results_retrieved["Hits@10"]) or 0.0,
                "gain_Hits@4": (results["Hits@4"]-results_retrieved["Hits@4"]) or 0.0,
                "gain_MAP@10": (results["MAP@10"]-results_retrieved["MAP@10"]) or 0.0,
                "gain_MRR@10": (results["MRR@10"]-results_retrieved["MRR@10"]) or 0.0,
            },
            "log": {
                "query": self.get_query(data),
                "golden_context": golden_context,
                "num_retrieved_documents": len(retrieved_documents),
                "num_reranked_documents": len(reranked_documents),
                "reranked_documents": reranked_documents,
                # "retrieved_documents": retrieved_documents, # Useful for debugging: log all documents returned by the retriever
                "evaluateDatetime": str(datetime.now()),
            },
            "valid": len(reranked_documents) != 0,
        }

    def compute_overall_metrics(self, results: list[dict]) -> dict:
        """
        Compute average generation metrics (e.g., BLEU, ROUGE, LLM-score) across a list of result dictionaries.
        """
        return self._compute_overall(results, "metrics", self.GENERATION_METRICS_LIST)

    def compute_overall_retrieval_metrics(self, results: list[dict]) -> dict:
        """
        Compute average retrieval metrics (e.g., Hits@k, MAP@10, MRR@10) across a list of result dictionaries.
        """
        return self._compute_overall(results, "retrieval_metrics", self.RETRIEVAL_METRICS_LIST)

    def save_output(self, output: dict) -> None:
        """Save evaluation results to a JSON file."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
            logger.info(f"Output saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to save output to {self.output_file}: {e}")
            raise e

    def append_jsonl(self, result: dict):
        """Append partial evaluation results to a JSONL file."""
        try:
            with open(self.output_checkpoint_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(
                f"Failed to append partial result to {self.output_checkpoint_file }: {e}")

    def load_jsonl(self, file_path: str) -> list[dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]

    def remove_invalid(self, results: list[dict]) -> list[dict]:
        """Remove invalid results from the list and return the cleaned results."""
        return [result for result in results if result["valid"]]

    def get_template(self):
        raise NotImplementedError("Depends on the specific dataset.")

    def send_request(self, query, arguments, max_retries=3, wait_seconds=5):
        parameters = {
            "stream": False,
            "temperature": arguments.temperature if arguments.temperature is not None else self.system_args["temperature"],
            "max_new_tokens": arguments.max_new_tokens if arguments.max_new_tokens is not None else self.system_args["max_new_tokens"],
            "top_p": self.system_args["top_p"],
            "top_k": self.system_args["top_k"],
            "typical_p": self.system_args["typical_p"],
            "repetition_penalty": self.system_args["repetition_penalty"],
        }

        logger.info(
            f"Sending request to ChatQA with query: '{query}' and parameters: {parameters}")

        for attempt in range(max_retries):
            response = self.chatqa_api_helper.call_chatqa(
                question=query, parameters=parameters)

            if response.status_code == 200:
                response_text = self.post_process(response)
                logger.debug(f"ChatQA response: {response_text}")
                return response_text
            else:
                logger.warning(
                    f"Attempt {attempt + 1} failed with error: {response.text}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_seconds} seconds...")
                    time.sleep(wait_seconds)  # wait before next attempt

        logger.error("All retry attempts failed.")
        return None

    def get_reranked_documents(self, query):
        """
        Connects to the RAG API at /v1/retrieve and returns reranked documents retrieved for the given query.
        """
        return self._get_documents(query, rerank=True)

    def get_retrieved_documents(self, query):
        """
        Connects to the RAG API at /v1/retrieve and returns all documents retrieved by the retriever (without reranking) for the given query
        """
        return self._get_documents(query, rerank=False)

    def post_process(self, result):
        return self.chatqa_api_helper.get_text(result)

    def evaluate(self, arguments, sort=True, show_progress_bar=False, contain_original_data=False):
        raise NotImplementedError("Depends on the specific dataset.")

    def _compute_overall(self, results: list[dict], metric_key: str, keys: list[str]) -> dict:
        overall = {key: 0 for key in keys}

        for result in results:
            metrics = result.get(metric_key, {})
            for key in keys:
                overall[key] += metrics.get(key, 0)

        overall_avg = {f"avg. {key}": round(
            value/len(results), 4) for key, value in overall.items()}
        overall_avg["num"] = len(results)
        return overall_avg

    def _check_connection_to_edp(self) -> bool:
        """
        Check if EDP backend is reachable.
        """
        try:
            response = self.edp_helper.list_buckets()
            if response.status_code == 200:
                logger.info("EDP connection: OK")
                return True
            logger.error(f"EDP connection failed: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to EDP: {e}")
        return False

    def _check_connection_to_chatqa(self) -> bool:
        """
        Check if ChatQA backend is reachable.
        """
        try:
            response = self.chatqa_api_helper.call_chatqa("hello")
            if response.status_code == 200:
                logger.info("ChatQA connection: OK")
                return True
            logger.error(f"ChatQA connection failed: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to ChatQA: {e}")
        return False

    # TODO: Track parameters used for retrieving documents as a part of the evaluation result
    def _get_documents(self, query: str, rerank: bool = True, max_retries: int = 3, wait_seconds: int = 5) -> list[str]:
        """
        Internal helper method to retrieve reranked documents, optionally all retrieved documents when rerank set to False.
        """
        texts = []

        payload = {
            "query": query,
            "reranker": "true" if rerank else "false",
            "distance_threshold": self.system_args["distance_threshold"],
            "fetch_k": self.system_args["fetch_k"],
            "k": self.system_args["k"],
            "lambda_mult": self.system_args["lambda_mult"],
            "score_threshold": self.system_args["score_threshold"],
            "search_type": self.system_args["search_type"],
        }

        if rerank:
            # set to 10 to support MAP@10 calculation and others
            payload["top_n"] = 10
            payload["rerank_score_threshold"] = self.system_args["rerank_score_threshold"]

        logger.info(f"Retrieving documents with payload: {payload}")
        try:

            for attempt in range(max_retries):
                response = self.edp_helper.retrieve(payload)
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"[Attempt {attempt + 1}] Document retrieval failed with status {response.status_code}. "
                            f"Response: {response.text}. Retrying in {wait_seconds} seconds..."
                        )
                        time.sleep(wait_seconds)
                        continue
                    else:
                        logger.error("All document retrieval attempts failed.")
                        raise ConnectionError(
                            f"Document retrieval failed. HTTP {response.status_code}: {response.text}"
                        )

            docs = response.json()["docs"]

            if rerank:
                # Note: in reranker responses, texts are nested under 'data', and then 'reranked_docs'
                texts = [doc["text"] for doc in docs["data"]["reranked_docs"]]
            else:
                # If rerank is False, the response follows the retriever's format
                texts = [doc["text"] for doc in docs["retrieved_docs"]]

            # Log a warning if no documents were found
            if not texts:
                logger.warning(
                    f"No documents returned from {'reranking' if rerank else 'retriever'} for query '{query}'")

        except json.JSONDecodeError:
            logger.error("Response is not in JSON format.")
        except KeyError as e:
            logger.error(f"Missing expected key in JSON response: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error processing retrieved documents: {e}")

        return texts
