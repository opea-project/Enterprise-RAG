#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest
import kr8s
import logging
import time
import os

from helpers.guard_helper import GuardType
from constants import TEST_FILES_DIR

logger = logging.getLogger(__name__)


class HPA:
     def __init__(self, name="", namespace="", metrics=""):
         self.name = name
         self.namespace = namespace
         self.metrics = metrics


def get_hpa_current_metrics(hpa_name: str, hpa_namespace: str) -> str:
    try:
        hpa_obj = kr8s.objects.HorizontalPodAutoscaler.get(hpa_name, namespace=hpa_namespace)
    except kr8s.NotFoundError as e:
        pytest.fail(f"HPA object {hpa_name} not found: {repr(e)}")
    try:
        return hpa_obj.status.currentMetrics[0].object.current
    except KeyError as e:
        pytest.fail(f"HPA object {hpa_name}: Object's <unknown> state has been detected: {repr(e)}")


@allure.testcase("IEASG-T186")
def test_hpa(edp_helper, chatqa_api_helper, guard_helper):
    """Test horizontal pods autoscaling"""
    def get_hpas(): return kr8s.get("horizontalpodautoscalers", namespace=kr8s.ALL)
    HPAS_WITH_INITIALLY_UNKNOWN_STATES = ["istio", "tei-reranking", "in-guard"]
    VLLM_HPA_NAME = "vllm"
    TORCHSERVE_R_HPA_NAME = "torchserve-reranking"
    TORCHSERVE_E_HPA_NAME = "torchserve-embedding"

    logger.info("Initial check to verify HPA objects creation...")
    PROMETHEUS_POD_NAME = "prometheus-adapter"
    try:
        kr8s.get("pod", PROMETHEUS_POD_NAME, namespace="monitoring")
    except kr8s.NotFoundError as e:
        pytest.fail(f"Can't detect {PROMETHEUS_POD_NAME} pod: {repr(e)}")
    # Fetch HPAs
    hpas = get_hpas()
    assert len(hpas) > 0, "No HPAs were found"
    # Check HPAs
    for hpa in hpas:
        logger.info(f"HPA object: {hpa.metadata.name}")

        # Verify HPA configuration
        assert hpa.spec.maxReplicas >= hpa.spec.minReplicas, "Max replicas should be >= min replicas"

        # Analyze HPA object's metrics
        if any(sub in hpa.metadata.name for sub in HPAS_WITH_INITIALLY_UNKNOWN_STATES):
            logger.info("Skip metrics' analysis for this HPA object")
            continue
        hpa_object_metrics = get_hpa_current_metrics(hpa.name, hpa.namespace)
        logger.info(f"Metrics: {hpa_object_metrics}")

        # Save metrics that will have to be changed
        if VLLM_HPA_NAME in hpa.metadata.name:
            vllm = HPA(hpa.name, hpa.namespace, hpa_object_metrics)
        elif TORCHSERVE_R_HPA_NAME in hpa.metadata.name:
            torchserve_reranking = HPA(hpa.name, hpa.namespace, hpa_object_metrics)
        elif TORCHSERVE_E_HPA_NAME in hpa.metadata.name:
            torchserve_embedding = HPA(hpa.name, hpa.namespace, hpa_object_metrics)

    assert 'vllm' in locals() and vllm.name != "" and vllm.namespace != "" and vllm.metrics != "", \
            (f"Failed to get initial HPA data for {VLLM_HPA_NAME}")

    logger.info(f"Check for HPA values changes on {vllm.name} after a question...")
    gen_question = "Tell me a 1000 word story about the meaning of life"
    response = chatqa_api_helper.call_chatqa(gen_question)
    assert response.status_code == 200, (f"Request failed with status code: {response.status_code}"
                                         f"Answer: {response.text}")

    vllm_current_metrics = vllm.metrics
    # Wait for updated HPA values of vllm
    ASSESSMENT_TRIES = 6
    for i in range(ASSESSMENT_TRIES):
        vllm_current_metrics = get_hpa_current_metrics(vllm.name, vllm.namespace)
        logger.info(f"Try #{i}, {vllm.name} Metrics: {vllm_current_metrics}")
        if vllm_current_metrics != vllm.metrics:
            break
        time.sleep(10)
    assert vllm_current_metrics != vllm.metrics, (f"{vllm.name}: HPA values have not changed: {vllm_current_metrics}")

    logger.info("Recheck HPA objects' metrics after uploading a file and providing additional question...")
    file = "story.pdf"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.INPUT, "sentiment", guard_params)
    doc_based_question = "Is it true that Krystianooo found a backdoor?"
    guard_helper.assert_allowed(doc_based_question)
    status_code, response = guard_helper.call_chatqa(doc_based_question)
    assert status_code != 466, (f"Question: {doc_based_question}"
                                f"Request banned with status code: {status_code}")
    # Refetch HPAs
    hpas = get_hpas()
    assert len(hpas) > 0, "No HPAs were found"
    # Recheck HPAs
    for hpa in hpas:
        logger.info(f"HPA object: {hpa.metadata.name}")

        # Reverify HPA object's metrics
        if HPAS_WITH_INITIALLY_UNKNOWN_STATES[0] in hpa.metadata.name:
            logger.info("Skip metrics' analysis for this HPA object")
            continue
        hpa_object_metrics = get_hpa_current_metrics(hpa.name, hpa.namespace)
        logger.info(f"Metrics: {hpa_object_metrics}")

        # Check for HPA values changes on torchserve
        if TORCHSERVE_R_HPA_NAME in hpa.metadata.name:
            assert 'torchserve_reranking' in locals(), (f"{TORCHSERVE_R_HPA_NAME}: missing initial data")
            assert hpa_object_metrics != torchserve_reranking.metrics, (f"{torchserve_reranking.name}: HPA values have not changed: {hpa_object_metrics}")
        elif TORCHSERVE_E_HPA_NAME in hpa.metadata.name:
            assert 'torchserve_embedding' in locals(), (f"{TORCHSERVE_E_HPA_NAME}: missing initial data")
            assert hpa_object_metrics != torchserve_embedding.metrics, (f"{torchserve_embedding.name}: HPA values have not changed: {hpa_object_metrics}")
