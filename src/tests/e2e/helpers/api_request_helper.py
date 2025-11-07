#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import secrets
import socket
import time
from urllib.parse import urljoin

import kr8s
import requests

logger = logging.getLogger(__name__)


class InvalidChatqaResponseBody(Exception):
    """
    Raised when the call to /v1/chatqa returns a body does not follow
    'Server-Sent Events' structure
    """
    pass


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

    def __init__(self, keycloak_helper=None):
        self.default_headers = {"Content-Type": "application/json"}
        self.keycloak_helper = keycloak_helper

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

    def get_headers(self, as_user=None):
        """ Get headers with the access token for authenticated requests. """
        if as_user:
            self.default_headers["authorization"] = f"Bearer {self.keycloak_helper.get_access_token(as_user=True)}" if self.keycloak_helper else ""
        else:
            self.default_headers["authorization"] = f"Bearer {self.keycloak_helper.access_token}" if self.keycloak_helper else ""
        return self.default_headers

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
            resonse_json_key = response.get("json")
            if resonse_json_key:
                reranked_docs = resonse_json_key.get("reranked_docs", [])
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
                # Sometimes (depending on the pipeline) the response is wrapped in single quotes
                elif line.startswith("data: '"):
                    line = line.removeprefix("data: '")
                    response_text += line.removesuffix("'")
                elif line.startswith("data: "):
                    response_text += line.removeprefix("data: ")
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

    def fix_encoding(self, string):
        try:
            # Encode as bytes, then decode with UTF-8
            return string.encode('latin1').decode('utf-8')
        except Exception:
            return string  # Append original if there's an error

    def get_text(self, response):
        """Extract the text from the response"""
        response_text, _ = self.format_response(response)
        return response_text
