#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import allure
import logging
import kr8s
import requests


SERVICES = [
    {"selector": "retriever-svc", "namespace": "chatqa", "port": 6620},
    {"selector": "reranking-svc", "namespace": "chatqa", "port": 8000},
    {"selector": "embedding-svc", "namespace": "chatqa", "port": 6000},
    {"selector": "embedding-svc", "namespace": "dataprep", "port": 6000},
    {"selector": "dataprep-usvc", "namespace": "dataprep", "port": 9399},
    {"selector": "ingestion-usvc", "namespace": "dataprep", "port": 6120},
    {"selector": "llm-svc", "namespace": "chatqa", "port": 9000}
]
IP_ADDRESS = "127.0.0.1"


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T26")
def test_api_health_checks():
    # Disable logs that are too verbose and make the output unclear
    logging.getLogger("httpcore").setLevel(logging.ERROR)

    failed_microservices = []

    for service in SERVICES:
        pods = kr8s.get("pods",
                        namespace=service["namespace"],
                        label_selector={"app": service["selector"]})

        with pods[0].portforward(remote_port=service["port"]) as local_port:
            headers = {"Content-Type": "application/json"}
            try:
                response = requests.get(
                    f"http://127.0.0.1:{local_port}/v1/health_check",
                    headers=headers
                )
                assert response.status_code == 200, \
                    f"Got unexpected status code for {service['selector']} health check API call"
                response.json()
            except (AssertionError, requests.exceptions.RequestException) as e:
                print(e)
                failed_microservices.append(service)

    assert failed_microservices == [], "/v1/health_check API call didn't succeed for some microservices"
