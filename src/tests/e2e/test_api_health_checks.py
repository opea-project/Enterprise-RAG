#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import kr8s
import pytest
import requests

logger = logging.getLogger(__name__)


@pytest.mark.smoke
@allure.testcase("IEASG-T26")
def test_api_health_checks(generic_api_helper):
    """
    Find the services that expose /v1/health_check API.
    For each service check if the health check API returns HTTP status code 200.
    Omit pods in kube-system, monitoring, monitoring-traces and auth-apisix namespaces.
    """
    svcs = []
    pods = kr8s.get("pods", namespace=kr8s.ALL)
    for pod in pods:
        ns = pod.metadata.namespace
        if ns in ["kube-system", "monitoring", "auth-apisix", "monitoring-traces"]:
            continue
        container = pod.spec.containers[0]
        if container.get('livenessProbe'):
            lp = container.get('livenessProbe')
            path = lp.get("httpGet", {}).get("path")
            port_name = lp.get("httpGet", {}).get("port")
            if path in ["v1/health_check", "/v1/health_check", "/health", "/healthz"]:
                selector = pod.metadata.labels.get("app.kubernetes.io/name")
                container_port = None
                if isinstance(port_name, int):
                    # Port may be specified as a number or as a name
                    container_port = port_name
                else:
                    for port in container.ports:
                        if port.name == port_name:
                            container_port = port.containerPort
                            break
                svcs.append({"selector": {"app.kubernetes.io/name": selector},
                             "namespace": ns,
                             "port": container_port,
                             "health_path": path})

    failed_microservices = []
    for service in svcs:
        try:
            response = generic_api_helper.call_health_check_api(
                service['namespace'], service['selector'], service['port'], service['health_path'])
            assert response.status_code == 200, \
                f"Got unexpected status code for {service['selector']} health check API call"
        except (AssertionError, requests.exceptions.RequestException) as e:

            logger.warning(e)
            failed_microservices.append(service)

    assert failed_microservices == [], "/v1/health_check API call didn't succeed for some microservices"
