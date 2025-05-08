#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from http import HTTPStatus

import allure
import pytest
import requests

from src.tests.docker_setups.embeddings.langchain_torchserve import (
    EmbeddingsLangchainTorchserveDockerSetup,
)


@pytest.fixture(scope="module")
def containers():
    containers = EmbeddingsLangchainTorchserveDockerSetup(
        "comps/embeddings/impl/model-server/torchserve/docker/.env"
    )
    containers.deploy()

    yield containers

    del containers


@allure.testcase("IEASG-T7")
@pytest.mark.embeddings
def test_simple_scenario_golden(containers):
    """Validates most expected positive scenario."""
    url = (
        f"http://{containers._HOST_IP}:{containers.MICROSERVICE_API_PORT}/v1/embeddings"
    )
    request_body = {"text": "What is Deep Learning?"}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=request_body, headers=headers)

    assert response.status_code == HTTPStatus.OK, "Incorrect response status code"
