#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import concurrent
import logging
import secrets
import socket
import time
from urllib.parse import urljoin

import kr8s
import requests
from tests.e2e.validation.constants import (
    ERAG_DOMAIN, INGRESS_NGINX_CONTROLLER_NS,
    INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR)

logger = logging.getLogger(__name__)


class CustomPortForward(object):

    def __init__(self, remote_port, namespace, label_selector, local_port=None):
        local_port = self._find_unused_port() if local_port is None else local_port
        pod = self._get_pod(namespace, label_selector)
        self.pf = kr8s.portforward.PortForward(pod, remote_port=remote_port, local_port=local_port)

    def __enter__(self):
        self.pf.start()
        time.sleep(1)
        return self.pf

    def __exit__(self, type, value, traceback):
        self.pf.stop()
        time.sleep(1)

    def _find_unused_port(self, start=10000, end=60000):
        """
        Return a random unused port between start and end
        """
        while True:
            port = secrets.randbelow(end - start) + start
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(("127.0.0.1", port))
                if result != 0:  # Port is not in use
                    return port

    def _get_pod(self, namespace, label_selector):
        pods = kr8s.get("pods",
                        namespace=namespace,
                        label_selector=label_selector)
        return pods[0]


class InvalidChatqaResponseBody(Exception):
    """
    Raised when the call to /v1/chatqa returns a body does not follow
    'Server-Sent Events' structure
    """
    pass


class ApiResponse:
    """
    Wrapper class for the response from 'requests' library
    """

    def __init__(self, response, response_time, exception=None):
        self._response = response
        self._response_time = response_time
        self._exception = exception

    def __getattr__(self, name):
        return getattr(self._response, name)

    @property
    def response_time(self):
        return self._response_time

    @property
    def exception(self):
        return self._exception


class ApiRequestHelper:

    def __init__(self, namespace=None, label_selector=None, api_port=8080):
        self.namespace = namespace
        self.label_selector = label_selector
        self.api_port = api_port
        self.default_headers = {"Content-Type": "application/json"}

    def call_chatqa(self, question, **custom_params):
        """
        Make /v1/chatqa API call with the provided question.
        """
        json_data = {
            "text": question
        }
        json_data.update(custom_params)
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            return self._call_chatqa(json_data, pf)

    def call_chatqa_in_parallel(self, questions):
        """Ask questions in parallel"""

        request_bodies = []
        for question in questions:
            json_data = {"text": question, "parameters": {"streaming": False}}
            request_bodies.append(json_data)

        results = []
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(questions)) as executor:
                futures_to_questions = {}
                for request_body in request_bodies:
                    future = executor.submit(self._call_chatqa, request_body, pf)
                    futures_to_questions[future] = question

                for future in concurrent.futures.as_completed(futures_to_questions):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        results.append(ApiResponse(None, None,
                                                   exception=f"Request failed with exception: {e}"))
        return results

    def _call_chatqa(self, request_body, port_forward):
        logger.info(f"Asking the following question: {request_body.get('text')}")
        start_time = time.time()
        response = requests.post(
            f"http://127.0.0.1:{port_forward.local_port}/v1/chatqa",
            headers=self.default_headers,
            json=request_body
        )
        api_call_duration = round(time.time() - start_time, 2)
        logger.info(f"ChatQA API call duration: {api_call_duration}")
        return ApiResponse(response, api_call_duration)

    def call_chatqa_through_apisix(self, token, question):
        """
        Make /api/v1/chatqna API call through APISIX using provided token.

        This method does not port-forwarding router-server. Instead, it does port-forwarding of nginx-controller
        in order to reach it in case of Kind deployment.
        """
        url = f"{ERAG_DOMAIN}/api/v1/chatqna"
        payload = {"text": question}
        headers = self.default_headers
        headers["authorization"] = f"Bearer {token}"

        logger.info(f"Asking the following question: {question}")
        start_time = time.time()
        with CustomPortForward(443, INGRESS_NGINX_CONTROLLER_NS,
                               INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR, 443):
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                stream=True,
                verify=False
            )
        api_call_duration = round(time.time() - start_time, 2)
        logger.info(f"ChatQA API call duration: {api_call_duration}")
        return ApiResponse(response, api_call_duration)

    def format_response(self, response):
        """
        Parse raw response_body from the chatqa response and return a human-readable text
        """
        if response.headers.get("Content-Type") == "application/json":
            response_text = response.json().get("text")
            if response_text is None:
                response_text = response.json().get("error")
            return response_text
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
                    logger.warning("There're no 'reranked_docs' e2e tests for the moment, Ignoring...")
                    # reranked_docs = line[7:-1]
                elif line.startswith("data:"):
                    response_text += line[7:-1]
                else:
                    logger.warning(f"Unexpected line in the response: {line}")
                    raise InvalidChatqaResponseBody(
                        "Chatqa API response body does not follow 'Server-Sent Events' structure. "
                        f"Response: {response.text}.\n\nHeaders: {response.headers}"
                    )
            # Replace new line characters for better output
            return response_text.replace('\\n', '\n')
        else:
            raise InvalidChatqaResponseBody(
                f"Unexpected Content-Type in the response: {response.headers.get('Content-Type')}")

    def fix_encoding(self, string):
        try:
            # Encode as bytes, then decode with UTF-8
            return string.encode('latin1').decode('utf-8')
        except Exception:
            return string  # Append original if there's an error

    def call_health_check_api(self, namespace, selector, port, health_path="v1/health_check"):
        """
        API call to microservice health_check API.
        Microservices are not exposed so we need to forward their ports first.
        namespace and selector are used in order to find the specified pod
        which handles health_check call.
        """
        with CustomPortForward(port, namespace, selector) as pf:
            logger.info(f"Attempting to make a request to {namespace}/{selector}...")
            base_url = f"http://127.0.0.1:{pf.local_port}/"
            full_url = urljoin(base_url, health_path)
            response = requests.get(
                full_url,
                headers=self.default_headers,
                timeout=10
            )
            return response

    def words_in_response(self, substrings, response):
        """Returns true if any of the substrings appear in the response strings"""
        response = response.lower()
        return any(substring.lower() in response for substring in substrings)

    def all_words_in_response(self, substrings, response):
        """Returns true if all of the substrings appear in the response strings"""
        response = response.lower()
        return all(substring.lower() in response for substring in substrings)
