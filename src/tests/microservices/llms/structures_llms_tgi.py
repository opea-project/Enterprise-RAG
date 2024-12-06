import logging
import os
from enum import Enum
from typing import Type

from python_on_whales import Container
from structures_base import LLMsDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LLMs_TGI_EnvKeys(Enum):
    """This struct declares all env variables from .env file.

    It is created to ensure env variables for testing are in sync with design by devs.
    """
    LLM_TGI_MODEL_NAME = "LLM_TGI_MODEL_NAME"
    LLM_TGI_PORT = "LLM_TGI_PORT"
    MAX_INPUT_TOKENS = "MAX_INPUT_TOKENS"
    MAX_TOTAL_TOKENS = "MAX_TOTAL_TOKENS"


class LLMsTgiDockerSetup(LLMsDockerSetup):
    """TGI has different docker images and .envs for platforms, but share the rest of the properties."""

    MODELSERVER_CONTAINER_NAME = f"{LLMsDockerSetup.CONTAINER_NAME_BASE}-endpoint"

    MODELSERVER_PORT = 80

    @property
    def _ENV_KEYS(self) -> Type[LLMs_TGI_EnvKeys]:
        return LLMs_TGI_EnvKeys

    @property
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        return "Connected"

    @property
    def _microservice_envs(self) -> dict:
        return {
            "LLM_MODEL_NAME": self._get_docker_env(self._ENV_KEYS.LLM_TGI_MODEL_NAME),
            "LLM_MODEL_SERVER": "tgi",
            "LLM_MODEL_SERVER_ENDPOINT": f"http://{self._HOST_IP}:{self.INTERNAL_COMMUNICATION_PORT}",
        }

    def __init__(self, model_server_img_url: str, golden_configuration_src: str, config_override: dict = None):
        super().__init__(golden_configuration_src, config_override)
        self._modelserver_image_name = model_server_img_url

    def _build_model_server(self):
        return self._pull_image(self._modelserver_image_name)

    def _run_model_server(self) -> Container:
        container = self._run_container(
            self._modelserver_image_name,
            name=self.MODELSERVER_CONTAINER_NAME,
            ipc="host",  # We should get rid of it as it weakens isolation
            publish=[
                (self.INTERNAL_COMMUNICATION_PORT, self.MODELSERVER_PORT),
            ],
            envs={
                "HF_TOKEN": os.environ["HF_TOKEN"],
                **self.COMMON_PROXY_SETTINGS,
            },
            volumes=[("./data", "/data")],
            command=[
                "--model-id",
                self._get_docker_env(self._ENV_KEYS.LLM_TGI_MODEL_NAME),
                "--max-input-tokens",
                self._get_docker_env(self._ENV_KEYS.MAX_INPUT_TOKENS),
                "--max-total-tokens",
                self._get_docker_env(self._ENV_KEYS.MAX_TOTAL_TOKENS),
            ],
            wait_after=60,
            **self.COMMON_RUN_OPTIONS,
        )
        return container
