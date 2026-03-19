# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_env_vars():
    """Set up default environment variables for tests."""
    # Set default env vars before any module imports
    os.environ.setdefault('DOCSUM_DEFAULT_SUMMARY_TYPE', 'map_reduce')
    os.environ.setdefault('DOCSUM_LLM_USVC_ENDPOINT', 'http://localhost:9000/v1')
    os.environ.setdefault('DOCSUM_USVC_PORT', '9001')
    yield
    # Note: We don't clean up here as tests may override these individually


@pytest.fixture(autouse=True, scope="session")
def mock_validation():
    """Mock the validation request that happens during OPEADocsum initialization."""
    with patch('comps.docsum.utils.opea_docsum.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture(autouse=True, scope="session")
def mock_register_microservice():
    """Mock the register_microservice decorator."""
    def decorator_mock(**kwargs):
        def wrapper(func):
            return func
        return wrapper

    with patch('comps.register_microservice', decorator_mock):
        yield decorator_mock


@pytest.fixture(autouse=True, scope="session")
def mock_register_statistics():
    """Mock the register_statistics decorator."""
    def decorator_mock(**kwargs):
        def wrapper(func):
            return func
        return wrapper

    with patch('comps.register_statistics', decorator_mock):
        yield decorator_mock
