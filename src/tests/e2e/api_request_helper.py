#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

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

    def __init__(self, namespace, label_selector):
        self.namespace = namespace
        self.label_selector = label_selector
        self.api_port = 8080

    def call_chatqa(self, question):
        """
        Make /v1/chatqa API call with the provided question.

        If print_response is set to True, the response will be live-printed
        for debugging purposes
        """
        headers = {"Content-Type": "application/json"}
        json_data = {"text": question}
        pods = kr8s.get("pods",
                        namespace=self.namespace,
                        label_selector={"app": self.label_selector})

        with pods[0].portforward(remote_port=self.api_port) as local_port:
            print(f"Asking the following question: {question}")
            start_time = time.time()
            response = requests.post(
                f"http://127.0.0.1:{local_port}/v1/chatqa",
                headers=headers,
                json=json_data
            )
            duration = time.time() - start_time
            print(f"ChatQA API call duration: {duration}")
        return response

    def format_response(self, response_body):
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
