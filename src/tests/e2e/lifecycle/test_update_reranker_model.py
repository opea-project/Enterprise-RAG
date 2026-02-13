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

RERANKER_POD_LABEL_SELECTOR = "app.kubernetes.io/name=reranking-usvc"


@allure.testcase("IEASG-T310")
def test_update_reranker_model(k8s_helper):
    """
    Test verifies if reranker pod have the expected RERANKING_MODEL_NAME
    environment variable set.
    """
    expected_model_name = cfg.get("reranking_model_name")
    logger.info(f"Expected reranking model name from config: {expected_model_name}")
    reranker_pod = k8s_helper.get_pod_by_label(namespace=CHATQA_NAMESPACE, label_selector=RERANKER_POD_LABEL_SELECTOR)

    command = ["sh", "-c", "echo $RERANKING_MODEL_NAME"]
    logger.info(f"Checking environment variable $RERANKING_MODEL_NAME in pod: {reranker_pod.name}")
    try:
        env_value = k8s_helper.exec_in_pod(reranker_pod, command)
        logger.info(f"Pod '{reranker_pod.name}' reports RERANKING_MODEL_NAME = '{env_value}'")
    except Exception as e:
        pytest.fail(f"Test failed while executing command in pod '{reranker_pod.name}'. Error: {e}")

    assert env_value == expected_model_name, \
        f"Pod '{reranker_pod.name}' has an incorrect model name. Expected: '{expected_model_name}', Found: '{env_value}'"
