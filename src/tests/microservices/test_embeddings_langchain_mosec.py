from http import HTTPStatus

import allure
import pytest
import requests

from src.tests.docker_setups.embeddings.langchain_mosec import (
    EmbeddingsLangchainMosecDockerSetup,
)


@pytest.fixture(scope="module")
def containers():
    containers = EmbeddingsLangchainMosecDockerSetup("comps/embeddings/impl/model_server/mosec/docker/.env")
    containers.deploy()

    yield containers

    del containers


@allure.testcase("IEASG-T3")
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


@allure.testcase("IEASG-T59")
@pytest.mark.embeddings
def test_empty_body_golden(containers):
    url = (
        f"http://{containers._HOST_IP}:{containers.MICROSERVICE_API_PORT}/v1/embeddings"
    )
    request_body = {}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=request_body, headers=headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, (
        "Incorrect response status code"
    )
