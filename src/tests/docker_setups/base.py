import os
from abc import ABC, abstractmethod
import socket
from enum import Enum
from typing import Type

import python_on_whales
from python_on_whales import docker, Container, Image
import logging
from dotenv import dotenv_values
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseDockerSetup(ABC):

    _images: list[Image]
    _containers: list[Container]

    COMMON_BUILD_OPTIONS = {
        "cache": True,
        "progress": "plain",
    }

    COMMON_RUN_OPTIONS = {
        "detach": True,
    }

    COMMON_PROXY_SETTINGS = {
        "http_proxy": os.getenv(
            "http_proxy", ""
        ),  # None as default is passed to container causing proxy error
        "https_proxy": os.getenv("https_proxy", ""),
        "no_proxy": os.getenv("no_proxy", ""),
    }

    def __init__(self, config_override: dict = None):
        """

        For overriding docker containers, use key of image name.
        """
        pwd = os.path.dirname(__file__)
        self._main_src_path = os.path.join(pwd, "../..")

        self._images = []
        self._containers = []
        self._config_override = config_override

    def deploy(self):
        self.build_images()
        self.run_services()
        self.check_containers()

    @abstractmethod
    def build_images(self):
        pass

    @abstractmethod
    def run_services(self):
        pass

    def check_containers(self):
        """Verify if all containers are in "running" state."""

        failed_containers = False

        for c in self._containers:
            try:
                self._check_container(c)
            except RuntimeError:
                logger.debug("Exception caught and registered. Will continue checking remaining containers.")
                failed_containers = True

        if failed_containers:
            logger.critical(
                "There are failed containers. Raising error to break all tests."
            )
            raise RuntimeError("There are failed containers")

    @property
    def _HOST_IP(self):
        """
        Function to provide host ip for docker network communication through host.

        Note:
            This value is needed due to old way of communication between dockers that uses host.
            It is to be refactored into either docker-compose or more sophisticated network solutions.
            AFAIK function below should return proper host ip unless specific configuration in /etc/hosts
        """
        ip = socket.gethostbyname(socket.gethostname())
        if ip == "127.0.0.1":
            raise ValueError("Improper host id, need to fix")
        return ip

    def _build_image(self, image_name: str, **kwargs) -> Image:
        """Docker API wrapper function for build.

        If an error happens during build, function is run again with enabled streaming.
        Because it's impossible to have both returned object and log stream iterator.
        Also, so far no way found to get the normal streaming into log.
        """
        logger.debug(f"Run build of image {image_name}")
        try:
            return docker.build(tags=image_name, **kwargs)  # returned type is Image
        except python_on_whales.exceptions.DockerException as e:
            logger.critical("Error when building image. Rerun with streaming...")
            try:
                for log_msg in docker.build(
                    tags=image_name, stream_logs=True, **kwargs
                ):  # returned type is Iterator[str]
                    logger.error(log_msg)
            except python_on_whales.exceptions.DockerException:
                pass
            raise e

    def _pull_image(self, image_name: str) -> Image:
        return docker.pull(image_name)

    def _run_container(self, image_name: str, wait_after: int = 0, **kwargs) -> Container:
        """Docker API wrapper function for run.

        :param str image_name: Docker image name, required by target function
        :param int wait_after: wait in seconds after container is run (optional, default 0)
        :param dict **kwargs: rest of arguments for target function
        :return: Container object (from python_on_whales lib)
        """

        try:
            kwargs["env"].update(self._config_override[image_name]["run"])
        except (KeyError, TypeError):
            pass

        container = docker.run(image=image_name, **kwargs)
        logger.info(f"Container {image_name} started.")
        if wait_after > 0:
            logger.debug(f"Wait {wait_after}s for container to get up.")
            time.sleep(wait_after)

        return container

    def _check_container(self, container: Container):
        """Verify if the container is in "running" state."""

        if container.state.status != "running":
            logger.error(f"Container {container.name} failed. Print logs:")
            logger.error(container.logs())
            logger.critical(
                "There are failed containers. Raising error to break all tests."
            )
            raise RuntimeError("There are failed containers")

    def destroy(self):
        """Execute this manually when you cannot rely on destructor."""
        logger.debug("Executing DockerSetup destruction")

        docker.container.stop(self._containers)
        docker.container.remove(self._containers)
        self._containers = []

        docker.image.remove(self._images)
        self._images = []

    def __del__(self):
        self.destroy()


