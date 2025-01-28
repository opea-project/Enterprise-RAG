import logging
import os
from enum import Enum
from typing import Type

from python_on_whales import Container, Image
from src.tests.docker_setups.base import LLMsDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

class LLMs_VllmOV_CPU_EnvKeys(Enum):
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


class LLMsVllmOV_CPU_DockerSetup(LLMsDockerSetup):
    """Implements VLLM with OpenVino Docker setup"""

    MODELSERVER_CONTAINER_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-endpoint"
    MODELSERVER_IMAGE_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-vllm"

    MODELSERVER_PORT = 80

    @property
    def _ENV_KEYS(self) -> Type[LLMs_VllmOV_CPU_EnvKeys]:
        return LLMs_VllmOV_CPU_EnvKeys

    @property
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        return "Application startup complete"

    @property
    def _microservice_envs(self) -> dict:
        return {
            "LLM_MODEL_NAME": self.get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME),
            "LLM_MODEL_SERVER": "vllm",
            "LLM_MODEL_SERVER_ENDPOINT": f"http://{self._HOST_IP}:{self.INTERNAL_COMMUNICATION_PORT}",
        }

    @property
    def _model_server_envs(self) -> dict:
        envs_keys = [
            self._ENV_KEYS.VLLM_CPU_KVCACHE_SPACE,
            self._ENV_KEYS.VLLM_DTYPE,
            self._ENV_KEYS.VLLM_MAX_NUM_SEQS,
            self._ENV_KEYS.VLLM_SKIP_WARMUP,
            self._ENV_KEYS.VLLM_TP_SIZE,
            self._ENV_KEYS.VLLM_PP_SIZE,
            self._ENV_KEYS.VLLM_OPENVINO_KVCACHE_SPACE,
            self._ENV_KEYS.VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS,
            self._ENV_KEYS.VLLM_OPENVINO_CPU_KV_CACHE_PRECISION,
        ]

        env_vars = {env_key.value : self.get_docker_env(env_key) for env_key in envs_keys}
        env_vars["VLLM_OPENVINO_DEVICE"] = "CPU"
        return env_vars

    def _build_model_server(self) -> Image:
        return self._build_image(
            self.MODELSERVER_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/llms/impl/model_server/vllm/docker/Dockerfile.openvino",
            context_path=f"{self._main_src_path}/comps/llms/impl/model_server/vllm/",
            **self.COMMON_BUILD_OPTIONS,
        )

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
                **self._model_server_extra_envs,
                **self.COMMON_PROXY_SETTINGS,
            },
            command=[
                    "--model",
                    f"{self.get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME)}",
                    "--max-num-seqs",
                    f"{self.get_docker_env(self._ENV_KEYS.VLLM_MAX_NUM_SEQS)}",
                    "--max-model-len",
                    f"{self.get_docker_env(self._ENV_KEYS.VLLM_MAX_MODEL_LEN)}",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    f"{self.MODELSERVER_PORT}"
            ],
            wait_after=60,
            **self._model_server_docker_extras,
            **self.COMMON_RUN_OPTIONS,
        )
        return container
