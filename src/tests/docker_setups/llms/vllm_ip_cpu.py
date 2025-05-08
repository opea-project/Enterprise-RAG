import logging
import os
import shutil
from enum import Enum
from typing import Type

from python_on_whales import Container, Image

from src.tests.docker_setups.base import LLMsDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LLMs_VllmIP_CPU_EnvKeys(Enum):
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


class LLMsVllmIP_CPU_DockerSetup(LLMsDockerSetup):
    """Implements VLLM with IPEX Docker setup"""

    MODELSERVER_CONTAINER_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-endpoint"
    MODELSERVER_IMAGE_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-vllm"

    MODELSERVER_PORT = 80

    VOLUMES = [("./data", "/data")]

    def __init__(
        self,
        golden_configuration_src: str,
        config_override: dict = None,
        custom_microservice_envs: dict = None,
        custom_microservice_docker_params: dict = None,
        custom_model_server_envs: dict = None,
        custom_model_server_docker_params: dict = None,
    ):
        super().__init__(
            golden_configuration_src,
            config_override,
            custom_microservice_envs,
            custom_microservice_docker_params,
            custom_model_server_envs,
            custom_model_server_docker_params,
        )

        # Also create directories for volumes.
        logger.debug(f"Start creating volume directories (UID={os.getuid()})")
        for volume_pair in self.VOLUMES:
            host_dir = volume_pair[0]
            try:
                os.makedirs(host_dir)
                logger.debug(f"Created {host_dir}.")
            except FileExistsError:
                logger.debug(f"Found existing directory {host_dir}. Will delete.")
                shutil.rmtree(host_dir)
                os.makedirs(host_dir)
                logger.debug(f"Created {host_dir}.")
        logger.info("Created volume directories.")

    @property
    def _ENV_KEYS(self) -> Type[LLMs_VllmIP_CPU_EnvKeys]:
        return LLMs_VllmIP_CPU_EnvKeys

    @property
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        return "Application startup complete"

    @property
    def _model_server_envs(self) -> dict:
        envs_keys = [
            self._ENV_KEYS.VLLM_CPU_KVCACHE_SPACE,
            self._ENV_KEYS.VLLM_DTYPE,
            self._ENV_KEYS.VLLM_MAX_NUM_SEQS,
            self._ENV_KEYS.VLLM_SKIP_WARMUP,
            self._ENV_KEYS.VLLM_TP_SIZE,
            self._ENV_KEYS.VLLM_PP_SIZE,
        ]

        env_vars = {
            env_key.value: self.get_docker_env(env_key) for env_key in envs_keys
        }
        env_vars["VLLM_OPENVINO_DEVICE"] = "CPU"
        return env_vars

    @property
    def _microservice_envs(self) -> dict:
        return {
            "LLM_MODEL_NAME": self.get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME),
            "LLM_MODEL_SERVER": "vllm",
            "LLM_MODEL_SERVER_ENDPOINT": f"http://{self._HOST_IP}:{self.INTERNAL_COMMUNICATION_PORT}",
        }

    def _build_model_server(self) -> Image:
        return self._build_image(
            self.MODELSERVER_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/llms/impl/model_server/vllm/docker/Dockerfile.cpu",
            context_path=f"{self._main_src_path}/comps/llms/impl/model_server/vllm/",
            build_args={
                "USER_UID": os.getuid()
            },  # Pass current user UID for docker non-priviledged user
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
            volumes=self.VOLUMES,
            command=[
                "--model",
                f"{self.get_docker_env(self._ENV_KEYS.LLM_VLLM_MODEL_NAME)}",
                "--device",
                "cpu",
                "--tensor-parallel-size",
                f"{self.get_docker_env(self._ENV_KEYS.VLLM_TP_SIZE)}",
                "--pipeline-parallel-size",
                f"{self.get_docker_env(self._ENV_KEYS.VLLM_PP_SIZE)}",
                "--dtype",
                f"{self.get_docker_env(self._ENV_KEYS.VLLM_DTYPE)}",
                "--max-num-seqs",
                f"{self.get_docker_env(self._ENV_KEYS.VLLM_MAX_NUM_SEQS)}",
                "--max-model-len",
                f"{self.get_docker_env(self._ENV_KEYS.VLLM_MAX_MODEL_LEN)}",
                "--download_dir",
                "/data",
                "--host",
                "0.0.0.0",
                "--port",
                f"{self.MODELSERVER_PORT}",
            ],
            wait_after=60,
            **self._model_server_docker_extras,
            **self.COMMON_RUN_OPTIONS,
        )
        return container

    def __del__(self):
        for volume_pair in self.VOLUMES:
            host_dir = volume_pair[0]
            try:
                shutil.rmtree(host_dir)
            except FileNotFoundError:
                pass
        logger.info("Docker volume directories removed")

        super().__del__()
