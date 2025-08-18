#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import time

import requests

from tests.e2e.helpers.api_request_helper import ApiRequestHelper, ApiResponse
from tests.e2e.validation.constants import ERAG_DOMAIN

logger = logging.getLogger(__name__)


class FingerprintApiHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper=keycloak_helper)

    def change_arguments(self, json_data):
        """
        /v1/system_fingerprint/change_arguments API call
        """
        start_time = time.time()
        response = requests.post(
            f"{ERAG_DOMAIN}/v1/system_fingerprint/change_arguments",
            headers=self.get_headers(),
            json=json_data,
            verify=False
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
        start_time = time.time()
        response = requests.post(
            url=f"{ERAG_DOMAIN}/v1/system_fingerprint/append_arguments",
            headers=self.get_headers(),
            json=json_data,
            verify=False
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
