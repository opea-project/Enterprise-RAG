#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import kr8s
import requests
import time


class InvalidChatqaResponseBody(Exception):
    """
    Raised when the call to /v1/chatqa returns a body does not follow
    'Server-Sent Events' structure
    """
    pass


class ApiRequestHelper:

    def __init__(self, namespace=None, label_selector=None):
        self.namespace = namespace
        self.label_selector = label_selector
        self.api_port = 8080
        self.default_headers = {"Content-Type": "application/json"}

    def call_chatqa(self, question):
        """
        Make /v1/chatqa API call with the provided question.
        """
        json_data = {"text": question}
        pods = kr8s.get("pods",
                        namespace=self.namespace,
                        label_selector={"app": self.label_selector})

        with pods[0].portforward(remote_port=self.api_port) as local_port:
            print(f"Asking the following question: {question}")
            start_time = time.time()
            response = requests.post(
                f"http://127.0.0.1:{local_port}/v1/chatqa",
                headers=self.default_headers,
                json=json_data
            )
            duration = time.time() - start_time
            print(f"ChatQA API call duration: {duration}")
        return response

    def format_response(self, response_body):
        """
        Parse raw response_body from the chatqa response and return a human-readable text
        """
        response_lines = response_body.splitlines()
        response_text = ""
        for line in response_lines:
            if line == "":
                continue
            elif not line.startswith("data:"):
                raise InvalidChatqaResponseBody(
                    "Chatqa API response body does not follow "f"'Server-Sent Events' structure. "
                    f"Response: {response_body}"
                )
            else:
                response_text += line[7:-1]
        # Replace new line characters for better output
        return response_text.replace('\\n', '\n')

    def call_dataprep_upload_file(self, filepath):
        """
        Make /v1/dataprep API call to upload a specified file.
        """
        with open(filepath, "rb") as f:
            file_content = f.read()
            file_content_base64 = base64.b64encode(file_content)
            file_content_base64_str = str(file_content_base64, "utf-8")

        json_data = {
            "files": [{
                    "filename": "test_dataprep.txt",
                    "data64": file_content_base64_str
                }
            ]
        }
        return self._call_dataprep_upload_file(json_data)

    def call_dataprep_upload_custom_body(self, custom_body):
        """
        Make /v1/dataprep API call with a specified custom request body
        """
        return self._call_dataprep_upload_file(custom_body)

    def _call_dataprep_upload_file(self, request_body):
        pod = self._get_pod()
        with pod.portforward(remote_port=self.api_port) as local_port:
            response = requests.post(
                f"http://127.0.0.1:{local_port}/v1/dataprep",
                headers=self.default_headers,
                json=request_body
            )
        return response

    def call_dataprep_upload_links(self, links):
        """
        API call to upload a link to a website
        """
        body = {"links": links}
        return self._call_dataprep_upload_link(body)

    def call_dataprep_upload_link_custom_body(self, custom_body):
        """
        API call to upload a link to a website. Use custom request body
        """
        return self._call_dataprep_upload_link(custom_body)

    def _call_dataprep_upload_link(self, body):
        pod = self._get_pod()
        with pod.portforward(remote_port=self.api_port) as local_port:
            response = requests.post(
                f"http://127.0.0.1:{local_port}/v1/dataprep",
                headers=self.default_headers,
                json=body
            )
        return response

    def call_health_check_api(self, namespace, selector, port):
        """
        API call to microservice health_check API.
        Microservices are not exposed so we need to forward their ports first.
        namespace and selector are used in order to find the specified pod
        which handles health_check call.
        """
        pod = self._get_pod(namespace, selector)
        with pod.portforward(remote_port=port) as local_port:
            print(f"Attempting to make a request to {namespace}/{selector}...")
            response = requests.get(
                f"http://127.0.0.1:{local_port}/v1/health_check",
                headers=self.default_headers,
                timeout=10
            )
            return response

    def _get_pod(self, namespace=None, label_selector=None):
        ns = namespace if namespace else self.namespace
        selector = label_selector if label_selector else self.label_selector
        pods = kr8s.get("pods",
                        namespace=ns,
                        label_selector={"app": selector})
        return pods[0]
