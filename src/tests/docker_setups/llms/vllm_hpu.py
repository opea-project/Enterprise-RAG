import logging
import os
from enum import Enum
from typing import Type

from python_on_whales import Container, Image
from src.tests.docker_setups.base import LLMsDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LLMs_VLLM_HPU_EnvKeys(Enum):
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
    HABANA_VISIBLE_DEVICES = "HABANA_VISIBLE_DEVICES"
    SHARDED = "SHARDED"
    NUM_SHARD = "NUM_SHARD"
    OMPI_MCA_btl_vader_single_copy_mechanism = "OMPI_MCA_btl_vader_single_copy_mechanism"
    PT_HPU_ENABLE_LAZY_COLLECTIVES = "PT_HPU_ENABLE_LAZY_COLLECTIVES"
    PT_HPU_LAZY_ACC_PAR_MODE = "PT_HPU_LAZY_ACC_PAR_MODE"


class LLMsVllm_HPU_DockerSetup(LLMsDockerSetup):

    MODELSERVER_CONTAINER_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-endpoint"
    MODELSERVER_IMAGE_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-vllm"

    MODELSERVER_PORT = 80

    @property
    def _ENV_KEYS(self) -> Type[LLMs_VLLM_HPU_EnvKeys]:
        return LLMs_VLLM_HPU_EnvKeys

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
        envs = [
            self._ENV_KEYS.HABANA_VISIBLE_DEVICES,
            self._ENV_KEYS.SHARDED,
            self._ENV_KEYS.NUM_SHARD,
            self._ENV_KEYS.OMPI_MCA_btl_vader_single_copy_mechanism,
            self._ENV_KEYS.PT_HPU_ENABLE_LAZY_COLLECTIVES,
            self._ENV_KEYS.PT_HPU_LAZY_ACC_PAR_MODE,
            self._ENV_KEYS.VLLM_CPU_KVCACHE_SPACE,
            self._ENV_KEYS.VLLM_SKIP_WARMUP
        ]

        return {env_key.value : self.get_docker_env(env_key) for env_key in envs}

    def _build_model_server(self) -> Image:
        return self._build_image(
            self.MODELSERVER_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/llms/impl/model_server/vllm/docker/Dockerfile.hpu",
            context_path=f"{self._main_src_path}/comps/llms/impl/model_server/vllm/",
            **self.COMMON_BUILD_OPTIONS,
        )

    def _run_model_server(self) -> Container:
        container = self._run_container(
            self.MODELSERVER_IMAGE_NAME,
            name=self.MODELSERVER_CONTAINER_NAME,
            ipc="host",  # We should get rid of it as it weakens isolation
            cap_add=["sys_nice"],
            publish=[
                (self.INTERNAL_COMMUNICATION_PORT, self.MODELSERVER_PORT),
            ],
            envs={
                "HF_TOKEN": os.environ["HF_TOKEN"],
                **self._model_server_envs,
                **self._model_server_extra_envs,
                **self.COMMON_PROXY_SETTINGS,
            },
            volumes=[("./data", "/data")],
            command=[
                '/bin/bash',
                '-c',
                f"python3 -m vllm.entrypoints.openai.api_server --model {self.get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME)} --device hpu --tensor-parallel-size {self.get_docker_env(self._ENV_KEYS.VLLM_TP_SIZE)} --pipeline-parallel-size 1 --dtype {self.get_docker_env(self._ENV_KEYS.VLLM_DTYPE)} --max-num-seqs {self.get_docker_env(self._ENV_KEYS.VLLM_MAX_NUM_SEQS)} --host 0.0.0.0 --port 80"
            ],
            wait_after=60,
            runtime="habana",
            **self._model_server_docker_extras,
            **self.COMMON_RUN_OPTIONS,
        )
        return container
