#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import allure
import kr8s
import pytest

@pytest.mark.smoke
@allure.testcase("IEASG-T27")
def test_pods_are_running():
    pods_not_running = []
    for pod in kr8s.get("pods", namespace=kr8s.ALL): # type: kr8s.api_resources.Pod
        # Skip pods owned by a Job
        if "ownerReferences" in pod.metadata:
            for owner in pod.metadata.ownerReferences:
                if "kind" in owner:
                    if owner.kind == "Job":
                        continue  # Skip this pod and move to the next iteration
        if not pod.status.phase == "Running" and not pod.status.phase == "Succeeded":
            pods_not_running.append(f"{pod.namespace}/{pod.name} is in {pod.status.phase}")
    assert pods_not_running == [], "Some of the pods are not in Running or Succeeded state"
