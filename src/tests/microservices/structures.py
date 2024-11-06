import os
from abc import ABC, abstractmethod
import socket
from time import sleep
import python_on_whales
from python_on_whales import docker, Container, Image
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseTest(ABC):

    _images: list[Image]
    _containers: list[Container]

    COMMON_BUILD_OPTIONS = {
        "cache": True,
        "progress": "plain",
    }

    COMMON_RUN_OPTIONS = {
        "runtime": "runc",
        "detach": True,
    }

    COMMON_PROXY_SETTINGS = {
        "http_proxy": os.getenv(
            "http_proxy", ""
        ),  # None as default is passed to container causing proxy error
        "https_proxy": os.getenv("https_proxy", ""),
        "no_proxy": os.getenv("no_proxy", ""),
    }

    def __init__(self):
        pwd = os.path.dirname(__file__)
        self._main_src_path = os.path.join(pwd, "../..")

        self._images = []
        self._containers = []

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
            if c.state.status != "running":
                failed_containers = True
                logger.error(f"Container {c.name} failed. Print logs:")
                logger.error(c.logs())

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

    def _build_image(self, **kwargs) -> Image:
        """Docker API wrapper function for build.

        If an error happens during build, function is run again with enabled streaming.
        Because it's impossible to have both returned object and log stream iterator.
        Also, so far no way found to get the normal streaming into log.
        """
        try:
            return docker.build(**kwargs)  # returned type is Image
        except python_on_whales.exceptions.DockerException as e:
            logger.critical("Error when building image. Rerun with streaming...")
            try:
                for log_msg in docker.build(
                    stream_logs=True, **kwargs
                ):  # returned type is Iterator[str]
                    logger.error(log_msg)
            except python_on_whales.exceptions.DockerException:
                pass
            raise e

    def _run_container(self, image: str, wait_after: int = 0, **kwargs) -> Container:
        """Docker API wrapper function for run.

        :param str image: Docker image name, required by target function
        :param int wait_after: wait in seconds after container is run (optional, default 0)
        :param dict **kwargs: rest of arguments for target function
        :return: Container object (from python_on_whales lib)
        """

        container = docker.run(image=image, **kwargs)
        logger.info(f"Container {image} started.")
        if wait_after > 0:
            logger.debug(f"Wait {wait_after}s for container to get up.")
            sleep(wait_after)

        return container

    def __del__(self):
        logger.debug("Running docker microservices destructor")
        docker.container.stop(self._containers)
        docker.container.remove(self._containers)
        docker.image.remove(self._images)


class EmbeddingsTest(BaseTest):

    _model_server_img: Image
    _microservice_img: Image

    _model_server_container: Container
    _microservice_container: Container

    def __init__(self):
        super().__init__()
        self._model_server_img = None
        self._microservice_img = None
        self._model_server_container = None
        self._microservice_container = None

    def build_images(self):
        self._model_server_img = self._build_model_server()
        self._images.append(self._model_server_img)

        self._microservice_img = self._build_microservice()
        self._images.append(self._microservice_img)

    def run_services(self):
        try:
            self._model_server_container = self._run_model_server()
            self._containers.append(self._model_server_container)

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
