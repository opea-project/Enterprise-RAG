#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest

from tests.e2e.validation.constants import CHATQA_NAMESPACE
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

EMBEDDING_POD_LABEL_SELECTOR = "app.kubernetes.io/name=embedding-usvc"


@allure.testcase("IEASG-T311")
def test_update_embedding_model(k8s_helper):
    """
    Test verifies if reranker pod have the expected EMBEDDING_MODEL_NAME
    environment variable set.
    """
    expected_model_name = cfg.get("embedding_model_name")
    logger.info(f"Expected reranking model name from config: {expected_model_name}")
    embedding_pod = k8s_helper.get_pod_by_label(namespace=CHATQA_NAMESPACE,
                                                label_selector=EMBEDDING_POD_LABEL_SELECTOR)

    command = ["sh", "-c", "echo $EMBEDDING_MODEL_NAME"]
    logger.info(f"Checking environment variable $EMBEDDING_MODEL_NAME in pod: {embedding_pod.name}")
    try:
        env_value = k8s_helper.exec_in_pod(embedding_pod, command)
        logger.info(f"Pod '{embedding_pod.name}' reports EMBEDDING_MODEL_NAME = '{env_value}'")
    except Exception as e:
        pytest.fail(f"Test failed while executing command in pod '{embedding_pod.name}'. Error: {e}")

    assert env_value == expected_model_name, \
        f"Pod '{embedding_pod.name}' has an incorrect model name. Expected: '{expected_model_name}', Found: '{env_value}'"
