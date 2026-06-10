# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import httpx
import time
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger("mcp_gateway")

# ContextVar holding the session_id for the current request, used to look up
# per-session token state without propagating secrets across async boundaries.
_current_session_id: ContextVar[str | None] = ContextVar("_current_session_id", default=None)

# Session state holds only client credentials - tokens fetched on demand per tool call.
# Entries removed when SSE connection closes.
_session_state: dict[str, dict] = {}


async def cleanup_inactive_sessions(timeout: int) -> None:
    """Background task - close sessions idle beyond timeout."""
    while True:
        await asyncio.sleep(60)
        now = time.monotonic()
        to_remove = []
        for sid, state in list(_session_state.items()):
            if sid.startswith("__pending__"):
                continue
            last_activity = state.get("last_activity", now)
            if now - last_activity > timeout:
                to_remove.append(sid)
        for sid in to_remove:
            _session_state.pop(sid, None)
            logger.info(f"Session {sid[:16]} closed due to inactivity")


async def _fetch_token_for_session(session_id: str, keycloak_token_endpoint: str) -> str:
    """Exchange session credentials for a fresh Keycloak token.

    Tokens fetched on-demand per tool call - not stored in _session_state.
    Reduces security risk by minimizing token lifetime in memory.
    """
    state = _session_state[session_id]
    client_id = state["client_id"]
    client_secret = state["client_secret"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                keycloak_token_endpoint,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
        r.raise_for_status()
    except Exception as exc:
        # Redact secret from exception message before logging
        exc_str = str(exc).replace(client_secret, "***") if client_secret and client_secret in str(exc) else str(exc)
        logger.error(f"Token exchange failed: {exc_str}")
        raise

    state["last_activity"] = time.monotonic()
    return r.json()["access_token"]


async def get_access_token(keycloak_token_endpoint: str) -> str:
    """Fetch a fresh access token for the current session.

    Tokens fetched on-demand per call - no caching. This minimizes token exposure window.
    Raises RuntimeError if called outside an authenticated session context.
    """
    session_id = _current_session_id.get()
    # If the ContextVar holds a placeholder key that has already been re-keyed to a UUID,
    # fall back to scanning for a state entry whose client_id matches - this handles the
    # case where the tool handler task inherited the placeholder before re-keying.
    state = _session_state.get(session_id) if session_id else None
    if state is None and session_id and session_id.startswith("__pending__"):
        # Extract the client_id embedded in the placeholder and find the live entry
        parts = session_id.split("__")
        if len(parts) >= 3:
            client_id = parts[2]
            for sid, s in _session_state.items():
                if s.get("client_id") == client_id:
                    state = s
                    session_id = sid  # use real key for _fetch_token_for_session
                    _current_session_id.set(sid)
                    break
    if state is None:
        raise RuntimeError("No active session - X-MCP-Client-ID / X-MCP-Client-Secret not provided")

    async with state["lock"]:
        return await _fetch_token_for_session(session_id, keycloak_token_endpoint)


async def _send_json_response(send: Send, status: int, body: str) -> None:
    encoded = body.encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(encoded)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": encoded, "more_body": False})


class CallerCredentialsMiddleware:
    """Auth enforcement and credential exchange for MCP connections.

    Pure ASGI middleware (no BaseHTTPMiddleware) so that SSE streaming works correctly -
    BaseHTTPMiddleware buffers the response body which breaks long-lived SSE connections.

    On SSE connect (GET .../sse):
      - Requires X-MCP-Client-ID + X-MCP-Client-Secret headers.
      - Validates credentials via immediate token exchange.
      - Intercepts the first SSE 'endpoint' event to learn FastMCP's session UUID,
        then stores credentials under that UUID for tool call authentication.
      - Removes state on disconnect.

    On tool call (POST .../messages/?session_id=<uuid>):
      - Looks up _session_state by session_id, sets _current_session_id ContextVar.
      - get_access_token() fetches a fresh token per call (not cached).

    APISIX skip_auth is set for the MCP route - this middleware is the sole auth boundary.
    """

    def __init__(
        self,
        app: ASGIApp,
        keycloak_token_endpoint: str,
        max_concurrent_sessions: int,
        max_sessions_per_client: int,
    ) -> None:
        self.app = app
        self.keycloak_token_endpoint = keycloak_token_endpoint
        self.max_concurrent_sessions = max_concurrent_sessions
        self.max_sessions_per_client = max_sessions_per_client

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "").rstrip("/")
        headers = dict(scope.get("headers", []))
        is_sse = path.endswith("/sse")

        if is_sse:
            client_id = headers.get(b"x-mcp-client-id", b"").decode().strip()
            client_secret = headers.get(b"x-mcp-client-secret", b"").decode().strip()

            if not client_id or not client_secret:
                await _send_json_response(
                    send,
                    status=401,
                    body='{"error":"unauthorized","detail":"Provide X-MCP-Client-ID and X-MCP-Client-Secret headers"}',
                )
                return

            if len(_session_state) >= self.max_concurrent_sessions:
                await _send_json_response(
                    send,
                    status=503,
                    body='{"error":"too_many_sessions","detail":"Maximum concurrent sessions reached"}',
                )
                return

            # Per-client session limit - count active sessions for this client_id
            client_count = sum(1 for s in _session_state.values() if s.get("client_id") == client_id)
            if client_count >= self.max_sessions_per_client:
                await _send_json_response(
                    send,
                    status=503,
                    body='{"error":"too_many_sessions_per_client","detail":"Maximum sessions per client reached"}',
                )
                return

            # Temporary key until FastMCP's endpoint event reveals the real session UUID.
            placeholder = f"__pending__{client_id}__{id(scope)}"
            lock = asyncio.Lock()
            _session_state[placeholder] = {
                "client_id": client_id,
                "client_secret": client_secret,
                "last_activity": time.monotonic(),
                "lock": lock,
            }

            # Validate credentials by attempting token exchange
            try:
                async with lock:
                    await _fetch_token_for_session(placeholder, self.keycloak_token_endpoint)
            except Exception as exc:
                _session_state.pop(placeholder, None)
                exc_str = str(exc).replace(client_secret, "***") if client_secret and client_secret in str(exc) else str(exc)
                logger.error(f"Token exchange failed for client {client_id}: {exc_str}")
                await _send_json_response(send, status=401, body='{"error":"invalid_client"}')
                return

            # Wrap `send` to intercept the SSE endpoint event and re-key the session.
            real_uuid: list[str] = []

            async def _send_wrapper(message: dict) -> None:
                if message["type"] == "http.response.body" and not real_uuid:
                    body = message.get("body", b"")
                    text = body.decode(errors="replace") if isinstance(body, bytes) else body
                    if "event: endpoint" in text and "session_id=" in text:
                        for line in text.splitlines():
                            line = line.strip()
                            if line.startswith("data:") and "session_id=" in line:
                                uuid_hex = line.split("session_id=")[-1].strip()
                                if uuid_hex and not uuid_hex.startswith("__pending__"):
                                    async with _session_state.get(placeholder, {}).get("lock", asyncio.Lock()):
                                        state = _session_state.pop(placeholder, None)
                                        if state is not None:
                                            _session_state[uuid_hex] = state
                                            real_uuid.append(uuid_hex)
                                            logger.info(f"Session {uuid_hex} mapped for client {client_id}")
                                break
                await send(message)

            ctx_token = _current_session_id.set(placeholder)
            try:
                await self.app(scope, receive, _send_wrapper)
            finally:
                _current_session_id.reset(ctx_token)
                sid = real_uuid[0] if real_uuid else placeholder
                _session_state.pop(sid, None) or _session_state.pop(placeholder, None)

        else:
            # POST /messages/?session_id=<uuid> - look up session from query string.
            query = scope.get("query_string", b"").decode()
            session_id: str | None = None
            for part in query.split("&"):
                if part.startswith("session_id="):
                    session_id = part[len("session_id="):]
                    break

            # Update last activity
            if session_id and session_id in _session_state:
                _session_state[session_id]["last_activity"] = time.monotonic()

            ctx_token = _current_session_id.set(session_id)
            try:
                await self.app(scope, receive, send)
            finally:
                _current_session_id.reset(ctx_token)
