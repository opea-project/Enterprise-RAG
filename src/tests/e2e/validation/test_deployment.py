#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest
import kr8s
import logging
import time
import os
from typing import Dict, Any, Union

from tests.e2e.helpers.guard_helper import GuardType
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)


class HPA:
    # Class constants
    ASSESSMENT_TRIES = 6
    RETRY_INTERVAL = 10

    def __init__(self, name: str = "", namespace: str = "", metrics: Union[Dict[str, Any], str] = ""):
        self.name = name
        self.namespace = namespace
        self.metrics = metrics

    def check_metrics_not_zero(self) -> bool:
        """
        Checks if metrics value is not equal to zero.
        Returns True if the value is non-zero, False otherwise.
        """
        if not self.metrics or not isinstance(self.metrics, dict):
            return False

        try:
            metrics_val = self.metrics[next(iter(self.metrics))]
            if isinstance(metrics_val, str) and metrics_val.isdigit():
                return bool(int(metrics_val))
            elif isinstance(metrics_val, (int, float)):
                return bool(metrics_val)
            return True
        except (StopIteration, KeyError):
            return False

    def check_initialization(self) -> bool:
        """
        Checks if all expected instance attributes are initialized and not empty.
        """
        for attr_name, attr_value in self.__dict__.items():
            if not attr_name.startswith('__') and isinstance(attr_value, str):
                if attr_value == "":
                    return False
        return True

    def check_updated_hpa_values(self) -> None:
        """
        Checks if the current metrics is updated and asserts if not changed.
        """
        current_metrics = self.metrics
        for i in range(self.ASSESSMENT_TRIES):
            current_metrics = HPA.get_hpa_current_metrics(self.name, self.namespace)
            logger.info(f"Try #{i + 1}/{self.ASSESSMENT_TRIES}, {self.name} Metrics: {current_metrics}")
            if current_metrics != self.metrics:
                break
            time.sleep(self.RETRY_INTERVAL)
        assert current_metrics != self.metrics, (f"{self.name}: HPA values have not changed: {current_metrics}")

    @staticmethod
    def get_hpa_current_metrics(hpa_name: str, hpa_namespace: str) -> Any:
        """Get current metrics for HPA object."""
        try:
            hpa_obj = kr8s.objects.HorizontalPodAutoscaler.get(hpa_name, namespace=hpa_namespace)
        except kr8s.NotFoundError as e:
            pytest.fail(f"HPA object {hpa_name} not found: {repr(e)}")

        try:
            if not hasattr(hpa_obj, 'status') or not hasattr(hpa_obj.status, 'currentMetrics'):
                pytest.fail(f"HPA object {hpa_name}: No current metrics available")
            current_metrics = hpa_obj.status.currentMetrics
            if not current_metrics:
                pytest.fail(f"HPA object {hpa_name}: Current metrics list is empty")
            return current_metrics[0].object.current
        except (KeyError, AttributeError, IndexError) as e:
            pytest.fail(f"HPA object {hpa_name}: Object's <unknown> state has been detected: {repr(e)}")


@allure.testcase("IEASG-T186")
def test_hpa(edp_helper, chatqa_api_helper, guard_helper):
    """Test horizontal pods autoscaling"""
    # Constants
    HPAS_WITH_INITIALLY_UNKNOWN_STATES = ["istio", "tei-reranking", "in-guard"]
    VLLM_HPA = "vllm"
    TORCHSERVE_R_HPA = "torchserve-reranking"
    TORCHSERVE_E_HPA = "torchserve-embedding"
    TORCHSERVE_HPA_IDENTIFIERS = {TORCHSERVE_R_HPA, TORCHSERVE_E_HPA}
    TRACKED_HPA_IDENTIFIERS = TORCHSERVE_HPA_IDENTIFIERS.union({VLLM_HPA})
    PROMETHEUS_POD = "prometheus-adapter"

    def get_hpas():
        return kr8s.get("horizontalpodautoscalers", namespace=kr8s.ALL)

    logger.info("Initial check to verify HPA objects creation...")
    try:
        kr8s.get("pod", PROMETHEUS_POD, namespace="monitoring")
    except kr8s.NotFoundError as e:
        pytest.skip(f"Can't detect {PROMETHEUS_POD} pod: {repr(e)}")

    # Fetch HPAs
    hpas = get_hpas()
    assert len(hpas) > 0, "No HPAs were found"

    # Initialize HPA objects dictionary to track them
    tracked_hpas = {}

    # Check HPAs
    for hpa in hpas:
        logger.info(f"HPA object: {hpa.metadata.name}")

        # Verify HPA configuration
        assert hpa.spec.maxReplicas >= hpa.spec.minReplicas, "Max replicas should be >= min replicas"

        # Analyze HPA object's metrics
        if any(sub in hpa.metadata.name for sub in HPAS_WITH_INITIALLY_UNKNOWN_STATES):
            logger.info("Skip metrics' analysis for this HPA object")
            continue

        hpa_object_metrics = HPA.get_hpa_current_metrics(hpa.name, hpa.namespace)
        logger.info(f"Metrics: {hpa_object_metrics}")

        # Save metrics that will have to be changed
        if hpa.metadata.name in TRACKED_HPA_IDENTIFIERS:
            tracked_hpas[hpa.metadata.name] = HPA(hpa.name, hpa.namespace, hpa_object_metrics)

    assert VLLM_HPA in tracked_hpas and tracked_hpas[VLLM_HPA].check_initialization(), (
        f"Failed to get initial HPA data for {VLLM_HPA}")

    logger.info(f"Check for HPA values changes on {tracked_hpas[VLLM_HPA].name} after a question...")
    gen_question = "Tell me a 1000 word story about the meaning of life"
    response = chatqa_api_helper.call_chatqa(gen_question)
    assert response.status_code == 200, (f"Request failed with status code: {response.status_code}, "
                                         f"Answer: {response.text}")

    if not tracked_hpas[VLLM_HPA].check_metrics_not_zero():
        tracked_hpas[VLLM_HPA].check_updated_hpa_values()

    logger.info("Recheck HPA objects' metrics after uploading a file and providing additional question...")
    file = "story.pdf"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.INPUT, "sentiment", guard_params)
    doc_based_question = "Is it true that Krystianooo found a backdoor?"
    guard_helper.assert_allowed(doc_based_question)
    status_code, response = guard_helper.call_chatqa(doc_based_question)
    assert status_code != 466, (f"Question: {doc_based_question}, "
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

        hpa_object_metrics = HPA.get_hpa_current_metrics(hpa.name, hpa.namespace)
        logger.info(f"Metrics: {hpa_object_metrics}")

        # Check for HPA values changes on torchserve
        if hpa.metadata.name in TORCHSERVE_HPA_IDENTIFIERS:
            assert hpa.metadata.name in tracked_hpas and tracked_hpas[hpa.metadata.name].check_initialization(), (
                f"{tracked_hpas[hpa.metadata.name].name}: missing initial data")
            if not tracked_hpas[hpa.metadata.name].check_metrics_not_zero():
                tracked_hpas[hpa.metadata.name].check_updated_hpa_values()
