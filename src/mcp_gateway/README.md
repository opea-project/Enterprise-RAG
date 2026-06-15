# MCP Gateway Microservice

The MCP (Model Context Protocol) gateway exposes Intel® AI for Enterprise RAG capabilities as tools that AI agents can discover and call over a persistent SSE connection. It implements the MCP SSE transport and acts as the sole authentication boundary for agent traffic.

## Table of Contents

1. [MCP Gateway Microservice](#mcp-gateway-microservice)
2. [Overview](#overview)
3. [Available Tools](#available-tools)
4. [Configuration Options](#configuration-options)
5. [Getting Started](#getting-started)
   - 5.1. [🚀 Start MCP Gateway with Python (Option 1)](#-start-mcp-gateway-with-python-option-1)
     - 5.1.1. [Install Requirements](#install-requirements)
     - 5.1.2. [Start Microservice](#start-microservice)
   - 5.2. [🚀 Start MCP Gateway with Docker (Option 2)](#-start-mcp-gateway-with-docker-option-2)
     - 5.2.1. [Build the Docker Image](#build-the-docker-image)
     - 5.2.2. [Run the Docker Container](#run-the-docker-container)
   - 5.3. [Verify the MCP Gateway](#verify-the-mcp-gateway)
     - 5.3.1. [Health Check](#health-check)
     - 5.3.2. [List MCP Tools](#list-mcp-tools)
6. [Authentication](#authentication)

---

## Overview

The gateway translates MCP tool calls from AI agents into HTTP requests to internal Enterprise RAG services (EDP, SeaweedFS). Which tools are registered at startup depends on which backend endpoints are configured:

| Condition | Registered tools |
|-----------|-----------------|
| `EDP_ENDPOINT` set | `retrieve_context`, `list_buckets`, `ingest_url`, `ingest_file`, `check_ingestion_status` |

Tools not backed by a running service are not registered - agents see only what is available on their deployment.

Authentication is handled entirely by the gateway. Agents send their Keycloak `client_id` and `client_secret` directly in headers on SSE connect; the gateway exchanges them for a Keycloak token via `client_credentials` grant and handles all token refresh transparently.

---

## Available Tools

### `retrieve_context`
Retrieves ranked document chunks from the knowledge base without running the full LLM pipeline. Use when you want source passages or need to supply retrieved context to your own LLM.

**Requires:** `EDP_ENDPOINT`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Natural-language search phrase |
| `top_n` | integer | `5` | Number of ranked chunks to return if reranker is enabled. Ignored if reranker is false. |
| `k` | integer | `32` | Number of candidates to retrieve from retriever. Must be >= top_n for correct retrieval. Higher k may improve recall but increases latency. |
| `reranker` | boolean | `true` | Apply reranking; `false` for faster, less precise results |
| `search_type` | string | `"similarity"` | `similarity`, `similarity_search_with_siblings`, or `similarity_distance_threshold` |

### `list_buckets`
Lists all available buckets (collections) in the knowledge base. Call this before ingesting files to discover valid bucket names.

**Requires:** `EDP_ENDPOINT`

No parameters.

Returns: `list[str]` - bucket name strings.

### `ingest_url`
Ingests a URL into the knowledge base for processing. The EDP pipeline fetches the content, extracts text, chunks it, and generates embeddings. Processing starts asynchronously - the tool returns as soon as the URL is queued.

**Requires:** `EDP_ENDPOINT`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to ingest (e.g. `https://example.com/document.pdf`). Must be a valid http or https URL reachable by the EDP service. |

### `ingest_file`
Uploads base64-encoded file content directly into the knowledge base. Use for files you already have in memory; prefer `ingest_url` for URL-hosted files.

**Requires:** `EDP_ENDPOINT`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | string | required | Destination bucket name |
| `filename` | string | required | Object name in storage |
| `content_base64` | string | required | Base64-encoded file bytes (standard alphabet, padding required) |
| `content_type` | string | `"application/octet-stream"` | MIME type hint |

### `check_ingestion_status`
Check processing status of files and URLs in knowledge base. Query by bucket/filename or url. Fetches only relevant data - files if bucket/filename/id provided, links if url/id provided, both if all params None.

**Requires:** `EDP_ENDPOINT`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | string | `None` | Filter files by bucket name |
| `id` | string | `None` | Filter by unique ID (fetches both files and links when provided) |
| `filename` | string | `None` | Filter files by object name |
| `url` | string | `None` | Filter links by URL |

Returns: `list[dict]` - file entries contain `id`, `bucket_name`, `object_name`, `status`, `chunks_total`, `chunks_processed`, `job_message`, `created_at`, `size`. Link entries contain `id`, `uri`, `status`, `chunks_total`, `chunks_processed`, `job_message`, `created_at`.

Status values: `uploaded`, `processing`, `ingested`, `error`, `deleting`, `canceled`.

---

## Configuration Options

Settings are read from environment variables. The `impl/microservice/.env` file provides development defaults; in production all values are injected via Helm at deploy time.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KEYCLOAK_TOKEN_ENDPOINT` | Yes | (none) | Keycloak token URL, e.g. `http://keycloak-http.auth.svc/realms/EnterpriseRAG/protocol/openid-connect/token` |
| `EDP_ENDPOINT` | Yes | (none) | Internal EDP backend URL. Required - MCP gateway exposes only EDP retrieval/ingestion tools. |
| `MCP_SERVER_HOST` | No | `0.0.0.0` | Host address the server binds to |
| `MCP_SERVER_PORT` | No | `8000` | Port the server listens on |
| `S3_TLS_VERIFY` | No | `true` | Set to `false` to disable TLS verification for S3 storage (dev only) |
| `MCP_MAX_SESSIONS` | No | `100` | Maximum concurrent SSE sessions (DoS protection) |
| `MCP_MAX_SESSIONS_PER_CLIENT` | No | `5` | Maximum sessions per client_id (per-client DoS protection) |
| `MCP_SESSION_INACTIVITY_TIMEOUT` | No | `600` | Seconds before idle sessions are closed (prevents orphaned sessions) |
| `SSL_CERT_FILE` | No | (certifi default) | Path to CA certificate bundle for TLS verification |
| `OPEA_LOGGER_LEVEL` | No | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Getting Started

There are 2 ways to run this microservice:
  - [via Python](#-start-mcp-gateway-with-python-option-1)
  - [via Docker](#-start-mcp-gateway-with-docker-option-2) **(recommended)**

### 🚀 Start MCP Gateway with Python (Option 1)

#### Install Requirements
To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml --group security-overrides
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python mcp_gateway.py
```

### 🚀 Start MCP Gateway with Docker (Option 2)

#### Build the Docker Image
Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../../
docker build -t opea/mcp-gateway:latest -f mcp_gateway/impl/microservice/Dockerfile .
```

#### Run the Docker Container

```bash
docker run -d --name="mcp-gateway" \
  --net=host \
  --ipc=host \
  opea/mcp-gateway
```

If the backend services are running at different endpoints than the default, update the environment variables accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
docker run -d --name="mcp-gateway" \
  -e KEYCLOAK_TOKEN_ENDPOINT=http://<keycloak-host>/realms/EnterpriseRAG/protocol/openid-connect/token \
  -e EDP_ENDPOINT=http://<edp-host>:5000 \
  --net=host \
  --ipc=host \
  opea/mcp-gateway
```

### Verify the MCP Gateway

#### Health Check

```bash
curl http://localhost:8000/api/v1/mcp/health \
  -X GET \
  -H 'Content-Type: application/json'
```

#### List MCP Tools

```bash
curl -N http://localhost:8000/api/v1/mcp/sse \
  -H "X-MCP-Client-ID: <client-id>" \
  -H "X-MCP-Client-Secret: <client-secret>"
```

---

## Authentication

Agents authenticate by sending their Keycloak client credentials as HTTP headers on the SSE connect request:

```
GET /api/v1/mcp/sse
X-MCP-Client-ID: <keycloak-client-id>
X-MCP-Client-Secret: <keycloak-client-secret>
```

The gateway exchanges these for a Keycloak access token via `client_credentials` grant, holds the secret in memory only for the duration of the session (for transparent token refresh), and discards it on disconnect. Agents never need to obtain or manage tokens themselves.

**Each production agent should use a dedicated Keycloak client** configured as:
- `serviceAccountsEnabled: true`
- `standardFlowEnabled: false`
- `directAccessGrantsEnabled: false`
- Service account assigned `ERAG-user` (or `ERAG-admin`) role on `EnterpriseRAG-oidc-backend`
- For `ingest_file`: service account assigned `erag-admin-group` on `EnterpriseRAG-oidc-minio` + `minio_roles` claim mapper

When deployed via Ansible with `mcp.enabled: true`, a ready-to-use `mcp-test-client` is created automatically. Its credentials are written to `deployment/ansible-logs/default_credentials.txt`.

See `docs/mcp_integration.md` for the full integration guide including production client setup and troubleshooting.
