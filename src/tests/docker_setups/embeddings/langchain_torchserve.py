import logging
from enum import Enum
from typing import Type

from python_on_whales import Container, Image

from src.tests.docker_setups.base import EmbeddingsDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Embeddings_Langchain_Torchserve_EnvKeys(Enum):
    """This struct declares all env variables from .env file.

    It is created to ensure env variables for testing are in sync with design by devs.
    """

    TORCHSERVE_PORT = "TORCHSERVE_PORT"
    TORCHSERVE_MGMT_PORT = "TORCHSERVE_MGMT_PORT"
    TORCHSERVE_METRICS_PORT = "TORCHSERVE_METRICS_PORT"
    TORCHSERVE_MODEL_NAME = "TORCHSERVE_MODEL_NAME"
    EMBEDDING_CONNECTOR = "EMBEDDING_CONNECTOR"
    TORCHSERVE_BATCH_SIZE = "TORCHSERVE_BATCH_SIZE"
    TORCHSERVE_AMP_DTYPE = "TORCHSERVE_AMP_DTYPE"
    TORCHSERVE_MIN_WORKERS = "TORCHSERVE_MIN_WORKERS"
    TORCHSERVE_MAX_WORKERS = "TORCHSERVE_MAX_WORKERS"
    TORCHSERVE_MAX_BATCH_DELAY = "TORCHSERVE_MAX_BATCH_DELAY"
    TORCHSERVE_RESPONSE_TIMEOUT = "TORCHSERVE_RESPONSE_TIMEOUT"
    OMP_NUM_THREADS = "OMP_NUM_THREADS"


class EmbeddingsLangchainTorchserveDockerSetup(EmbeddingsDockerSetup):
    ENDPOINT_CONTAINER_NAME = f"{EmbeddingsDockerSetup.CONTAINER_NAME_BASE}-endpoint"
    ENDPOINT_IMAGE_NAME = f"opea/{ENDPOINT_CONTAINER_NAME}:comps"

    @property
    def MODEL_SERVER_PORT(self):
        return self.get_docker_env(self._ENV_KEYS.TORCHSERVE_PORT)

    @property
    def _ENV_KEYS(self) -> Type[Embeddings_Langchain_Torchserve_EnvKeys]:
        return Embeddings_Langchain_Torchserve_EnvKeys

    @property
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        return "WORKER_MODEL_LOADED"

    @property
    def _model_server_envs(self) -> dict:
        envs = [
            self._ENV_KEYS.TORCHSERVE_AMP_DTYPE,
            self._ENV_KEYS.TORCHSERVE_BATCH_SIZE,
            self._ENV_KEYS.TORCHSERVE_MAX_BATCH_DELAY,
            self._ENV_KEYS.TORCHSERVE_MAX_WORKERS,
            self._ENV_KEYS.TORCHSERVE_MIN_WORKERS,
            self._ENV_KEYS.TORCHSERVE_MODEL_NAME,
            self._ENV_KEYS.TORCHSERVE_RESPONSE_TIMEOUT,
        ]

        env_vars = {env_key.value: self.get_docker_env(env_key) for env_key in envs}
        env_vars["VLLM_OPENVINO_DEVICE"] = "CPU"
        return env_vars

    @property
    def _microservice_envs(self) -> dict:
        return {
            "EMBEDDING_CONNECTOR": self.get_docker_env(
                self._ENV_KEYS.EMBEDDING_CONNECTOR
            ),
            "EMBEDDING_MODEL_NAME": self.get_docker_env(
                self._ENV_KEYS.TORCHSERVE_MODEL_NAME
            ),
            "EMBEDDING_MODEL_SERVER": "torchserve",
            "EMBEDDING_MODEL_SERVER_ENDPOINT": f"http://{self._HOST_IP}:{self.INTERNAL_COMMUNICATION_PORT}",
        }

    def _build_model_server(self) -> Image:
        return self._build_image(
            self.ENDPOINT_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/embeddings/impl/model-server/torchserve/docker/Dockerfile",
            context_path=f"{self._main_src_path}/comps/embeddings/impl/model-server/torchserve/",
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
            envs={
                **self._model_server_envs,
                **self._model_server_extra_envs,
                **self.COMMON_PROXY_SETTINGS,
            },
            wait_after=60,
            **self.COMMON_RUN_OPTIONS,
        )
        return container