class LanguageUsvcDockerSetup(BaseDockerSetup):

    _model_server_img: Image
    _microservice_img: Image

    _model_server_container: Container
    _microservice_container: Container

    def __init__(
        self,
        golden_configuration_src: str,
        config_override: dict = None,
        custom_microservice_envs: dict = None,
        custom_microservice_docker_params: dict = None,
        custom_model_server_envs: dict = None,
        custom_model_server_docker_params: dict = None
    ):
        """
        :param str golden_configuration_src: Path to .env, with respect to src root
        :param dict config_override: Overrides of golden configuration
        :param dict custom_microservice_envs: Add your own ENV variables (aside from .env file) for microservice
        :param dict custom_microservice_docker_params: Add your own docker flags for microservice
        :param dict custom_model_server_envs: Add your own ENV variables (aside from .env file) for model server
        :param dict custom_model_server_docker_params: Add your own docker flags for model server
        """
        super().__init__(config_override)
        self._model_server_img = None
        self._microservice_img = None
        self._model_server_container = None
        self._microservice_container = None

        self._docker_conf = None

        self._load_golden_configuration(golden_configuration_src)
        self._microservice_extra_envs = custom_microservice_envs if custom_microservice_envs else dict()
        self._microservice_docker_extras = custom_microservice_docker_params if custom_microservice_docker_params else dict()
        self._model_server_extra_envs = custom_model_server_envs if custom_model_server_envs else dict()
        self._model_server_docker_extras = custom_model_server_docker_params if custom_model_server_docker_params else dict()

    @property
    @abstractmethod
    def _microservice_envs(self) -> dict:
        """ Microservice itself is same for all microservices,
         of same Language Components (LLMs, Embeddings), but differently configured. """
        pass

    @property
    @abstractmethod
    def _MODEL_SERVER_READINESS_MSG(self) -> str:
        """ String to search for in readiness checks. Implement this in child classes. """
        pass

    @property
    @abstractmethod
    def _ENV_KEYS(self) -> Type[Enum]:
        """Links the object of env keys for concrete model server configuration."""
        pass

    def build_images(self):
        self._model_server_img = self._build_model_server()
        self._images.append(self._model_server_img)

        self._microservice_img = self._build_microservice()
        self._images.append(self._microservice_img)

    def run_services(self):
        try:
            self._model_server_container = self._run_model_server()
            self._containers.append(self._model_server_container)
            self._wait_for(self._model_server_container, self._MODEL_SERVER_READINESS_MSG, timeout=3600, check_every=120)

            self._microservice_container = self._run_microservice()
            self._containers.append(self._microservice_container)

        except python_on_whales.exceptions.DockerException as e:
            logger.error("Error when starting containers on command:")
            logger.error(e.docker_command)
            logger.error("STDOUT:")
            logger.error(e.stdout)
            logger.error("STDERR:")
            logger.error(e.stderr)
            raise

    def get_docker_env(self, key_member) -> str:
        """Get value from golden configuration or it's overrider value"""
        key = key_member.value
        try:
            value = self._config_override[key]
            logger.debug(f"Found {key} in config overrides. {key}={value}")
        except (TypeError, KeyError):   # When override is None or key does not exist
            value = self._docker_conf[key]
            logger.debug(f"Using {key} from golden configuration. {key}={value}")
        return value

    def _wait_for(self, container: Container, str_to_find: str, timeout: int = 300, check_every: int = 15):
        """Polls container logs until finds a string or reach timeout"""

        start_time = time.time()
        elapsed = 0

        logger.debug(f"Running readiness check for container {container.name}")
        while elapsed < timeout:
            elapsed = int(time.time() - start_time)
            str_logs = container.logs(tail=100)
            self._check_container(container)
            if str_to_find in str_logs:
                logger.info(f"Readiness string \"{str_to_find}\" found in {container.name} in {elapsed}s")
                return True

            logger.debug(f"\"{str_to_find}\" not found in {container.name}. Elapsed {elapsed}/{timeout}s. Retry in {check_every}s")
            time.sleep(check_every)

        logger.error("Timeout reached. String not found. Raising exception")
        raise TimeoutError

    def _load_golden_configuration(self, golden_configuration_src: str):
        """Loads default env variables provided by developers.

        :param str golden_configuration_src: Path to .env, with respect to src root
        """

        file_path = os.path.join(self._main_src_path, golden_configuration_src)
        self._docker_conf = dotenv_values(file_path)
        self._validate_golden_configuration()
        logger.info("Loaded .env golden configuration:")
        logger.info(self._docker_conf)

    def _validate_golden_configuration(self):
        """Verify if all required env vars has been loaded."""
        for member in self._ENV_KEYS:
            key_name = member.value
            assert key_name in self._docker_conf, f"{key_name} not found in configuration"

    @abstractmethod
    def _build_model_server(self):
        pass

    @abstractmethod
    def _build_microservice(self):
        pass

    @abstractmethod
    def _run_model_server(self) -> Container:
        pass

    @abstractmethod
    def _run_microservice(self) -> Container:
        pass


