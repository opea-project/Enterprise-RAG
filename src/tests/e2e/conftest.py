#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
from datetime import datetime, timezone
import kr8s
import os
import logging
import pytest
import tarfile
import urllib3

from helpers.api_request_helper import ApiRequestHelper
from helpers.edp_helper import EdpHelper
from helpers.fingerprint_api_helper import FingerprintApiHelper
from helpers.guard_helper import GuardHelper
from helpers.istio_helper import IstioHelper
from helpers.keycloak_helper import KeycloakHelper

NAMESPACES = ["chatqa", "edp", "fingerprint", "dataprep", "system", "istio-system", "rag-ui"]  # List of namespaces to fetch logs from
TEST_LOGS_DIR = "test_logs"

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--credentials-file", action="store", default="",
                     help="Path to credentials file. Required fields: "
                          "KEYCLOAK_ERAG_ADMIN_USERNAME and KEYCLOAK_ERAG_ADMIN_PASSWORD")


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


@pytest.fixture(scope="session", autouse=True)
def disable_guards_at_startup(guard_helper, suppress_logging):
    """
    Disable all guards at the beginning of the test suite.
    Note that supress_logging fixture is deliberately placed here to ensure that it is executed
    before this fixture (otherwise we'd see a lot of unwanted logs at startup)
    """
    guard_helper.disable_all_guards()
    yield


@pytest.fixture(scope="function", autouse=True)
def collect_k8s_logs(request):
    """
    Collect logs from all pods in the specified namespaces after each test function.
    Attach the archived logs to the allure report.
    """
    test_start_time = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec='seconds').replace("+00:00", "Z")
    yield

    test_name = request.node.name
    log_dir = f"{TEST_LOGS_DIR}/{test_name}"
    os.makedirs(log_dir, exist_ok=True)

    api = kr8s.api()
    for namespace in NAMESPACES:
        pods = api.get("pods", namespace=namespace)

        for pod in pods:
            pod_name = pod.metadata.name
            log_file = os.path.join(log_dir, f"{namespace}_{pod_name}.log")

            logs = "\n".join(pod.logs(since_time=test_start_time))
            with open(log_file, "w") as f:
                f.write(logs)
    logger.info(f"Logs collected in {log_dir}")

    # Archive all logs into a tar.gz file
    tar_path = f"{TEST_LOGS_DIR}/logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{test_name}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(log_dir, arcname=test_name)
    logger.info(f"Logs archived: {tar_path}")

    # Attach in allure report
    allure.attach.file(tar_path, f"logs_{test_name}.tar.gz")


@pytest.fixture(scope="session")
def chatqa_api_helper():
    return ApiRequestHelper("chatqa", {"app": "router-service"})


@pytest.fixture(scope="session")
def keycloak_helper(request):
    return KeycloakHelper(request.config.getoption("--credentials-file"))


@pytest.fixture(scope="session")
def edp_helper():
    return EdpHelper(namespace="edp", label_selector={"app.kubernetes.io/name": "edp-backend"}, api_port=5000)


@pytest.fixture(scope="session")
def fingerprint_api_helper():
    return FingerprintApiHelper("fingerprint", {"app.kubernetes.io/name": "fingerprint"}, 6012)


@pytest.fixture(scope="session")
def istio_helper():
    return IstioHelper()


@pytest.fixture(scope="session")
def generic_api_helper():
    return ApiRequestHelper()


@pytest.fixture(scope="session")
def guard_helper(chatqa_api_helper, fingerprint_api_helper):
    return GuardHelper(chatqa_api_helper, fingerprint_api_helper)


@pytest.fixture(scope="session")
def code_snippets():
    """
    Reads code snippet files from a specified directory and returns
    a dictionary mapping each snippet's name (without the file extension)
    to its content.
    """
    def _code_snippets(snippets_dir=None):
        code_snippets = {}
        if snippets_dir is None:
            snippets_dir = "files/code_snippets"

        for filename in os.listdir(snippets_dir):
            file_path = os.path.join(snippets_dir, filename)
            with open(file_path, 'r') as file:
                content = file.read()
                name_without_extension = os.path.splitext(filename)[0]
                code_snippets[name_without_extension] = content
        return code_snippets

    return _code_snippets
