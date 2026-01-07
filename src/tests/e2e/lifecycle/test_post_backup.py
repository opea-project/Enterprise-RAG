#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import os

from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)


@allure.testcase("IEASG-T313")
def test_post_backup_backup_created(k8s_helper):
    """
    Check backup is properly created.
    1. check  if "velero" namespace exists.
    2. check if there is at least one backup in velero namespace.
    3. check if backup is in "Completed" status (check all backups for the sake of simplicity).
    4. check if there are no "Error" or "CrashLoopBackOff" pods in "velero" namespace.
    """
    velero_ns = k8s_helper.get_namespace("velero")
    assert velero_ns is not None, "Velero namespace does not exist."

    backups = k8s_helper.get_backups(namespace="velero")
    assert len(backups) > 0, "No backups found in velero namespace."

    for backup in backups:
        logger.debug(f"Backup Name: {backup.name}, Status: {backup.status.phase}")
        assert backup.status.phase == "Completed", f"Backup {backup.name} is not completed."

    velero_pods = k8s_helper.list_pods(namespace="velero")
    for pod in velero_pods:
        pod_status = pod.status.phase
        logger.debug(f"Pod Name: {pod.name}, Status: {pod_status}")
        assert pod_status not in ["Error", "CrashLoopBackOff"], f"Pod {pod.name} is in {pod_status} status."


@allure.testcase("IEASG-T314")
def test_post_backup_data_ingested_after_backup(keycloak_helper, edp_helper, chat_history_helper):
    """
    Ingest some data which should not be present in the backup since backup was already created.
    1. Upload a file to the system via EDP.
    2. Create a chat history via Chat History API.
    3. Create a new user in Keycloak.
    """
    # Upload a file
    file = "test_post_backup.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))

    # Create chat history
    chat_history_helper.save_history([
        {
            "question": "How do voles affect the ecosystem near Gdansk Airport?",
            "answer": "They serve as a crucial food source for various predators such as owls, "
                      "foxes, and snakes, helping maintain the balance of the food web.",
            "metadata": {}
        }
    ])

    # Create a new user
    user = "post-backup-user-that-should-not-exist-after-restore"
    if not keycloak_helper.user_exists(user):
        keycloak_helper.add_user(user, "PostBackupPass123!", "PostBackupUser", "PostBackupSurname", "postbackup@example.com")