class EmbeddingsDockerSetup(LanguageUsvcDockerSetup):

    CONTAINER_NAME_BASE = "test-comps-embeddings"

    MICROSERVICE_CONTAINER_NAME = f"{CONTAINER_NAME_BASE}-microservice"
    MICROSERVICE_IMAGE_NAME = f"opea/{MICROSERVICE_CONTAINER_NAME}:comps"
    MICROSERVICE_API_PORT = 5002
    MICROSERVICE_API_ENDPOINT = "/v1/embeddings"

    INTERNAL_COMMUNICATION_PORT = 5001

    def _build_microservice(self) -> Image:
        return self._build_image(
            self.MICROSERVICE_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/embeddings/impl/microservice/Dockerfile",
            context_path=f"{self._main_src_path}",
            **self.COMMON_BUILD_OPTIONS,
        )

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
                **self._microservice_envs,
                **self.COMMON_PROXY_SETTINGS,
            },
            wait_after=15,
            **self.COMMON_RUN_OPTIONS,
        )
        return container

class LLMsDockerSetup(LanguageUsvcDockerSetup):

    CONTAINER_NAME_BASE = "test-comps-llms"

    MICROSERVICE_CONTAINER_NAME = f"{CONTAINER_NAME_BASE}-microservice"
    MICROSERVICE_IMAGE_NAME = f"opea/{MICROSERVICE_CONTAINER_NAME}:comps"
    MICROSERVICE_API_PORT = 5002
    MICROSERVICE_API_ENDPOINT = "/v1/chat/completions"

    INTERNAL_COMMUNICATION_PORT = 5001



    def _build_microservice(self):
        return self._build_image(
            self.MICROSERVICE_IMAGE_NAME,
            file=f"{self._main_src_path}/comps/llms/impl/microservice/Dockerfile",
            context_path=f"{self._main_src_path}",
            **self.COMMON_BUILD_OPTIONS,
        )

    def _run_microservice(self) -> Container:
        container = self._run_container(
            self.MICROSERVICE_IMAGE_NAME,
            name=self.MICROSERVICE_CONTAINER_NAME,
            ipc="host",  # We should get rid of it as it weakens isolation
            runtime="runc",
            publish=[
                (self.MICROSERVICE_API_PORT, 9000),
            ],
            envs={
                **self._microservice_envs,
                **self._microservice_extra_envs,
                **self.COMMON_PROXY_SETTINGS,
            },
            wait_after=30,
            **self._microservice_docker_extras,
            **self.COMMON_RUN_OPTIONS,
        )
        return container
