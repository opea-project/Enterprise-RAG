#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import os
import threading
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client

from tests.e2e.helpers.keycloak_helper import DEFAULT_CREDENTIALS_PATH
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

TOOL_CALL_TIMEOUT = 120


class McpHelper:
    """Helper for E2E testing the MCP gateway.

    MCP protocol uses SSE (Server-Sent Events) which requires holding an open
    HTTP connection to receive responses while sending requests via POST.
    This inherently needs async I/O or threading.

    This helper hides that complexity from synchronous test code by running a
    single persistent MCP session in a background thread. Tests call simple
    synchronous methods (list_tools, call_tool) which internally schedule work
    on the background event loop and block until the result arrives.

    Why a persistent session: the MCP gateway rate-limits new SSE connections.
    Opening a new session per test (19+ connects in ~60s) triggers 429 errors.
    One session for the whole suite avoids this entirely.

    Lifecycle:
        1. __init__  → background thread opens SSE connection + MCP handshake
        2. tests     → call list_tools() / call_tool() synchronously
        3. close()   → cancels background task, closes SSE connection
    """

    def __init__(self, credentials_file):
        fqdn = cfg.get("FQDN", "erag.com")
        self.mcp_sse_url = f"https://{fqdn}/api/v1/mcp/sse"
        self.mcp_health_url = f"https://{fqdn}/api/v1/mcp/health"
        self._credentials = self._load_mcp_credentials(credentials_file)
        self._loop = None
        self._thread = None
        self._session = None
        self._ready = threading.Event()
        self._start_session()

    def _load_mcp_credentials(self, credentials_file) -> dict[str, str]:
        """Parse MCP_TEST_CLIENT_ID and MCP_TEST_CLIENT_SECRET from the credentials file."""
        file_path = credentials_file if credentials_file and os.path.exists(credentials_file) else DEFAULT_CREDENTIALS_PATH
        credentials = {}
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    credentials[key.strip()] = value.strip().strip('"')
        return {
            "client_id": credentials.get("MCP_TEST_CLIENT_ID", ""),
            "client_secret": credentials.get("MCP_TEST_CLIENT_SECRET", ""),
        }

    @property
    def client_id(self) -> str:
        return self._credentials["client_id"]

    @property
    def client_secret(self) -> str:
        return self._credentials["client_secret"]

    def _httpx_client_factory(
        self,
        headers: dict | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
    ) -> httpx.AsyncClient:
        """Factory passed to sse_client — creates an httpx client with MCP auth headers.

        MCP gateway authenticates agents via X-MCP-Client-ID + X-MCP-Client-Secret
        headers (not Bearer tokens). The gateway exchanges these for a Keycloak token
        internally.
        """
        merged_headers = {
            "X-MCP-Client-ID": self.client_id,
            "X-MCP-Client-Secret": self.client_secret,
        }
        if headers:
            merged_headers.update(headers)
        return httpx.AsyncClient(
            verify=False,
            headers=merged_headers,
            timeout=timeout or httpx.Timeout(TOOL_CALL_TIMEOUT),
            auth=auth,
        )

    def _start_session(self):
        """Spin up background thread with an asyncio event loop running the MCP session.

        Blocks until the session is fully initialized (SSE connected + MCP handshake
        complete) or raises after 30s timeout.
        """
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_session, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=30):
            raise RuntimeError("MCP session failed to initialize within 30s")

    def _run_session(self):
        """Entry point for the background thread — just runs the event loop."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._session_lifecycle())

    async def _session_lifecycle(self):
        """The actual MCP session — opens SSE, handshakes, then sleeps forever.

        Steps:
          1. sse_client opens GET /sse → receives the POST endpoint URL
          2. ClientSession sends 'initialize' JSON-RPC → server confirms capabilities
          3. self._ready.set() signals the main thread that it can start using the session
          4. Infinite sleep keeps the SSE connection alive
          5. On CancelledError (from close()) the context managers clean up
        """
        async with sse_client(self.mcp_sse_url, httpx_client_factory=self._httpx_client_factory) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self._ready.set()
                try:
                    while True:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    pass

    def _run_in_session(self, coro_func):
        """Bridge between sync test code and the async session.

        Schedules the given async function on the background event loop, then
        blocks the calling (main) thread until the result is ready. This is how
        synchronous tests can use the async MCP SDK without themselves being async.
        """
        future = asyncio.run_coroutine_threadsafe(coro_func(), self._loop)
        return future.result(timeout=TOOL_CALL_TIMEOUT)

    def close(self):
        """Tear down the background session. Called by the pytest fixture on teardown."""
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(self._loop):
                self._loop.call_soon_threadsafe(task.cancel)
        if self._thread:
            self._thread.join(timeout=5)

    def check_health(self) -> int:
        """Simple GET to /health — does not use the MCP session at all."""
        with httpx.Client(verify=False, timeout=10) as client:
            r = client.get(self.mcp_health_url)
            return r.status_code

    def list_tools(self) -> list[str]:
        """Ask the MCP server what tools are available. Returns list of tool name strings."""
        async def _coro():
            tools_response = await self._session.list_tools()
            return [t.name for t in tools_response.tools]
        return self._run_in_session(_coro)

    def call_tool(self, tool_name: str, arguments: dict) -> tuple[bool, Any]:
        """Invoke an MCP tool and return (success, parsed_result).

        MCP SDK 1.27.2+ returns results with structuredContent field (parsed JSON)
        alongside legacy text content. Prefer structuredContent when available.

        Returns:
            (True, parsed_data) on success
            (False, raw_error_content) when the server reports isError=True
        """
        async def _coro():
            result = await self._session.call_tool(tool_name, arguments)
            if result.isError:
                return False, result.content

            # MCP SDK 1.27.2+ includes structuredContent with pre-parsed result
            if hasattr(result, "structuredContent") and result.structuredContent:
                structured = result.structuredContent
                # Gateway wraps all tool responses in {"result": [...]}
                if isinstance(structured, dict) and "result" in structured:
                    unwrapped = structured["result"]
                    # retrieve_context returns list with single retrieval object, unwrap for test compatibility
                    # Other tools (check_ingestion_status, list_buckets) return variable-length lists - keep as-is
                    if tool_name == "retrieve_context" and isinstance(unwrapped, list) and len(unwrapped) == 1:
                        return True, unwrapped[0]
                    return True, unwrapped
                return True, structured

            # Fallback: parse from text content (legacy behavior for older SDKs)
            content = result.content
            if not content:
                return True, None
            if len(content) == 1 and hasattr(content[0], "text"):
                text = content[0].text
                try:
                    parsed = json.loads(text)
                    # Gateway wraps in {"result": [...]}, unwrap it
                    if isinstance(parsed, dict) and "result" in parsed:
                        return True, parsed["result"]
                    return True, parsed
                except (json.JSONDecodeError, TypeError):
                    return True, text
            if all(hasattr(c, "text") for c in content):
                texts = [c.text for c in content]
                parsed = []
                for t in texts:
                    try:
                        parsed.append(json.loads(t))
                    except (json.JSONDecodeError, TypeError):
                        parsed.append(t)
                return True, parsed
            return True, content
        return self._run_in_session(_coro)

    def connect_with_invalid_credentials(self) -> bool:
        """Try to establish an MCP session with bogus credentials.

        Used by the negative auth test. Opens a completely separate connection
        (not the persistent session) with fake client_id/secret.

        Returns True if the gateway rejected the connection (expected behavior).
        Returns False if it somehow succeeded (test should fail).
        """
        try:
            asyncio.run(self._connect_invalid())
            return False
        except Exception:
            return True

    async def _connect_invalid(self):
        """Attempt full MCP handshake with invalid credentials — expected to raise."""
        def _invalid_factory(headers=None, timeout=None, auth=None):
            merged_headers = {
                "X-MCP-Client-ID": "invalid-client-id",
                "X-MCP-Client-Secret": "invalid-client-secret",
            }
            if headers:
                merged_headers.update(headers)
            return httpx.AsyncClient(
                verify=False,
                headers=merged_headers,
                timeout=timeout or httpx.Timeout(15),
                auth=auth,
            )

        async with sse_client(self.mcp_sse_url, httpx_client_factory=_invalid_factory) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.list_tools()
