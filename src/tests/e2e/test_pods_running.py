#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import allure
import kr8s


@allure.testcase("IEASG-T27")
def test_pods_are_running():
    pods_not_running = []
    for pod in kr8s.get("pods", namespace=kr8s.ALL):
        if not pod.status.phase == "Running":
            pods_not_running.append(f"{pod.namespace}/{pod.name}")
    assert pods_not_running == [], "Some of the pods are not in running state"
