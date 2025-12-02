#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import hashlib
from pathlib import Path

import allure
from datetime import datetime, timezone
import kr8s
import os
import logging
import pytest
import tarfile
import urllib3
import yaml

from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import TEST_FILES_DIR
from tests.e2e.helpers.api_request_helper import ApiRequestHelper
from tests.e2e.helpers.chatqa_api_helper import ChatQaApiHelper
from tests.e2e.helpers.chat_history_helper import ChatHistoryHelper
from tests.e2e.helpers.docsum_helper import DocSumHelper

from tests.e2e.helpers.edp_helper import EdpHelper
from tests.e2e.helpers.fingerprint_api_helper import FingerprintApiHelper
from tests.e2e.helpers.guard_helper import GuardHelper
from tests.e2e.helpers.istio_helper import IstioHelper
from tests.e2e.helpers.k8s_helper import K8sHelper
from tests.e2e.helpers.keycloak_helper import KeycloakHelper

# List of namespaces to fetch logs from
NAMESPACES = ["auth-apisix", "chatqa",  "docsum", "edp", "fingerprint", "dataprep", "system", "istio-system", "rag-ui"]
TEST_LOGS_DIR = "test_logs"

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--credentials-file", action="store", default="",
                     help="Path to credentials file. Required fields: "
                          "KEYCLOAK_ERAG_ADMIN_USERNAME and KEYCLOAK_ERAG_ADMIN_PASSWORD")
    parser.addoption("--build-config-file", action="store", default="../../deployment/ansible-logs/config.yaml",
                     help="Path to build configuration YAML file")


def pytest_configure(config):
    """
    Load build configuration from the specified YAML file and store it in the global cfg dictionary.
    """
    # Manually configure logging here since pytest configures it only after this hook
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    build_config_filepath = config.getoption("--build-config-file")
    if os.path.exists(build_config_filepath):
        logger.debug(f"Loading build configuration from {build_config_filepath}")
        with open(build_config_filepath, "r") as f:
            build_configuration = yaml.safe_load(f)

        # store into global cfg
        cfg.update(build_configuration)
    else:
        pytest.fail("Build configuration file not found. Please provide a valid path using --build-config-file option.")

    # Remove previously configured logger. If it was not removed, every log would be displayed twice.
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)


def pytest_runtest_call(item):
    scenario_name = os.getenv("SCENARIO", "Install")
    custom = f"{scenario_name}:{item.nodeid}"
    custom_history_id = hashlib.sha256(custom.encode()).hexdigest()
    allure.dynamic.parameter("historyId", custom_history_id)


def pytest_collection_modifyitems(config, items):
    root_dir = Path(config.rootdir)
    scenario_name = os.getenv("SCENARIO", "Install")
    for item in items:
        test_path = Path(item.fspath)
        test_directory = test_path.parent
        try:
            relative_dir = test_directory.relative_to(root_dir)
            folder_parts = relative_dir.parts
            final_suite_name = ".".join(folder_parts)
        except ValueError:
            final_suite_name = test_directory.name
        scenario_tag = f"scenario:{scenario_name}"
        pipeline_tag = f"pipeline:{ cfg.get('pipelines', [])[0]['type'] }"
        llm_model_tag = f"llm_model:{ cfg.get('llm_model', []) }"

        add_marker(item, "parentSuite", scenario_name)
        add_marker(item, "suite", final_suite_name)
        add_marker(item, "feature", scenario_tag)
        add_marker(item, "feature", pipeline_tag)
        add_marker(item, "feature", llm_model_tag)


def add_marker(item, label_name, label_value):
    item.add_marker(allure.label(label_name, label_value))


@pytest.fixture(scope="session", autouse=True)
def suppress_logging():
    """
    Disable logs that are too verbose and make the output unclear
    """
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("tqdm").setLevel(logging.ERROR)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    yield


@pytest.fixture(scope="session")
def k8s_helper(request, suppress_logging):
    return K8sHelper()


@pytest.fixture(scope="session")
def keycloak_helper(request, k8s_helper, suppress_logging):
    # suppress_logging fixture is deliberately placed here to ensure that it is executed
    return KeycloakHelper(request.config.getoption("--credentials-file"), k8s_helper)


