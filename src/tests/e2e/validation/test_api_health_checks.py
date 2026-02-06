#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
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
                selector = {"app.kubernetes.io/name": pod.metadata.labels.get("app.kubernetes.io/name")}
                if pod.metadata.labels.get("app.kubernetes.io/component"):
                    selector["app.kubernetes.io/component"] = pod.metadata.labels.get("app.kubernetes.io/component")
                container_port = None
                if isinstance(port_name, int):
                    # Port may be specified as a number or as a name
                    container_port = port_name
                else:
                    for port in container.ports:
                        if port.name == port_name:
                            container_port = port.containerPort
                            break
                svcs.append({"selector": selector,
                             "namespace": ns,
                             "port": container_port,
                             "health_path": path})

    failed_microservices = []
    for service in svcs:
        try:
            response = generic_api_helper.call_health_check_api(
                service['namespace'], service['selector'], service['port'], service['health_path'])

            if response.status_code != 200:
                error_msg = (
                    f"Health check failed for {service['selector']}. "
                    f"Status Code: {response.status_code}, "
                    f"Response Body: {response.text}"
                )
                logger.error(error_msg)
                assert response.status_code == 200, error_msg

        except (AssertionError, requests.exceptions.RequestException) as e:
            logger.warning(f"Error during health check for {service['selector']}: {e}")
            failed_microservices.append(service)

    assert failed_microservices == [], f"Health check failed for services: {failed_microservices}"
