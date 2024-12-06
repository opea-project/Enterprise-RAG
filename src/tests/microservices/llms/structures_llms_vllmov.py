import logging
import os
from enum import Enum
from typing import Type

from python_on_whales import Container, Image, docker
from structures_base import LLMsDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LLMs_VllmOV_EnvKeys(Enum):
    """This struct declares all env variables from .env file.

    It is created to ensure env variables for testing are in sync with design by devs.
    """
    LLM_VLLM_MODEL_NAME = "LLM_VLLM_MODEL_NAME"
    LLM_VLLM_PORT = "LLM_VLLM_PORT"
    VLLM_CPU_KVCACHE_SPACE = "VLLM_CPU_KVCACHE_SPACE"
    VLLM_DTYPE = "VLLM_DTYPE"
    VLLM_MAX_NUM_SEQS = "VLLM_MAX_NUM_SEQS"
    VLLM_SKIP_WARMUP = "VLLM_SKIP_WARMUP"
    VLLM_TP_SIZE = "VLLM_TP_SIZE"
    VLLM_PP_SIZE = "VLLM_PP_SIZE"
    VLLM_MAX_MODEL_LEN = "VLLM_MAX_MODEL_LEN"

    VLLM_OPENVINO_KVCACHE_SPACE = "VLLM_OPENVINO_KVCACHE_SPACE"
    VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS = "VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS"
    VLLM_OPENVINO_CPU_KV_CACHE_PRECISION = "VLLM_OPENVINO_CPU_KV_CACHE_PRECISION"


class LLMsVllmOVDockerSetup(LLMsDockerSetup):
    """Implements VLLM with OpenVino Docker setup"""

    MODELSERVER_CONTAINER_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-endpoint"
    MODELSERVER_IMAGE_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-vllm"

    MODELSERVER_PORT = 80

    VLLM_REPOSITORY_URL = "https://github.com/vllm-project/vllm.git"
    VLLM_TAG = "v0.6.4.post1"

    @property
    def _ENV_KEYS(self) -> Type[LLMs_VllmOV_EnvKeys]:
        return LLMs_VllmOV_EnvKeys

    @property
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        return "Application startup complete"

    @property
    def _microservice_envs(self) -> dict:
        return {
            "LLM_MODEL_NAME": self._get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME),
            "LLM_MODEL_SERVER": "vllm",
            "LLM_MODEL_SERVER_ENDPOINT": f"http://{self._HOST_IP}:{self.INTERNAL_COMMUNICATION_PORT}",
        }

    @property
    def _model_server_envs(self) -> dict:
        envs = [
            self._ENV_KEYS.VLLM_CPU_KVCACHE_SPACE,
            self._ENV_KEYS.VLLM_DTYPE,
            self._ENV_KEYS.VLLM_MAX_NUM_SEQS,
            self._ENV_KEYS.VLLM_SKIP_WARMUP,
            self._ENV_KEYS.VLLM_TP_SIZE,
            self._ENV_KEYS.VLLM_PP_SIZE,
        ]

        return {env_key.value : self._get_docker_env(env_key) for env_key in envs}

    def _build_model_server(self) -> Image:
        """Customized build that replicates steps in following script:
        /src/comps/llms/impl/model_server/vllm/run_vllm.sh
        This is hopefully subject to simplify.
        """

        cmd = f"""
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker:stable sh -c "
            set -eo pipefail && \
            export HTTP_PROXY={LLMsVllmOVDockerSetup.COMMON_PROXY_SETTINGS["http_proxy"]} && \
            export HTTPS_PROXY={LLMsVllmOVDockerSetup.COMMON_PROXY_SETTINGS["https_proxy"]} && \
            export NO_PROXY={LLMsVllmOVDockerSetup.COMMON_PROXY_SETTINGS["no_proxy"]} && \
            apk add --no-cache git && \
            git clone https://github.com/vllm-project/vllm.git /workspace/vllm && \
            cd /workspace/vllm && \
            git -c advice.detachedHead=false checkout v0.6.4.post1 && \
            sed -i 's|pip install intel-openmp|pip install intel-openmp==2025.0.1|g' Dockerfile.cpu && \
            DOCKER_BUILDKIT=1 docker build -f Dockerfile.cpu -t {LLMsVllmOVDockerSetup.MODELSERVER_IMAGE_NAME} --shm-size=128g . --build-arg https_proxy=$HTTP_PROXY --build-arg http_proxy=$HTTPS_PROXY --build-arg no_proxy=$NO_PROXY
            "
        """
        logger.debug("Execute following command:")
        logger.debug(cmd)
        os.system(cmd)

        image = docker.image.inspect(LLMsVllmOVDockerSetup.MODELSERVER_IMAGE_NAME)

        return image

    def _run_model_server(self) -> Container:
        container = self._run_container(
            self.MODELSERVER_IMAGE_NAME,
            name=self.MODELSERVER_CONTAINER_NAME,
            publish=[
                (self.INTERNAL_COMMUNICATION_PORT, self.MODELSERVER_PORT),
            ],
            envs={
                "HF_TOKEN": os.environ["HF_TOKEN"],
                **self._model_server_envs,
                **self.COMMON_PROXY_SETTINGS,
            },
            volumes=[("./data", "/data")],
            command=[
                '--model',
                f'{self._get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME)}',
                "--host",
                "0.0.0.0",
                "--port",
                f"{self.MODELSERVER_PORT}"
            ],
            wait_after=60,
            **self.COMMON_RUN_OPTIONS,
        )
        return container
