#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import json
import logging
import os
import pytest

from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR


@pytest.fixture(autouse=True)
def edp_cleanup_after_test():
    """No-op override: files must persist for post-upgrade verification."""
    yield


@pytest.fixture(scope="session", autouse=True)
def edp_cleanup_after_session():
    """No-op override: files must persist for post-upgrade verification."""
    yield

logger = logging.getLogger(__name__)

PRE_UPGRADE_STATE_FILE = "/tmp/pre_upgrade_state.json"

UPGRADE_TEST_USER = "upgrade-test-user"
UPGRADE_TEST_PASSWORD = "PreUpgradePass123!"
FINGERPRINT_TEMPERATURE = 0.5

FILE_1 = "test_pre_upgrade.txt"
FILE_2 = "test_pre_upgrade_2.txt"

CHAT_HISTORY_QUESTION = "Fenwick Oldarren: what navigation instrument did he invent in Brenthallow?"
CHAT_HISTORY_ANSWER = "The Quorvane."


@allure.testcase("IEASG-T620")
def test_pre_upgrade(k8s_helper, fingerprint_api_helper, edp_helper, chat_history_helper, keycloak_helper):
    """
    Populate the system with data before upgrade:
    1. Read and save current system version from deployment manifest.
    2. Change a fingerprint parameter (LLM temperature).
    3. Upload two documents via EDP and wait for ingestion.
    4. Create a chat history entry.
    5. Create a Keycloak user.

    All state is persisted to a JSON file so test_post_upgrade.py can verify data survival.
    """
    state = {}

    # 1. Save current version
    version = k8s_helper.get_deployment_manifest_version()
    logger.info(f"Current system version before upgrade: {version}")
    state["version"] = version

    # 2. Change fingerprint parameter
    fingerprint_api_helper.set_component_parameters("llm", temperature=FINGERPRINT_TEMPERATURE)
    logger.info(f"Set LLM temperature to {FINGERPRINT_TEMPERATURE}")
    state["fingerprint_temperature"] = FINGERPRINT_TEMPERATURE

    # 3. Upload documents
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, FILE_1))
    logger.info(f"Uploaded and ingested: {FILE_1}")

    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, FILE_2))
    logger.info(f"Uploaded and ingested: {FILE_2}")

    state["files"] = [FILE_1, FILE_2]

    # 3b. Verify documents are visible in EDP after ingestion
    files_response = edp_helper.list_files()
    assert files_response.status_code == 200, f"Failed to list EDP files: {files_response.status_code}"
    all_files = files_response.json()
    file_names = [f.get("object_name", "") for f in all_files]
    logger.info(f"EDP files after ingestion ({len(all_files)} total): {file_names}")
    for expected in [FILE_1, FILE_2]:
        assert any(expected in name for name in file_names), (
            f"Uploaded file '{expected}' not found in EDP immediately after ingestion. "
            f"Available files: {file_names}"
        )

    # 4. Create chat history
    save_response = chat_history_helper.save_history([
        {
            "question": CHAT_HISTORY_QUESTION,
            "answer": CHAT_HISTORY_ANSWER,
            "metadata": {}
        }
    ])
    assert save_response.status_code == 200, (
        f"Failed to save chat history: {save_response.status_code}"
    )
    logger.info("Chat history entry created")

    # 4b. Read-back verification — confirm history was actually persisted
    histories_response = chat_history_helper.get_all_histories()
    assert histories_response.status_code == 200, f"Failed to list histories: {histories_response.status_code}"
    all_histories = [h["history_name"] for h in histories_response.json()]
    logger.info(f"Chat histories after save ({len(all_histories)} total): {all_histories}")
    assert any("Fenwick Oldarren" in h for h in all_histories), (
        f"Chat history read-back failed — entry not found immediately after save. "
        f"Available histories: {all_histories}"
    )

    state["chat_history_question"] = CHAT_HISTORY_QUESTION

    # 5. Create Keycloak user
    if not keycloak_helper.user_exists(UPGRADE_TEST_USER):
        keycloak_helper.add_user(
            UPGRADE_TEST_USER,
            UPGRADE_TEST_PASSWORD,
            "UpgradeTest",
            "User",
            "upgrade-test@example.com"
        )
        logger.info(f"Created Keycloak user: {UPGRADE_TEST_USER}")
    else:
        logger.info(f"Keycloak user '{UPGRADE_TEST_USER}' already exists, reusing")
    state["keycloak_user"] = UPGRADE_TEST_USER
    state["keycloak_password"] = UPGRADE_TEST_PASSWORD

    # Persist state for post-upgrade verification
    with open(PRE_UPGRADE_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    logger.info(f"Pre-upgrade state saved to {PRE_UPGRADE_STATE_FILE}")