@pytest.fixture(scope="session", autouse=True)
def temporarily_remove_user_required_actions(keycloak_helper, suppress_logging):
    """
    Disable the required actions for the erag-admin user temporarily to allow obtaining the access token without
    forcing to change the password. Get it back after the tests are done.
    """
    required_actions = keycloak_helper.read_current_required_actions(keycloak_helper.admin_access_token,
                                                                     keycloak_helper.erag_admin_username)
    if required_actions:
        keycloak_helper.remove_required_actions(keycloak_helper.admin_access_token,
                                                keycloak_helper.erag_admin_username)
    yield
    # Restore original settings after tests
    if required_actions:
        keycloak_helper.revert_required_actions(required_actions, keycloak_helper.admin_access_token,
                                                keycloak_helper.erag_admin_username)


@pytest.fixture(scope="session")
def temporarily_remove_regular_user_required_actions(keycloak_helper):
    """
    Temporarily remove required actions for the regular user to allow obtaining an access token.
    """
    required_actions = keycloak_helper.read_current_required_actions(keycloak_helper.admin_access_token,
                                                                     keycloak_helper.erag_user_username)
    if required_actions:
        keycloak_helper.remove_required_actions(keycloak_helper.admin_access_token,
                                                keycloak_helper.erag_user_username)
    yield
    # Restore original settings after tests
    if required_actions:
        keycloak_helper.revert_required_actions(required_actions, keycloak_helper.admin_access_token,
                                                keycloak_helper.erag_user_username)


@pytest.fixture(scope="session", autouse=True)
def disable_guards_at_startup(guard_helper, suppress_logging, temporarily_remove_user_required_actions):
    """
    Disable all guards at the beginning of the test suite.
    Note that supress_logging fixture is deliberately placed here to ensure that it is executed
    before this fixture (otherwise we'd see a lot of unwanted logs at startup)
    """
    fingerprint_enabled = cfg.get("fingerprint", {}).get("enabled")
    if fingerprint_enabled:
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
            try:
                logs = "\n".join(pod.logs(since_time=test_start_time))
            except Exception as e:
                logger.warning(f"Failed to read logs for pod {pod_name} in namespace {namespace}. "
                               f"Pod might have already been deleted. Exception: {e}")
                continue
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
def edp_helper(keycloak_helper):
    return EdpHelper(keycloak_helper=keycloak_helper)


@pytest.fixture(scope="session")
def chatqa_api_helper(keycloak_helper):
    return ChatQaApiHelper(keycloak_helper)


@pytest.fixture(scope="session")
def chat_history_helper(keycloak_helper):
    return ChatHistoryHelper(keycloak_helper)


@pytest.fixture(scope="session")
def docsum_helper(keycloak_helper):
    return DocSumHelper(keycloak_helper)


@pytest.fixture(scope="session")
def fingerprint_api_helper(keycloak_helper):
    return FingerprintApiHelper(keycloak_helper)


@pytest.fixture(scope="session")
def istio_helper():
    return IstioHelper()


@pytest.fixture(scope="session")
def generic_api_helper():
    return ApiRequestHelper()


@pytest.fixture(scope="session")
def guard_helper(chatqa_api_helper, fingerprint_api_helper):
    return GuardHelper(chatqa_api_helper, fingerprint_api_helper)


@pytest.fixture(scope="function")
def temporarily_remove_brute_force_detection(keycloak_helper):
    """
    Disable brute force detection in Keycloak for the duration of the test.
    This is to avoid locking the user out in case of many concurrent requests.
    """
    keycloak_helper.set_brute_force_detection(False)
    yield
    keycloak_helper.set_brute_force_detection(True)


@pytest.fixture(scope="session")
def code_snippets():
    """
    Reads code snippet files from a specified directory and returns
    a dictionary mapping each snippet's name (without the file extension)
    to its content.
    """
    return _read_test_files("code_snippets")


@pytest.fixture(scope="session")
def long_code_snippets():
    """
    Reads code snippet files from a specified directory and returns
    a dictionary mapping each snippet's name (without the file extension)
    to its content.
    """
    return _read_test_files("code_snippets_long")


@pytest.fixture(scope="module")
def texts():
    """
    Reads text files from a specified directory and returns
    a dictionary mapping each text's name (without the file extension)
    to its content.
    """
    return _read_test_files("docsum")


def _read_test_files(test_files_subdirectory="docsum"):
    """
    Reads test files from a specified subdirectory within the TEST_FILES_DIR
    and returns a dictionary mapping each file's name (without the file extension)
    to its content.
    """
    test_files = {}
    directory_with_test_files = f"{TEST_FILES_DIR}/{test_files_subdirectory}"
    for filename in os.listdir(directory_with_test_files):
        file_path = os.path.join(directory_with_test_files, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            name_without_extension = os.path.splitext(filename)[0]
            test_files[name_without_extension] = content
    return test_files
