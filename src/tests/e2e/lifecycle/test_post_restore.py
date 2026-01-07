#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest

logger = logging.getLogger(__name__)


@allure.testcase("IEASG-T315")
def test_post_restore_data_exists(keycloak_helper, edp_helper, chat_history_helper, chatqa_api_helper):
    """
    1. Verify that the previously uploaded file is present in the system.
    2. Verify that the chat history is present.
    3. Verify that the previously created user exists.
    4. Ask a question related to the pre-backup data to ensure the system responds correctly.
    """
    # Verify uploaded file exists
    file_name = "test_pre_backup.txt"
    files = edp_helper.list_files()
    for item in files.json():
        if file_name in item['object_name']:
            logger.debug(f"File found: {item['object_name']}")
            break
    else:
        pytest.fail(f"File {file_name} not found after restore.")

    # Verify chat history exists
    response = chat_history_helper.get_all_histories()
    all_history_names = [history["history_name"] for history in response.json()]
    logger.debug(f"All histories: {all_history_names}")
    for history in all_history_names:
        if "What is the name of the cheese" in history:
            logger.debug(f"Chat history found: {history}")
            break
    else:
        pytest.fail("Chat history not found after restore.")

    # Verify user
    user = "backup-test"
    assert keycloak_helper.user_exists(user), f"User {user} not found after restore"

    response = chatqa_api_helper.call_chatqa(
        "What unique product does Elvira Marqens craft in the village of Rulberton?")
    assert response.status_code == 200, "Unexpected status code returned"
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}")
    assert "cheese" in response_text.lower(), "Unexpected answer from ChatQA after restore"


@allure.testcase("IEASG-T316")
def test_post_restore_data_does_not_exists(keycloak_helper, edp_helper, chat_history_helper):
    """
    Check if data ingested after backup does not exist after restore.
    """
    # Verify uploaded file does not exist
    file_name = "test_post_backup.txt"
    files = edp_helper.list_files()
    for item in files.json():
        if file_name in item['object_name']:
            pytest.fail(f"File {file_name} found after restore, but it should not be present.")

    # Verify chat history does not exist
    response = chat_history_helper.get_all_histories()
    all_history_names = [history["history_name"] for history in response.json()]
    logger.debug(f"All histories: {all_history_names}")
    for history in all_history_names:
        if "How do voles affect" in history:
            pytest.fail("Chat history found after restore, but it should not be present.")

    # Verify user does not exist
    user = "post-backup-user-that-should-not-exist-after-restore"
    assert not keycloak_helper.user_exists(user), f"User {user} found after restore, but it should not be present."
