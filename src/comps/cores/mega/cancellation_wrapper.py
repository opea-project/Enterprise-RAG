from contextlib import asynccontextmanager
from typing import Optional

from anyio import create_task_group
from fastapi import Request

from .logger import get_opea_logger

logger = get_opea_logger("cancel_on_disconnect")

@asynccontextmanager
async def cancel_on_disconnect(request: Request):
    """
    Async context manager for async code that needs to be cancelled if client disconnects prematurely.
    The client disconnect is monitored through the Request object.
    Author: https://github.com/dorinclisu/runner-with-api/ (MIT License)
    """
    async with create_task_group() as tg:
        async def watch_disconnect():
            while True:
                message = await request.receive()

                if message['type'] == 'http.disconnect':
                    client = f'{request.client.host}:{request.client.port}' if request.client else '-:-'
                    logger.info(f'{client} - "{request.method} {request.url.path}" 499 DISCONNECTED')

                    tg.cancel_scope.cancel()
                    break

        tg.start_soon(watch_disconnect)

        try:
            yield
        finally:
            tg.cancel_scope.cancel()


@asynccontextmanager
async def maybe_cancel_on_disconnect(request: Optional[Request] = None):
    """
    Async context manager that optionally wraps operations with cancellation monitoring.
    If request is provided, monitors for client disconnect; otherwise acts as pass-through.

    Args:
        request: Optional FastAPI Request object for monitoring disconnections

    Example:
        async with maybe_cancel_on_disconnect(request):
            # Your async operations here
            await some_long_operation()
    """
    if request:
        async with cancel_on_disconnect(request):
            yield
    else:
        yield
