#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import concurrent
import kr8s
import requests
import secrets
import socket
import time


class CustomPortForward(object):

    def __init__(self, remote_port, namespace, label_selector):
        local_port = self._find_unused_port()
        pod = self._get_pod(namespace, label_selector)
        self.pf = kr8s.portforward.PortForward(pod, remote_port=remote_port, local_port=local_port)

    def __enter__(self):
        self.pf.start()
        time.sleep(1)
        return self.pf

    def __exit__(self, type, value, traceback):
        self.pf.stop()

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
                        label_selector={"app": label_selector})
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

    def __init__(self, namespace=None, label_selector=None):
        self.namespace = namespace
        self.label_selector = label_selector
        self.api_port = 8080
        self.default_headers = {"Content-Type": "application/json"}

    def call_chatqa(self, question, **custom_params):
        """
        Make /v1/chatqa API call with the provided question.
        """
        json_data = {
            "text": question,
            "parameters": {
                "streaming": False
            }
        }
        json_data["parameters"].update(custom_params)

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
                                                   f"Request failed with exception: {e}"))
        return results

    def _call_chatqa(self, request_body, port_forward):
        print(f"Asking the following question: {request_body.get('text')}")
        start_time = time.time()
        response = requests.post(
            f"http://127.0.0.1:{port_forward.local_port}/v1/chatqa",
            headers=self.default_headers,
            json=request_body
        )
        duration = round(time.time() - start_time, 2)
        print(f"ChatQA API call duration: {duration}")
        return ApiResponse(response, duration)

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
        return self._call_dataprep_upload(json_data)

    def call_dataprep_upload_custom_body(self, custom_body):
        """
        Make /v1/dataprep API call with a specified custom request body
        """
        return self._call_dataprep_upload(custom_body)

    def call_dataprep_upload_links(self, links):
        """
        API call to upload a link to a website
        """
        body = {"links": links}
        return self._call_dataprep_upload(body)

    def _call_dataprep_upload(self, request_body):
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.post(
                f"http://127.0.0.1:{pf.local_port}/v1/dataprep",
                headers=self.default_headers,
                json=request_body
            )
        return response

    def call_health_check_api(self, namespace, selector, port):
        """
        API call to microservice health_check API.
        Microservices are not exposed so we need to forward their ports first.
        namespace and selector are used in order to find the specified pod
        which handles health_check call.
        """
        with CustomPortForward(port, namespace, selector) as pf:
            print(f"Attempting to make a request to {namespace}/{selector}...")
            response = requests.get(
                f"http://127.0.0.1:{pf.local_port}/v1/health_check",
                headers=self.default_headers,
                timeout=10
            )
            return response
