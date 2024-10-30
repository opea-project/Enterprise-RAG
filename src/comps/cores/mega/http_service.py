# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import inspect
import time

from typing import Optional

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from uvicorn import Config, Server

from .base_service import BaseService
from .base_statistics import collect_all_statistics


def generate_lifespan(startup_methods: Optional[list], close_methods: Optional[list]):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if startup_methods is not None and isinstance(startup_methods, list):
            for method in startup_methods:
                if inspect.iscoroutinefunction(method):
                    await method()
                else:
                    method()

        yield

        if close_methods is not None and isinstance(close_methods, list):
            for method in close_methods:
                if inspect.iscoroutinefunction(method):
                    await method()
                else:
                    method()

    return lifespan


class HTTPService(BaseService):
    """FastAPI HTTP service based on BaseService class.

    This property should return a fastapi app.
    """

    def __init__(
        self,
        uvicorn_kwargs: Optional[dict] = None,
        cors: Optional[bool] = True,
        startup_methods: Optional[list] = None,
        close_methods: Optional[list] = None,
        validate_methods: Optional[list] = None,
        **kwargs,
    ):
        """Initialize the HTTPService
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server
        :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.

        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.uvicorn_kwargs = uvicorn_kwargs or {}
        self.cors = cors
        self.startup_methods = startup_methods
        self.close_methods = close_methods

        self.lifespan_func = None
        if self.startup_methods is not None and isinstance(self.startup_methods, list) or \
           self.close_methods is not None and isinstance(self.close_methods, list):
            self.lifespan_func = generate_lifespan(self.startup_methods, self.close_methods)

        self.last_time_third_party_validated = 0
        self.TIMEFRAME_FOR_CHECKS = 10*60 # 10 minutes
        self.validate_methods = validate_methods

        self._app = self._create_app()
        Instrumentator().instrument(self._app, latency_lowr_buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 7.5, 10, 30, 60)).expose(self._app)

    @property
    def app(self):
        """Get the default base API app for Server
        :return: Return a FastAPI app for the default HTTPGateway."""
        return self._app

    def _create_app(self):
        """Create a FastAPI application.

        :return: a FastAPI application.
        """
        app = FastAPI(title=self.title, description=self.description, lifespan=self.lifespan_func)

        if self.cors:
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            self.logger.info("CORS is enabled.")

        @app.get(
            path="/v1/health_check",
            summary="Get the status of GenAI microservice",
            tags=["Debug"],
        )

        async def _health_check():
            """Get the health status of this GenAI microservice."""
            if self.last_time_third_party_validated == 0 or time.time() - self.last_time_third_party_validated > self.TIMEFRAME_FOR_CHECKS:
                self.last_time_third_party_validated = time.time()
                if self.validate_methods is not None and isinstance(self.validate_methods, list):
                    for method in self.validate_methods:
                        if inspect.iscoroutinefunction(method):
                            await method()
                        else:
                            method()

            self.logger.debug(f"Health check successful. Last time since third party validation: {round(time.time() - self.last_time_third_party_validated, 2)} sec ago.")
            return {"Service Title": self.title, "Service Description": self.description}

        @app.get(
            path="/v1/statistics",
            summary="Get the statistics of GenAI services",
            tags=["Debug"],
        )
        async def _get_statistics():
            """Get the statistics of GenAI services."""
            result = collect_all_statistics()
            return result

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            self.logger.error(f"A validation error occured: {exc.errors()}. Check whether the request body and all fields you provided are correct.")
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}))

        return app

    async def initialize_server(self):
        """Initialize and return HTTP server."""
        self.logger.info("Setting up HTTP server")

        class UviServer(Server):
            """The uvicorn server."""

            async def setup_server(self, sockets=None):
                """Setup uvicorn server.

                :param sockets: sockets of server.
                """
                config = self.config
                if not config.loaded:
                    config.load()
                self.lifespan = config.lifespan_class(config)
                await self.startup(sockets=sockets)
                if self.should_exit:
                    return

            async def start_server(self, **kwargs):
                """Start the server.

                :param kwargs: keyword arguments
                """
                await self.main_loop()

        app = self.app

        self.server = UviServer(
            config=Config(
                app=app,
                host=self.host_address,
                port=self.primary_port,
                log_level="info",
                **self.uvicorn_kwargs,
            )
        )
        self.logger.info(f"Uvicorn server setup on port {self.primary_port}")
        await self.server.setup_server()
        self.logger.info("HTTP server setup successful")

    async def execute_server(self):
        """Run the HTTP server indefinitely."""
        await self.server.start_server()

    async def terminate_server(self):
        """Terminate the HTTP server and free resources allocated when setting up the server."""
        self.logger.info("Initiating server termination")
        self.server.should_exit = True
        await self.server.shutdown()
        self.logger.info("Server termination completed")

    @staticmethod
    def check_server_readiness(ctrl_address: str, timeout: float = 1.0, logger=None, **kwargs) -> bool:
        """Check if server status is ready.

        :param ctrl_address: the address where the control request needs to be sent
        :param timeout: timeout of the health check in seconds
        :param logger: Customized Logger to be used
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        import urllib.request
        from http import HTTPStatus

        try:
            conn = urllib.request.urlopen(url=f"http://{ctrl_address}", timeout=timeout) # nosec B310
            return conn.code == HTTPStatus.OK
        except Exception as exc:
            if logger:
                logger.info(f"Exception: {exc}")

            return False

    @staticmethod
    async def async_check_server_readiness(ctrl_address: str, timeout: float = 1.0, logger=None, **kwargs) -> bool:
        """Asynchronously check if server status is ready.

        :param ctrl_address: the address where the control request needs to be sent
        :param timeout: timeout of the health check in seconds
        :param logger: Customized Logger to be used
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        return HTTPService.check_server_readiness(ctrl_address, timeout, logger=logger)
