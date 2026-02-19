#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import os

from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)


@allure.testcase("IEASG-T312")
def test_pre_backup(keycloak_helper, edp_helper, chat_history_helper):
    """
    Prepare data for backup:
    1. Upload a file to the system via EDP.
    2. Create a chat history via Chat History API.
    3. Create a new user in Keycloak.
    """
    # Populate db
    file = "test_pre_backup.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))

    # Populate chat history
    chat_history_helper.save_history([
        {
            "question": "What is the name of the cheese produced by Elvira Marqens from the village of Rulberton?",
            "answer": "Trindlefoss.",
            "metadata": {}
        }
    ])

    # Add new user if it does not exist
    user = "backup-test"
    if not keycloak_helper.user_exists(user):
        keycloak_helper.add_user(user, "PreBackupPass123!", "BackupUser", "BackupSurname", "backup@example.com")
