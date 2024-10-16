#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import pytest
from api_request_helper import ApiRequestHelper


@pytest.fixture(scope="session", autouse=True)
def suppress_logging():
    """
    Disable logs that are too verbose and make the output unclear
    """
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    yield


@pytest.fixture
def chatqa_api_helper():
    return ApiRequestHelper("chatqa", "router-service")


@pytest.fixture
def dataprep_api_helper():
    return ApiRequestHelper("dataprep", "router-service")


@pytest.fixture
def generic_api_helper():
    return ApiRequestHelper()
