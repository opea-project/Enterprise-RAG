#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import time

import requests

from tests.e2e.helpers.api_request_helper import (ApiRequestHelper, ApiResponse,
                                        CustomPortForward)

logger = logging.getLogger(__name__)


class FingerprintApiHelper(ApiRequestHelper):

    def __init__(self, namespace, label_selector, api_port):
        super().__init__(namespace=namespace, label_selector=label_selector, api_port=api_port)

    def change_arguments(self, json_data):
        """
        /v1/system_fingerprint/change_arguments API call
        """
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            response = requests.post(
                f"http://127.0.0.1:{pf.local_port}/v1/system_fingerprint/change_arguments",
                headers=self.default_headers,
                json=json_data
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (/v1/system_fingerprint/change_arguments) call duration: {duration}")
            return ApiResponse(response, duration)

    def append_arguments(self, text):
        """
        /v1/system_fingerprint/append_arguments API call
        """
        return self._append_arguments({"text": text})

    def append_arguments_custom_body(self, json_body):
        """
        /v1/append_arguments API call to Fingerprint microservice with a custom JSON body
        """
        return self._append_arguments(json_body)

    def _append_arguments(self, json_data):
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            response = requests.post(
                f"http://127.0.0.1:{pf.local_port}/v1/system_fingerprint/append_arguments",
                headers=self.default_headers,
                json=json_data
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (/v1/system_fingerprint/append_arguments) call duration: {duration}")
            return ApiResponse(response, duration)

    def set_streaming(self, streaming=True):
        """
        Disable streaming
        """
        self._change_llm_parameters(streaming=streaming)

    def set_llm_parameters(self, **parameters):
        """
        Change LLM parameters
        """
        self._change_llm_parameters(**parameters)

    def _change_llm_parameters(self, **parameters):
        body = [{
            "name": "llm",
            "data": {
                **parameters
            }
        }]
        self.change_arguments(body)
