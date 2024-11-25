import requests
from http import HTTPStatus

import logging
import allure

import pytest
from python_on_whales import Container, Image


from structures_base import EmbeddingsDockerSetup


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EmbeddingsLangchainMosecDockerSetup(EmbeddingsDockerSetup):

    CONTAINER_NAME_BASE = "test-comps-embeddings"

    ENDPOINT_CONTAINER_NAME = f"{CONTAINER_NAME_BASE}-endpoint"
    ENDPOINT_IMAGE_NAME = f"opea/{ENDPOINT_CONTAINER_NAME}:comps"

    MICROSERVICE_API_PORT = 5002
    MICROSERVICE_CONTAINER_NAME = f"{CONTAINER_NAME_BASE}-microservice"
    MICROSERVICE_IMAGE_NAME = f"opea/{MICROSERVICE_CONTAINER_NAME}:comps"

    INTERNAL_COMMUNICATION_PORT = 5001
    MODEL_SERVER_PORT = 8000

    API_ENDPOINT = "/v1/embeddings"

    @property
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        return "http service is running"

    def _build_model_server(self) -> Image:
        return self._build_image(
            self.ENDPOINT_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/embeddings/impl/model-server/mosec/docker/Dockerfile",
            context_path=f"{self._main_src_path}/comps/embeddings/impl/model-server/mosec/",
            **self.COMMON_BUILD_OPTIONS,
        )

    def _build_microservice(self) -> Image:
        return self._build_image(
            self.MICROSERVICE_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/embeddings/impl/microservice/Dockerfile",
            context_path=f"{self._main_src_path}",
            **self.COMMON_BUILD_OPTIONS,
        )

    def _run_model_server(self) -> Container:
        container = self._run_container(
            self.ENDPOINT_IMAGE_NAME,
            name=self.ENDPOINT_CONTAINER_NAME,
            cap_add=["SYS_NICE"],
            runtime="runc",
            publish=[
                (self.INTERNAL_COMMUNICATION_PORT, self.MODEL_SERVER_PORT),
            ],
            # TODO: Load from .env file
            envs={
                "MOSEC_PORT": 8000,
                "MOSEC_MODEL_NAME": "BAAI/bge-large-en-v1.5",
                "EMBEDDING_CONNECTOR": "langchain",
                "MOSEC_AMP_DTYPE": "BF16",
                "MOSEC_MAX_BATCH_SIZE": 32,
                "MOSEC_MAX_WAIT_TIME": 100,
                **self.COMMON_PROXY_SETTINGS,
            },
            remove=False,
            wait_after=60,
            **self.COMMON_RUN_OPTIONS,
        )
        return container

    def _run_microservice(self) -> Container:
        container = self._run_container(
            self.MICROSERVICE_IMAGE_NAME,
            name=self.MICROSERVICE_CONTAINER_NAME,
            ipc="host",  # We should get rid of it as it weakens isolation
            runtime="runc",
            publish=[
                (self.MICROSERVICE_API_PORT, 6000),
            ],
            envs={
                "EMBEDDING_MODEL_NAME": "BAAI/bge-large-zh",
                "EMBEDDING_MODEL_SERVER": "mosec",
                "EMBEDDING_CONNECTOR": "langchain",
                "EMBEDDING_MODEL_SERVER_ENDPOINT": f"http://{self._HOST_IP}:{self.INTERNAL_COMMUNICATION_PORT}",
                **self.COMMON_PROXY_SETTINGS,
            },
            wait_after=15,
            **self.COMMON_RUN_OPTIONS,
        )
        return container


@pytest.fixture(scope="module")
def containers():
    containers = EmbeddingsLangchainMosecDockerSetup()
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

    assert (
        response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    ), "Incorrect response status code"
