#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import concurrent.futures
import logging
import os
import requests
import time

from rouge import Rouge
from sentence_transformers import SentenceTransformer, util

from validation.constants import ERAG_DOMAIN, TEST_FILES_DIR
from helpers.api_request_helper import ApiRequestHelper, ApiResponse

logger = logging.getLogger(__name__)

DOCSUM_API_PATH = f"{ERAG_DOMAIN}/api/v1/docsum"


class SummaryEvaluator:
    """A class for evaluating summary quality using sentence transformers similarity and ROUGE scores"""
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.rouge = Rouge()

    def evaluate(self, original_text, summary):
        """
        Evaluate summary quality using sentence transformers similarity and ROUGE scores.
        Returns a tuple of (similarity_score, max_rouge_score).
        max_rouge_score is the highest score among all ROUGE metrics - this is done due to
        the case when the summary is very short in comparison to the original text.
        """

        # Sentence transformers similarity
        embedding_text = self.model.encode(original_text, convert_to_tensor=True)
        embedding_summary = self.model.encode(summary, convert_to_tensor=True)
        similarity = util.cos_sim(embedding_text, embedding_summary).item()
        logger.debug(f"Sentence transformers score:\t{round(similarity, 2)}")

        # ROUGE scores
        scores = self.rouge.get_scores(summary, original_text)
        max_rouge_score = 0
        for idx, score_dict in enumerate(scores):
            for rouge_key, metrics in score_dict.items():
                for metric_name, value in metrics.items():
                    if value > max_rouge_score:
                        max_rouge_score = value
        logger.debug(f"Highest rouge score: \t{round(max_rouge_score, 2)}")
        logger.debug(f"Similarity scores (rouge):{scores}")
        return similarity, max_rouge_score


class DocSumHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper=keycloak_helper)
        self.summary_evaluator = SummaryEvaluator()

    def call(self, texts=[], links=[], files=[], summary_type="map_reduce", as_user=False, stream=True):
        """Make DocSum API call with the provided texts, links, and files"""
        payload = {
            "files": files,
            "links": links,
            "texts": texts,
            "parameters": {
                "stream": stream,
                "summary_type": summary_type,
                "chunk_size": 2048
            }
        }
        return self.call_with_payload(payload, as_user=as_user, stream=stream)

    def call_in_parallel(self, texts=[], stream=True):
        """Make DocSum API calls in parallel for the provided texts"""
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(texts)) as executor:
            futures_to_questions = {}
            for text in texts:
                payload = {
                    "files": [],
                    "links": [],
                    "texts": [text],
                    "parameters": {
                        "stream": stream,
                        "chunk_size": 2048
                    }
                }
                future = executor.submit(self.call_with_payload, payload)
                futures_to_questions[future] = payload

            for future in concurrent.futures.as_completed(futures_to_questions):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(ApiResponse(None, None,
                                               exception=f"Request failed with exception: {e}"))
        return results

    def call_with_payload(self, payload, as_user=False, stream=True):
        """Make DocSum API call with the provided payload"""
        logger.info("Making DocSum API call")
        start_time = time.time()
        response = requests.post(
            url=DOCSUM_API_PATH,
            headers=self.get_headers(as_user),
            json=payload,
            stream=stream,
            verify=False
        )
        api_call_duration = round(time.time() - start_time, 2)
        logger.info(f"DocSum API call duration: {api_call_duration}")
        return ApiResponse(response, api_call_duration)

    def get_summary(self, response):
        """Extract summary from DocSum API response"""
        text = self.get_text(response)
        text = text.replace("Here is a concise summary:", "")
        summary = text.replace("[DONE]", "")
        logger.info(f"Got summary: '{summary}'")
        return summary

    def evaluate_summary(self, response, text, text_title=None, summary_type="map_reduce"):
        """Evaluate the summary in the DocSum API response"""
        summary = self.get_summary(response)
        failures = []
        if "[ERROR]" in summary:
            failures.append(f"DocSum API returned an error in the summary: {summary}")
            return failures
        similarity, max_rouge_score = self.summary_evaluator.evaluate(text, summary)
        if similarity < 0.4:
            failures.append(self.failure_message_sentence_transformers(text_title, similarity, summary_type))
        if max_rouge_score < 0.3:
            failures.append(self.failure_message_rouge(text_title, max_rouge_score, summary_type))
        return failures

    def failure_message_sentence_transformers(self, text_title, similarity, summary_type="map_reduce"):
        """Generate failure message for low sentence transformers similarity"""
        return (f"Summary may not be relevant ("
                f"text title: '{text_title}', "
                f"summary_type: '{summary_type}', "
                f"sentence transformers similarity score: {similarity})")

    def failure_message_rouge(self, text_title, max_rouge_score, summary_type="map_reduce"):
        """Generate failure message for low ROUGE score"""
        return (f"Summary may not be relevant ("
                f"text title: '{text_title}', "
                f"summary_type: '{summary_type}', "
                f"max rouge score: {max_rouge_score})")

    def prepare_file_attachment(self, file_name):
        """Prepare a file attachment for DocSum API call"""
        file_path = os.path.join(TEST_FILES_DIR, "docsum", file_name)
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        file_content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        return {
            "filename": file_name,
            "data64": file_content_base64
        }
