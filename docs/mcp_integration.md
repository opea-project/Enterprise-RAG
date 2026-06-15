# MCP Integration Guide

This guide covers deploying the Intel® AI for Enterprise RAG MCP gateway and connecting AI agents to it.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deploying with MCP Enabled](#deploying-with-mcp-enabled)
4. [Quick Start: Using the Test Client](#quick-start-using-the-test-client)
5. [Connecting an Agent](#connecting-an-agent)
   1. [Example: Python Agent Using the MCP SDK](#example-python-agent-using-the-mcp-sdk)
6. [Tool Reference](#tool-reference)
   1. [retrieve_context](#retrieve_context)
   2. [list_buckets](#list_buckets)
   3. [ingest_url](#ingest_url)
   4. [ingest_file](#ingest_file)
   5. [check_ingestion_status](#check_ingestion_status)
7. [Creating a Production Agent Client in Keycloak](#creating-a-production-agent-client-in-keycloak)
   1. [Using the Keycloak Admin Console](#using-the-keycloak-admin-console)
8. [Security Notes](#security-notes)

## Overview

The MCP (Model Context Protocol) gateway exposes Intel® AI for Enterprise RAG capabilities as tools that AI agents can discover and invoke over a persistent SSE connection. Available tools depend on which backend services are deployed:

| Tool | Requires | Description |
|------|----------|-------------|
| `retrieve_context` | EDP | Retrieve ranked document chunks from the knowledge base |
| `list_buckets` | EDP | List all available buckets (collections) in the knowledge base |
| `ingest_url` | EDP | Ingest a URL into the knowledge base for processing |
| `ingest_file` | EDP | Upload a file from base64-encoded content into a knowledge base bucket |
| `check_ingestion_status` | EDP | Check processing status of ingested files |

All tools at the moment require EDP to be deployed. Tools not backed by a running service are not registered.

Authentication is handled entirely by the MCP gateway. APISIX forwards traffic on `/api/v1/mcp/*` without JWT validation - the gateway is the sole auth boundary.

Agents authenticate by sending their Keycloak `client_id` and `client_secret` directly in request headers. The gateway exchanges these for a Keycloak token on SSE connect and handles all token refresh transparently. Agents never need to obtain or manage tokens themselves. The exchanged token is used for all backend calls (EDP, SeaweedFS) for that session.

## Prerequisites

- Kubernetes cluster provisioned and kubeconfig configured
- APISIX enabled (`apisix.enabled: true` in `config.yaml`)
- Inventory config prepared at `deployment/inventory/<cluster-name>/config.yaml`

## Deploying with MCP Enabled

Enable the MCP gateway before running the application playbook for the first time by setting `mcp.enabled: true` in your inventory config:

```yaml
# deployment/inventory/<cluster-name>/config.yaml
mcp:
  enabled: true
```

Then deploy Intel® AI for Enterprise RAG as usual, by using instructions in [docs](../deployment/README.md).

The playbook will automatically:

1. Run the Keycloak configurator job, which creates the `mcp-test-client` Keycloak client (service accounts enabled, Standard flow and implicit flow disabled) with `ERAG-user` role and S3 read/write permissions (`erag-admin-group` on `EnterpriseRAG-oidc-minio`)
2. Write `MCP_TEST_CLIENT_ID` and `MCP_TEST_CLIENT_SECRET` to `deployment/ansible-logs/default_credentials.txt`
3. Deploy the MCP gateway pod in the `mcp-gateway` namespace
4. Register the `/api/v1/mcp/*` route in APISIX (without JWT validation - the gateway handles auth)

## Quick Start: Using the Test Client

When MCP is enabled, the deployment automatically creates a ready-to-use `mcp-test-client` Keycloak service account with `ERAG-user` role. Its credentials are written to `deployment/ansible-logs/default_credentials.txt`.

Retrieve the credentials:

```bash
grep MCP_TEST deployment/ansible-logs/default_credentials.txt
# MCP_TEST_CLIENT_ID=mcp-test-client
# MCP_TEST_CLIENT_SECRET="<generated-secret>"
```

> [!NOTE]
> `mcp-test-client` is intended for development and testing only. For production integrations, create a dedicated client as described in [Creating a Production Agent Client in Keycloak](#creating-a-production-agent-client-in-keycloak).

## Connecting an Agent

Agents connect by passing their Keycloak `client_id` and `client_secret` as HTTP headers on the SSE connect request. No token acquisition is required - the gateway handles Keycloak token exchange and refresh internally.

```
GET https://erag.com/api/v1/mcp/sse
X-MCP-Client-ID: <your-client-id>
X-MCP-Client-Secret: <your-client-secret>
```

The headers are transmitted over TLS and are never logged by the gateway. The `client_secret` is held in memory only for the duration of the SSE session (for token refresh), then discarded on disconnect.

```bash
# Connect with curl (for testing - add --no-buffer for streaming)
curl -N "https://erag.com/api/v1/mcp/sse" \
  -H "X-MCP-Client-ID: mcp-test-client" \
  -H "X-MCP-Client-Secret: <value from default_credentials.txt>"
```

The agent receives the MCP `initialize` handshake followed by a `tools/list` response describing all available tools.

### Example: Python Agent Using the MCP SDK

```python
import asyncio
import base64
import httpx
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

MCP_URL = "https://erag.com/api/v1/mcp/sse"
CLIENT_ID = "mcp-test-client"      # or your production client
CLIENT_SECRET = "..."              # from default_credentials.txt or your own client


async def main():
    # Pass credentials directly - the gateway exchanges them for a Keycloak token
    headers = {
        "X-MCP-Client-ID": CLIENT_ID,
        "X-MCP-Client-Secret": CLIENT_SECRET,
    }

    async with sse_client(MCP_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools (depends on which pipelines are deployed)
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

            # Retrieve document chunks
            result = await session.call_tool(
                "retrieve_context",
                {"query": "What is the data retention policy?", "top_n": 3},
            )
            print(result.content)

            # Discover available buckets
            buckets = await session.call_tool("list_buckets", {})
            print(buckets.content)


asyncio.run(main())
```

## Tool Reference

### `retrieve_context`

Retrieves ranked document chunks from the knowledge base without generating an LLM answer. Use this when you want to supply retrieved context to your own LLM or inspect raw retrieval results.

**Requires:** EDP service. This tool is not registered when `EDP_ENDPOINT` is not configured.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Natural-language search phrase |
| `top_n` | integer | `5` | Number of ranked chunks to return if reranker is enabled. Ignored if reranker is false. |
| `k` | integer | `32` | Number of candidates to retrieve from retriever. Must be >= top_n for correct retrieval. Higher k may improve recall but increases latency. |
| `reranker` | boolean | `true` | Apply reranking step; set `false` for faster but less precise results |
| `search_type` | string | `"similarity"` | Vector search algorithm - see values below |

`search_type` values:

| Value | Description |
|-------|-------------|
| `"similarity"` | Cosine similarity search (default) |
| `"similarity_search_with_siblings"` | Cosine search that also returns adjacent chunks for better context continuity |
| `"similarity_distance_threshold"` | Cosine search with a maximum distance filter |

Returns: `list[dict]` - each item has `text` (string) and `metadata` (dict) fields, ordered by relevance descending.

### `list_buckets`

Lists all available buckets (collections) in the knowledge base. Call this before ingesting files to discover valid bucket names.

**Requires:** EDP service.

No parameters.

Returns: `list[str]` - bucket name strings.

### `ingest_url`

Ingests a URL into the knowledge base for processing. The EDP pipeline fetches the content, extracts text, chunks it, and generates embeddings. Processing starts asynchronously - this tool returns as soon as the URL is queued.

**Requires:** EDP service.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to ingest (e.g. `https://example.com/document.pdf`). Must be a valid http or https URL reachable by the EDP service. |

Returns: `dict` with `message` and `id` (list of link IDs created in the ingestion queue).

> [!NOTE]
> The URL must be reachable from within the cluster. For files behind external authentication or files you already have as bytes, use `ingest_file` instead.

### `ingest_file`

Uploads a file into the knowledge base from base64-encoded content. Use this when you already have the file bytes (e.g. a generated report, an attachment, or a small locally available file). For files hosted at a URL, prefer `ingest_url`.

**Requires:** EDP service.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | string | required | Destination bucket (collection) name |
| `filename` | string | required | Object name to store the file as (e.g. `reports/q1.pdf`) |
| `content_base64` | string | required | Base64-encoded file bytes (standard alphabet with padding) |
| `content_type` | string | `"application/octet-stream"` | MIME type hint for the processing pipeline |

Returns: `dict` with `bucket`, `filename`, and `status: "ingestion_started"`.

> [!NOTE]
> Files above ~50 MB may hit the 120 s upload timeout. base64 encoding adds ~33% overhead over the raw file size.

### `check_ingestion_status`

Check processing status of files and URLs in the knowledge base. Query by bucket/filename (for files) or url (for links). To reduce overhead, the tool only fetches files if bucket/filename/id provided, and only fetches links if url/id provided. If all parameters are None, fetches both files and links. Use this to monitor progress after calling `ingest_url` or `ingest_file`.

**Requires:** EDP service.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | string | `None` | Filter files by bucket name. If all parameters are None, returns all files and links. |
| `id` | string | `None` | Filter files and URLs by unique ID. If provided, fetches both files and links. |
| `filename` | string | `None` | Filter files by object name. When provided without bucket, matches filename across all buckets. |
| `url` | string | `None` | Filter links by URL. |

Returns: `list[dict]` - file entries contain `id`, `bucket_name`, `object_name`, `status`, `chunks_total`, `chunks_processed`, `job_message`, `created_at`, and `size`. Link entries contain `id`, `uri`, `status`, `chunks_total`, `chunks_processed`, `job_message`, `created_at`.

Status values: `uploaded`, `processing`, `ingested`, `error`, `deleting`, `canceled`.

## Creating a Production Agent Client in Keycloak

The `mcp-test-client` is for development only. For production integrations, create a dedicated client per agent so credentials can be rotated or revoked independently. Each production client needs three things: ERAG role (for backend access), `erag-admin-group` on `EnterpriseRAG-oidc-minio` (for S3 file operations), and a `minio_roles` claim mapper.

### Using the Keycloak Admin Console

1. Log in to `https://auth.erag.com` → select the **EnterpriseRAG** realm
2. Navigate to **Clients** → **Create client**
3. Set a **Client ID** (e.g. `my-agent`)
4. Enable **Client authentication** (disables public client mode)
5. Disable **Standard flow** and **Direct access grants**
6. Enable **Service accounts roles** → **Save**
7. Open the **Credentials** tab and copy the client secret
8. Open the **Service accounts roles** tab → **Assign role** → select `ERAG-admin`, `ERAG-user`, or `ERAG-maintainer` as appropriate
9. To enable `ingest_url` and `ingest_file`: go to **Clients → EnterpriseRAG-oidc-minio → Service account roles** for `service-account-my-agent` → assign `erag-admin-group`
10. Add a **Client scope mapper**: **Clients → my-agent → Client scopes → Add mapper → By configuration → User Client Role** → set Token Claim Name to `minio_roles`, Client ID to `EnterpriseRAG-oidc-minio`

## Security Notes

- **Do not use `mcp-test-client` in production.** It exists for initial testing only - create a dedicated client per agent for production integrations.
- **Revoke a compromised agent** by disabling or deleting its Keycloak client - other agents are unaffected.
- **The `X-MCP-Client-Secret` header** is transmitted over TLS and never logged by the gateway. The secret is held in gateway memory only for the duration of the SSE session (for token refresh) and is discarded on disconnect. Do not connect without TLS at the ingress.
- **Production agent clients must have `erag-admin-group` on `EnterpriseRAG-oidc-minio`** and a `minio_roles` claim mapper for `ingest_url` and `ingest_file` to work. See [Creating a Production Agent Client in Keycloak](#creating-a-production-agent-client-in-keycloak) for the required setup steps.
- **Token lifetime** is governed by the Keycloak realm's access token lifespan (default 5 minutes). The gateway handles refresh automatically before expiry.
- The MCP gateway pod runs as a non-root user with `readOnlyRootFilesystem: true` and `capabilities.drop: ALL`.
