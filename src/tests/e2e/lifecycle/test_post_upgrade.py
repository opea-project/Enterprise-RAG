#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import json
import logging
import pytest

from packaging.version import Version

logger = logging.getLogger(__name__)

PRE_UPGRADE_STATE_FILE = "/tmp/pre_upgrade_state.json"


def _load_pre_upgrade_state():
    try:
        with open(PRE_UPGRADE_STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(
            f"Pre-upgrade state file not found: {PRE_UPGRADE_STATE_FILE}. "
            "Run test_pre_upgrade.py (CLUSTER_STATE=before-upgrade) first."
        )


@allure.testcase("IEASG-T621")
def test_post_upgrade_version_changed(k8s_helper):
    """Verify the system version is higher after upgrade."""
    state = _load_pre_upgrade_state()
    old_version = state["version"]

    new_version = k8s_helper.get_deployment_manifest_version()
    logger.info(f"Version before upgrade: {old_version}, after upgrade: {new_version}")

    assert Version(new_version) > Version(old_version), (
        f"Expected version to increase after upgrade, got {old_version} -> {new_version}"
    )


@allure.testcase("IEASG-T622")
def test_post_upgrade_fingerprint_preserved(fingerprint_api_helper):
    """Verify the fingerprint LLM temperature change survived the upgrade."""
    state = _load_pre_upgrade_state()
    expected_temperature = state["fingerprint_temperature"]

    response = fingerprint_api_helper.append_arguments("")
    assert response.status_code == 200, f"Failed to read fingerprint: {response.status_code}"

    actual_temperature = response.json()["parameters"]["temperature"]
    logger.info(f"Expected temperature: {expected_temperature}, actual: {actual_temperature}")

    assert actual_temperature == expected_temperature, (
        f"Fingerprint temperature was reset during upgrade: "
        f"expected {expected_temperature}, got {actual_temperature}"
    )


@allure.testcase("IEASG-T623")
def test_post_upgrade_documents_exist(edp_helper):
    """Verify both pre-upgrade documents are still present in EDP."""
    state = _load_pre_upgrade_state()
    expected_files = state["files"]

    files_response = edp_helper.list_files()
    assert files_response.status_code == 200, f"Failed to list EDP files: {files_response.status_code}"
    all_files = files_response.json()
    file_entries = [(item.get("object_name", "?"), item.get("status", "?")) for item in all_files]
    logger.info(f"EDP files after upgrade ({len(all_files)} total):")
    for name, status in file_entries:
        logger.info(f"  - {name} [status={status}]")

    file_names = [name for name, _ in file_entries]
    for expected_file in expected_files:
        found = any(expected_file in name for name in file_names)
        if not found:
            pytest.fail(
                f"Pre-upgrade file '{expected_file}' not found in EDP after upgrade. "
                f"All files in EDP ({len(all_files)}): {file_names}"
            )


@allure.testcase("IEASG-T624")
def test_post_upgrade_chatqa_retrieval_works(chatqa_api_helper):
    """Verify ChatQA can retrieve and answer from pre-upgrade documents."""
    response = chatqa_api_helper.call_chatqa(
        "What navigation instrument did Fenwick Oldarren invent in the coastal town of Brenthallow?"
    )
    assert response.status_code == 200, f"ChatQA returned unexpected status: {response.status_code}"

    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}")
    assert "quorvane" in response_text.lower(), (
        f"Expected ChatQA to mention 'Quorvane' from pre-upgrade document, got: {response_text}"
    )


@allure.testcase("IEASG-T625")
def test_post_upgrade_chat_history_exists(chat_history_helper):
    """Verify the chat history entry from before upgrade still exists."""
    response = chat_history_helper.get_all_histories()
    assert response.status_code == 200, f"Failed to list chat histories: {response.status_code}"
    all_histories = response.json()
    all_history_names = [history["history_name"] for history in all_histories]
    logger.info(f"Chat histories after upgrade ({len(all_histories)} total):")
    for name in all_history_names:
        logger.info(f"  - {name}")

    found = any("Fenwick Oldarren" in h for h in all_history_names)
    if not found:
        pytest.fail(
            f"Pre-upgrade chat history not found after upgrade. "
            f"All histories ({len(all_histories)}): {all_history_names}"
        )


@allure.testcase("IEASG-T626")
def test_post_upgrade_user_exists_and_can_auth(keycloak_helper):
    """Verify the pre-upgrade Keycloak user exists and can authenticate."""
    state = _load_pre_upgrade_state()
    username = state["keycloak_user"]
    password = state["keycloak_password"]

    assert keycloak_helper.user_exists(username), (
        f"User '{username}' not found in Keycloak after upgrade"
    )

    token = keycloak_helper.get_user_access_token(username, password)
    assert token is not None, (
        f"Failed to obtain access token for user '{username}' after upgrade"
    )
    logger.info(f"User '{username}' authenticated successfully after upgrade")
