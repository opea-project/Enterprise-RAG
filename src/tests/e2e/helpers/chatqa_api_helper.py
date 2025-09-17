#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import concurrent
import json
import logging
import time

import requests
from tests.e2e.validation.constants import ERAG_DOMAIN
from tests.e2e.helpers.api_request_helper import ApiRequestHelper, ApiResponse


logger = logging.getLogger(__name__)
CHATQA_API_PATH = f"{ERAG_DOMAIN}/api/v1/chatqna"


class InvalidChatqaResponseBody(Exception):
    """
    Raised when the call to /v1/chatqa returns a body does not follow
    'Server-Sent Events' structure
    """
    pass


class ChatQaApiHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper=keycloak_helper)

    def call_chatqa(self, question, as_user=False, **custom_params):
        """
        Make /v1/chatqa API call with the provided question. Streaming disabled.
        """
        json_data = {
            "text": question
        }
        json_data.update(custom_params)
        return self._call_chatqa(json_data, as_user=as_user)

    def call_chatqa_with_streaming_enabled(self, question, **custom_params):
        """
        Make /v1/chatqa API call with the provided question and enable streaming response.
        """
        json_data = {
            "text": question
        }
        json_data.update(custom_params)
        return self._call_chatqa(json_data, stream=True)

    def call_chatqa_in_parallel(self, questions):
        """Ask questions in parallel"""

        request_bodies = []
        for question in questions:
            json_data = {"text": question, "parameters": {"streaming": False}}
            request_bodies.append(json_data)

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(questions)) as executor:
            futures_to_questions = {}
            for payload in request_bodies:
                future = executor.submit(self._call_chatqa, payload)
                futures_to_questions[future] = payload

            for future in concurrent.futures.as_completed(futures_to_questions):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(ApiResponse(None, None,
                                               exception=f"Request failed with exception: {e}"))
        return results

    def _call_chatqa(self, payload, stream=False, as_user=False):
        """
        Make /api/v1/chatqna API call through APISIX using provided token.
        """
        logger.info(f"Asking the following question: {payload['text']}")
        start_time = time.time()
        response = requests.post(
            url=CHATQA_API_PATH,
            headers=self.get_headers(as_user),
            json=payload,
            stream=stream,
            verify=False
        )
        api_call_duration = round(time.time() - start_time, 2)
        logger.info(f"ChatQA API call duration: {api_call_duration}")
        return ApiResponse(response, api_call_duration)

    def format_response(self, response):
        """
        Parse raw response_body from the chatqa response and return a human-readable text
        """
        response_text = ""
        reranked_docs = []
        if response.headers.get("Content-Type") == "application/json":
            response = response.json()
            response_text = response.get("text")
            if response_text is None:
                response_text = response.get("error")
            reranked_docs = response.get("json", {}).get("reranked_docs", [])
        elif response.headers.get("Content-Type") == "text/event-stream":
            text = self.fix_encoding(response.text)
            response_lines = text.splitlines()
            response_text = ""
            for line in response_lines:
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                if line == "":
                    continue
                if line.startswith("json:"):
                    # Remove 'json: ' prefix and parse the JSON content
                    reranked_docs = line[5:]
                    reranked_docs = json.loads(reranked_docs)
                    reranked_docs = reranked_docs.get("reranked_docs", [])
                elif line.startswith("data:"):
                    response_text += line[7:-1]
                else:
                    logger.warning(f"Unexpected line in the response: {line}")
                    raise InvalidChatqaResponseBody(
                        "Chatqa API response body does not follow 'Server-Sent Events' structure. "
                        f"Response: {response.text}.\n\nHeaders: {response.headers}"
                    )
            # Replace new line characters for better output
            response_text = response_text.replace('\\n', '\n')
        else:
            raise InvalidChatqaResponseBody(
                f"Unexpected Content-Type in the response: {response.headers.get('Content-Type')}")
        return response_text, reranked_docs

    def get_text(self, response):
        """Extract the text from the response"""
        response_text, _ = self.format_response(response)
        return response_text

    def get_reranked_docs(self, response):
        """Extract the reranked_docs from the response"""
        _, reranked_docs = self.format_response(response)
        return reranked_docs

    def fix_encoding(self, string):
        try:
            # Encode as bytes, then decode with UTF-8
            return string.encode('latin1').decode('utf-8')
        except Exception:
            return string  # Append original if there's an error

    def words_in_response(self, substrings, response):
        """Returns true if any of the substrings appear in the response strings"""
        response = response.lower()
        return any(substring.lower() in response for substring in substrings)

    def all_words_in_response(self, substrings, response):
        """Returns true if all of the substrings appear in the response strings"""
        response = response.lower()
        return all(substring.lower() in response for substring in substrings)

