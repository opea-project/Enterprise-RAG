# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import os
import requests

from comps import (
    change_opea_logger_level,
    get_opea_logger
)

from tests.e2e.evals.metrics import bleu_score, rougeL_score

from tests.e2e.helpers.api_request_helper import ApiRequestHelper
from tests.e2e.helpers.edp_helper import EdpHelper

# Initialize the logger for the microservice
logger = get_opea_logger("RAG Evaluator")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


class Evaluator:
    def __init__(
        self, dataset: list[dict] = None, output_path: str = None) -> None:
        """Args:
        dataset (list[dict]): The dataset for evaluation.
        output_path (str): The path to save results.
        """

        self.output_path = output_path
        self.dataset = dataset

        self.chatqa_api_helper = ApiRequestHelper("chatqa", {"app": "router-service"})
        self.edp_helper =  EdpHelper(namespace="edp", label_selector={"app.kubernetes.io/name": "edp-backend"}, api_port=5000, bucket_name="default")

    def validate_connections_to_rag_services(self) -> None:
        """
        Validate connections to EDP and ChatQA services.
        """
        if not self._check_connection_to_edp() or not self._check_connection_to_chatqa():
            raise ConnectionError("Failed to connect to required services.")


    def ingest_docs(self, document_path: str) -> None:
        """Args:
        document_path (str): The path to document
        """

        presigned_url = self.edp_helper.generate_presigned_url(document_path).json().get("url")
        response = self.edp_helper.upload_file(document_path, presigned_url)
            
        if response.status_code == 200:
            logger.info(f"File {document_path} uploaded successfully. Waiting for ingestion...")
            # The file is 6.1 MB and splits into 17,508 chunks.
            # The full process (uploading, text extracting, embedding, ingesting) usually takes around 3 minutes and 46 seconds,
            # so 4 minutes should be sufficient timeout only for being in status ingested.
            file = self.edp_helper.wait_for_file_upload(document_path, "ingested", timeout=240)
            logger.info(f"Successfully ingested {file['object_name']}.")
        else:
            logger.error(f"Error encountered while ingestion document {document_path}: {response.text}")
            raise Exception(f"Error encountered while ingestion document {document_path}: {response.text}")


    def get_ground_truth_text(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_query(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_document(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def scoring(self, data: dict) -> dict:
        generated_text = data["generated_text"]
        ground_truth_text = self.get_ground_truth_text(data)
        data["ground_truth_text"] = ground_truth_text

        bleu_avg, bleu1, bleu2, bleu3, bleu4 = bleu_score(generated_text, ground_truth_text)

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
                "evaluateDatetime": str(datetime.datetime.now()),
            },
            "valid": len(generated_text.strip()) != 0,
        }

    def compute_overall(self, results: list[dict]) -> dict:
        overall = {
            "bleu-avg": 0,
            "bleu-1": 0,
            "bleu-2": 0,
            "bleu-3": 0,
            "bleu-4": 0,
            "rouge-L": 0,
            "LLM-score": 0.0,
            "length": 0,
        }

        for result in results:
            overall = {key: overall[key] + result["metrics"][key] for key in overall.keys()}

        overall_save = {f"avg. {key}": value / len(results) for key, value in overall.items()}
        overall_save["num"] = len(results)
        return overall_save

    def save_output(self, output: dict) -> None:
        """Save evaluation results."""
        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
            logger.info(f"Output saved to {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to save output to {self.output_path}: {e}")
            raise e

    def remove_invalid(self, results: list[dict]) -> list[dict]:
        """Remove invalid results from the list and return the cleaned results."""
        return [result for result in results if result["valid"]]

    def get_template(self):
        raise NotImplementedError("Depends on the specific dataset.")

    def send_request(self, query, arguments):   
        parameters={"streaming": False, "temperature": arguments.temperature}
        response = self.chatqa_api_helper.call_chatqa(question=query, parameters=parameters)

        if response.status_code == 200:
            response_text = self.post_process(response)
            logger.debug(f"ChatQA response: {response_text}")

        else:
            logger.error(f"Request for pipeline failed due to {response.text}.")
            return ""
        
        return response_text
                
    def post_process(self, result):
        return self.chatqa_api_helper.format_response(result)

    def evaluate(self, arguments, sort=True, show_progress_bar=False, contain_original_data=False):
        raise NotImplementedError("Depends on the specific dataset.")
    
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
