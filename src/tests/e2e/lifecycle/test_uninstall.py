#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def temporarily_remove_user_required_actions():
    """Overrides the global session-scoped fixture with a no-op for uninstall tests."""
    pass


@pytest.fixture(scope="session", autouse=True)
def disable_guards_at_startup(guard_helper, suppress_logging, temporarily_remove_user_required_actions):
    """Overrides the global session-scoped fixture with a no-op for uninstall tests."""
    pass


@allure.testcase("IEASG-T309")
def test_uninstall(k8s_helper):
    """Verify that after uninstallation, only the allowed namespaces and no unexpected pods exist."""
    allowed_namespaces = ["default", "habana-system", "kube-system", "kube-public", "kube-node-lease", "local-path-storage"]
    current_namespaces = k8s_helper.list_namespaces()
    logger.debug(f"Namespaces in the cluster: {current_namespaces}")
    unexpected_ns = [ns for ns in current_namespaces if ns not in allowed_namespaces]
    assert not unexpected_ns, f"Unexpected namespaces found: {unexpected_ns}, expected only: {allowed_namespaces}"

    forbidden_pod_prefixes = ["rag-"]
    pods = k8s_helper.list_pods(namespace="default")
    logger.debug(f"Pods in 'default' namespace: {pods}")
    unexpected_pods = [pod.name for pod in pods if any(pod.name.startswith(prefix) for prefix in forbidden_pod_prefixes)]
    assert not unexpected_pods, f"Unexpected pods found in 'default' namespace: {unexpected_pods}"
