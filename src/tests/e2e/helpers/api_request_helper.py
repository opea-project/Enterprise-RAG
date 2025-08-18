#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import secrets
import socket
import time
from urllib.parse import urljoin

import kr8s
import requests
from tests.e2e.validation.constants import ERAG_DOMAIN

logger = logging.getLogger(__name__)
CHATQA_API_PATH = f"{ERAG_DOMAIN}/api/v1/chatqna"


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

    def get_headers(self):
        """ Get headers with the access token for authenticated requests. """
        token = self.keycloak_helper.get_access_token()
        headers = self.default_headers
        headers["authorization"] = f"Bearer {token}"
        return headers
