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
    For each service check if the health check API returns HTTP status code 200
    """
    svcs = []
    pods = kr8s.get("pods", namespace=kr8s.ALL)
    for pod in pods:
        container = pod.spec.containers[0]
        if container.get('livenessProbe'):
            lp = container.get('livenessProbe')
            path = lp.get("httpGet", {}).get("path")
            port_name = lp.get("httpGet", {}).get("port")
            if path == "v1/health_check":
                selector = pod.metadata.labels.get("app.kubernetes.io/name")
                ns = pod.metadata.namespace
                for port in container.ports:
                    if port.name == port_name:
                        container_port = port.containerPort
                        svcs.append({"selector": {"app.kubernetes.io/name": selector}, "namespace": ns, "port": container_port})

    failed_microservices = []
    for service in svcs:
        try:
            response = generic_api_helper.call_health_check_api(
                service['namespace'], service['selector'], service['port'])
            assert response.status_code == 200, \
                f"Got unexpected status code for {service['selector']} health check API call"
            response.json()
        except (AssertionError, requests.exceptions.RequestException) as e:
            logger.warning(e)
            failed_microservices.append(service)

    assert failed_microservices == [], "/v1/health_check API call didn't succeed for some microservices"
