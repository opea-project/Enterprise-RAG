#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import pytest
import urllib3
from helpers.api_request_helper import ApiRequestHelper
from helpers.edp_helper import EdpHelper
from helpers.fingerprint_api_helper import FingerprintApiHelper


@pytest.fixture(scope="session", autouse=True)
def suppress_logging():
    """
    Disable logs that are too verbose and make the output unclear
    """
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    yield


@pytest.fixture
def chatqa_api_helper():
    return ApiRequestHelper("chatqa", {"app": "router-service"})


@pytest.fixture
def edp_helper():
    return EdpHelper(namespace="edp", label_selector={"app.kubernetes.io/name": "edp-backend"}, api_port=5000)


@pytest.fixture
def fingerprint_api_helper():
    return FingerprintApiHelper("fingerprint", {"app.kubernetes.io/name": "fingerprint"}, 6012)


@pytest.fixture
def generic_api_helper():
    return ApiRequestHelper()
