#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import time

import requests

from tests.e2e.helpers.api_request_helper import ApiRequestHelper, ApiResponse
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)


class FingerprintApiHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper=keycloak_helper)
        self.change_args_api_path = f"https://{cfg.get('FQDN')}/v1/system_fingerprint/change_arguments"
        self.append_args_api_path = f"https://{cfg.get('FQDN')}/v1/system_fingerprint/append_arguments"

    def change_arguments(self, json_data, as_user=False):
        """
        /v1/system_fingerprint/change_arguments API call
        """
        start_time = time.time()
        response = requests.post(
            self.change_args_api_path,
            headers=self.get_headers(as_user=as_user),
            json=json_data,
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (/v1/system_fingerprint/change_arguments) call duration: {duration}")
        return ApiResponse(response, duration)

    def append_arguments(self, text, as_user=False):
        """
        /v1/system_fingerprint/append_arguments API call
        """
        return self._append_arguments({"text": text}, as_user=as_user)

    def append_arguments_custom_body(self, json_body):
        """
        /v1/append_arguments API call to Fingerprint microservice with a custom JSON body
        """
        return self._append_arguments(json_body)

    def _append_arguments(self, json_data, as_user=False):
        start_time = time.time()
        response = requests.post(
            self.append_args_api_path,
            headers=self.get_headers(as_user=as_user),
            json=json_data,
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (/v1/system_fingerprint/append_arguments) call duration: {duration}")
        return ApiResponse(response, duration)

    def set_component_parameters(self, component, **parameters):
        """Change component parameters"""
        body = [{
            "name": component,
            "data": {
                **parameters
            }
        }]
        self.change_arguments(body)
