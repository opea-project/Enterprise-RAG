#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import allure
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


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T26")
def test_api_health_checks(generic_api_helper):
    failed_microservices = []
    for service in SERVICES:
        try:
            response = generic_api_helper.call_health_check_api(
                service['namespace'], service['selector'], service['port'])
            assert response.status_code == 200, \
                f"Got unexpected status code for {service['selector']} health check API call"
            response.json()
        except (AssertionError, requests.exceptions.RequestException) as e:
            print(e)
            failed_microservices.append(service)

    assert failed_microservices == [], "/v1/health_check API call didn't succeed for some microservices"
