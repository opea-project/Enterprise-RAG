# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import os

import httpx
import uvicorn
import validators
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger

from utils.auth import (
    CallerCredentialsMiddleware,
    cleanup_inactive_sessions,
    get_access_token,
)
from utils.helpers import build_ssl_context


load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger("mcp_gateway")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))
logger.info("Starting MCP Gateway microservice")

EDP_ENDPOINT = os.getenv("EDP_ENDPOINT", "")
KEYCLOAK_TOKEN_ENDPOINT = os.getenv("KEYCLOAK_TOKEN_ENDPOINT", "")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))
MCP_ROOT_PATH = os.getenv("MCP_ROOT_PATH", "")
S3_TLS_VERIFY = os.getenv("S3_TLS_VERIFY", "true").strip().lower() not in ("false", "0", "no")
MAX_CONCURRENT_SESSIONS = int(os.getenv("MCP_MAX_SESSIONS", "100"))
MAX_SESSIONS_PER_CLIENT = int(os.getenv("MCP_MAX_SESSIONS_PER_CLIENT", "5"))
SESSION_INACTIVITY_TIMEOUT = int(os.getenv("MCP_SESSION_INACTIVITY_TIMEOUT", "600"))  # 10 min

_S3_SSL_CONTEXT = build_ssl_context(S3_TLS_VERIFY)

# Configure transport security to allow requests from APISIX proxy
# MCP SDK validates Host header to prevent DNS rebinding attacks
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[
        "127.0.0.1:*",
        "localhost:*",
        "[::1]:*",
        "erag.com",
        "*.erag.com",
        "mcp-gateway-svc:*",
        "mcp-gateway-svc.*:*",
    ]
)

mcp = FastMCP(
    "erag-mcp",
    transport_security=transport_security,
    message_path="/api/v1/mcp/messages/",
)


if EDP_ENDPOINT:
    @mcp.tool()
    async def retrieve_context(
        query: str,
        top_n: int = 5,
        k: int = 32,
        reranker: bool = True,
        search_type: str = "similarity",
    ) -> list[dict]:
        """Retrieve relevant document chunks from the knowledge base.

        Use this tool to search the knowledge base before answering a question,
        or when you need source passages without running the full RAG pipeline.
        Returns an empty list if no relevant documents are found or if the
        knowledge base contains no ingested documents yet.

        Each returned chunk contains at minimum:
          - 'text': the passage text
          - 'metadata': dict with source file info (filename, bucket, page, etc.)

        Args:
            query: Natural-language question or search phrase.
            top_n: Number of ranked chunks to return (default 5) if reranker is enabled. Will be ignored if reranker is false.
            k: Number of candidates to retrieve from retriever (default 32).
               Must be >= top_n for correct retrieval. Higher k may improve recall but increases latency.
            reranker: Whether to apply the reranking step (default true).
                      Set false to skip reranking for faster but less precise results.
            search_type: Vector search algorithm. Supported values:
                         'similarity' - cosine similarity search (default).
                         'similarity_search_with_siblings' - cosine search that also
                           returns adjacent chunks for better context continuity.
                         'similarity_distance_threshold' - cosine search filtered by a
                           maximum distance; requires passing distance_threshold in the
                           EDP request (not exposed as a tool parameter).

        Returns:
            List of document chunk dicts, ordered by relevance score descending.
        """
        try:
            if not query or not query.strip():
                raise ValueError("Query parameter cannot be empty")

            payload = {
                "query": query,
                "reranker": reranker,
                "top_n": top_n,
                "search_type": search_type,
                "k": k,
                "score_threshold": 0.02,
            }
            logger.info(f"Received retrieve_context request with query: {query}, k: {k}, top_n: {top_n}, reranker: {reranker}, search_type: {search_type}")
            token = await get_access_token(KEYCLOAK_TOKEN_ENDPOINT)
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{EDP_ENDPOINT}/api/retrieve",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
            r.raise_for_status()
            result = r.json()
            # Handle different response formats from EDP
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # Try common keys
                docs = result.get("retrieved_docs") or result.get("docs") or result.get("documents")
                if docs is not None:
                    return docs if isinstance(docs, list) else [docs]
                # If no known key, wrap the dict
                return [result]
            return []
        except ValueError as exc:
            logger.error(f"retrieve_context validation error: {exc}")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.error(f"retrieve_context auth error: {exc}")
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(f"retrieve_context HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            logger.error(f"retrieve_context request error: {exc}")
            raise HTTPException(status_code=503, detail=f"EDP service unavailable: {exc}") from exc
        except Exception as exc:
            logger.error(f"retrieve_context unexpected error: {exc}")
            raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

else:
    logger.warning("EDP_ENDPOINT not set - retrieve_context not registered")


if EDP_ENDPOINT:
    @mcp.tool()
    async def ingest_url(url: str) -> dict:
        """Ingest a URL into the knowledge base for processing.

        This tool submits a URL to the Enhanced Data Preparation (EDP) pipeline, which
        fetches the content, extracts text, chunks it, and generates embeddings. The URL
        must point to content that EDP's web crawler can access (public web pages, PDFs,
        etc.). Processing starts asynchronously - this tool returns as soon as the URL
        is queued.

        To monitor processing progress, use the check_ingestion_status tool with the
        returned link ID or the URL. Processing typically takes 30-120 seconds depending
        on content size and system load.

        Use this tool for ingesting web pages, online documents, or any content accessible
        via HTTP/HTTPS. For files you already have as bytes, use ingest_file instead.

        Args:
            url: The URL to ingest (e.g. 'https://example.com/document.pdf').
                 Must be a valid http or https URL reachable by the EDP service.

        Returns:
            Dict with 'message' and 'id' (list of link IDs created in the ingestion queue).
        """
        try:
            if not validators.url(url):
                raise ValueError(f"Invalid URL: {url}")

            logger.info(f"Received ingest_url request with url: {url}")
            token = await get_access_token(KEYCLOAK_TOKEN_ENDPOINT)
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{EDP_ENDPOINT}/api/links",
                    json={"links": [url]},
                    headers=headers,
                )
                r.raise_for_status()

            response = r.json()
            return response
        except ValueError as exc:
            logger.error(f"ingest_url validation error: {exc}")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.error(f"ingest_url auth error: {exc}")
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(f"ingest_url HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            logger.error(f"ingest_url request error: {exc}")
            raise HTTPException(status_code=503, detail=f"EDP service unavailable: {exc}") from exc
        except Exception as exc:
            logger.error(f"ingest_url unexpected error: {exc}")
            raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    @mcp.tool()
    async def ingest_file(
        bucket: str,
        filename: str,
        content_base64: str,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Upload a file directly into the knowledge base from base64-encoded content.

        Use this tool when you already have the file bytes (e.g. a generated report,
        an attachment, or a small locally available file). Encode the bytes as base64
        and pass them as content_base64. For files hosted at a URL, prefer ingest_url.

        Processing (text extraction, chunking, embedding) starts automatically and
        runs asynchronously - this tool returns as soon as the upload completes.

        To monitor processing progress, use the check_ingestion_status tool with the
        bucket and filename. Processing typically takes 30-120 seconds depending on
        file size and system load. Note that a unique file ID is not available
        immediately - it is created when the storage backend webhook triggers EDP
        processing. Poll check_ingestion_status to discover the ID once processing
        begins.

        IMPORTANT: The bucket must already exist. Passing a non-existent bucket
        name will result in a 404 error. Call list_buckets first to discover
        available bucket names.

        Args:
            bucket: Destination bucket name (collection) in the knowledge base.
                    Must be an existing bucket - call list_buckets to discover
                    available names. Do not invent bucket names.
            filename: Object name to store the file as (e.g. 'reports/q1.pdf').
                      Must be unique within the bucket or the existing object will
                      be overwritten.
            content_base64: Base64-encoded file bytes (standard alphabet, padding
                            required).
            content_type: MIME type hint for the processing pipeline
                          (default 'application/octet-stream'). Use 'application/pdf'
                          for PDFs, 'text/plain' for plain text, etc.

        Returns:
            Dict with 'bucket', 'filename', and 'status' ('ingestion_started').
            Unlike ingest_url, no 'id' field is returned - the file ID is assigned
            later when the storage webhook triggers processing. Use
            check_ingestion_status(bucket=bucket, filename=filename) to poll for
            the ID and processing status.
        """
        try:
            try:
                file_bytes = base64.b64decode(content_base64)
            except Exception as exc:
                raise ValueError(f"content_base64 is not valid base64: {exc}") from exc

            if len(file_bytes) == 0:
                raise ValueError("content_base64 decodes to empty file (0 bytes)")

            logger.info(f"Received ingest_file request with bucket: {bucket}, filename: {filename}, content_type: {content_type}, content_size_bytes: {len(file_bytes)}")
            token = await get_access_token(KEYCLOAK_TOKEN_ENDPOINT)
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient(timeout=60) as client:
                presign_r = await client.post(
                    f"{EDP_ENDPOINT}/api/presignedUrl",
                    json={"bucket_name": bucket, "object_name": filename, "method": "PUT"},
                    headers=headers,
                )
                presign_r.raise_for_status()
                put_url = presign_r.json()["url"]

            # When using Bearer token auth with presigned URLs, the storage backend
            # (SeaweedFS or MinIO with advanced IAM) validates the Bearer token at request time.
            # Pass the Authorization header to ensure proper RBAC enforcement.
            upload_headers = {"Content-Type": content_type}
            upload_headers.update(headers)  # Include Authorization header if present

            async with httpx.AsyncClient(timeout=120, verify=_S3_SSL_CONTEXT) as s3_client:
                upload_r = await s3_client.put(
                    put_url,
                    content=file_bytes,
                    headers=upload_headers,
                )
                upload_r.raise_for_status()

            return {"bucket": bucket, "filename": filename, "status": "ingestion_started"}
        except ValueError as exc:
            logger.error(f"ingest_file validation error: {exc}")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.error(f"ingest_file auth error: {exc}")
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(f"ingest_file HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            logger.error(f"ingest_file request error: {exc}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}") from exc
        except Exception as exc:
            logger.error(f"ingest_file unexpected error: {exc}")
            raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    @mcp.tool()
    async def list_buckets() -> list[str]:
        """List all available buckets (collections) in the knowledge base.

        Call this tool before ingesting files to discover which buckets exist.
        The default deployment creates a bucket named 'default'. Additional
        buckets can be created via the UI.

        Returns:
            List of bucket name strings.
        """
        try:
            logger.info("Received list_buckets request")
            token = await get_access_token(KEYCLOAK_TOKEN_ENDPOINT)
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{EDP_ENDPOINT}/api/list_buckets",
                    headers=headers,
                )
            r.raise_for_status()
            return r.json().get("buckets", [])
        except RuntimeError as exc:
            logger.error(f"list_buckets auth error: {exc}")
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(f"list_buckets HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            logger.error(f"list_buckets request error: {exc}")
            raise HTTPException(status_code=503, detail=f"EDP service unavailable: {exc}") from exc
        except Exception as exc:
            logger.error(f"list_buckets unexpected error: {exc}")
            raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    @mcp.tool()
    async def check_ingestion_status(
        bucket: str | None = None,
        id: str | None = None,
        filename: str | None = None,
        url: str | None = None,
    ) -> list[dict]:
        """Check ingestion status of files and URLs in the knowledge base.

        Query file or link processing status by bucket/filename or url. To reduce overhead,
        the tool only fetches files if bucket/filename/id provided, and only fetches links
        if url/id provided. If all parameters are None, fetches both files and links.
        Use this to monitor processing progress after calling ingest_url or ingest_file.

        Status values:
          - 'uploaded': item uploaded, queued for processing
          - 'processing': extraction/chunking/embedding in progress
          - 'ingested': ready for retrieval
          - 'error': processing failed (check job_message for details)
          - 'deleting': deletion in progress
          - 'canceled': processing canceled by user

        Args:
            bucket: Filter files by bucket name. If all parameters are None, returns
                    all files and links.
            id: Filter files and URLs by their unique ID. If provided, fetches both
                files and links.
            filename: Filter files by object name. When provided without bucket, matches
                      filename across all buckets.
            url: Filter links by URL.

        Returns:
            List of status dicts. File entries contain:
              - id: UUID
              - bucket_name: storage bucket
              - object_name: file path/key
              - status: current processing state
              - chunks_total: total chunks to process
              - chunks_processed: chunks processed so far
              - job_message: error/status message if any
              - created_at: upload timestamp
              - size: file size in bytes
            Link entries contain:
              - id: UUID
              - uri: the URL being processed
              - status, chunks_total, chunks_processed, job_message, created_at (same as files)
        """
        try:
            logger.info(f"Received check_ingestion_status request with bucket: {bucket}, filename: {filename}, url: {url}")
            token = await get_access_token(KEYCLOAK_TOKEN_ENDPOINT)
            headers = {"Authorization": f"Bearer {token}"}

            # Determine which endpoints to query
            all_none = bucket is None and filename is None and url is None and id is None
            need_files = all_none or bucket is not None or filename is not None or id is not None
            need_links = all_none or url is not None or id is not None
            logger.info(f"check_ingestion_status will fetch {'files' if need_files else ''}{' and ' if need_files and need_links else ''}{'links' if need_links else ''} based on provided filters")

            files = []
            links = []

            # When querying a specific file by bucket+filename immediately after upload,
            # retry briefly to account for S3 webhook propagation delay (typically 50-200ms).
            # Only retry when filtering by specific file (not broad queries).
            retry_on_empty = bool(filename and bucket and not all_none)
            max_retries = 3 if retry_on_empty else 1
            retry_delay = 0.1  # 100ms between retries

            for attempt in range(max_retries):
                async with httpx.AsyncClient(timeout=30) as client:
                    tasks = []
                    if need_files:
                        tasks.append(client.get(f"{EDP_ENDPOINT}/api/files", headers=headers))
                    else:
                        tasks.append(None)
                    if need_links:
                        tasks.append(client.get(f"{EDP_ENDPOINT}/api/links", headers=headers))
                    else:
                        tasks.append(None)

                    results = await asyncio.gather(*[t for t in tasks if t is not None])

                    result_idx = 0
                    if need_files:
                        files_r = results[result_idx]
                        files_r.raise_for_status()
                        files = files_r.json()
                        result_idx += 1
                    if need_links:
                        links_r = results[result_idx]
                        links_r.raise_for_status()
                        links = links_r.json()

                # Filter files by bucket and/or filename if provided
                filtered_files = files
                if bucket:
                    filtered_files = [f for f in filtered_files if f.get("bucket_name") == bucket]
                if filename:
                    filtered_files = [f for f in filtered_files if f.get("object_name") == filename]

                # If we got results or this is the last attempt, break
                if filtered_files or attempt == max_retries - 1:
                    files = filtered_files
                    break

                # Retry: file just uploaded, webhook may not have fired yet
                logger.debug(f"check_ingestion_status: file not found (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s")
                await asyncio.sleep(retry_delay)

            # Check for ID uniqueness between files and links
            if files and links:
                file_ids = {file.get("id") for file in files}
                link_ids = {link.get("id") for link in links}
                id_overlap = file_ids & link_ids
                if id_overlap:
                    logger.warning(f"ID collision detected between files and links: {sorted(id_overlap)}")

            # Filter by ID if provided
            if id:
                files = [f for f in files if f.get("id") == id]
                links = [link for link in links if link.get("id") == id]

            logger.info(files)

            # Filter links by url if provided
            if url:
                links = [link for link in links if link.get("uri") == url]

            # Combine results
            return files + links
        except RuntimeError as exc:
            logger.error(f"check_ingestion_status auth error: {exc}")
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(f"check_ingestion_status HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            logger.error(f"check_ingestion_status request error: {exc}")
            raise HTTPException(status_code=503, detail=f"EDP service unavailable: {exc}") from exc
        except Exception as exc:
            logger.error(f"check_ingestion_status unexpected error: {exc}")
            raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

else:
    logger.warning("EDP_ENDPOINT not set - list_buckets, ingest_url, ingest_file, and check_ingestion_status not registered")


async def health(_: StarletteRequest) -> JSONResponse:
    return JSONResponse({"status": "ok"})


_starlette_app = Starlette(
    routes=[
        Route("/api/v1/mcp/health", health),
        Mount("/api/v1/mcp", app=mcp.sse_app()),
    ]
)
app = CallerCredentialsMiddleware(
    _starlette_app,
    keycloak_token_endpoint=KEYCLOAK_TOKEN_ENDPOINT,
    max_concurrent_sessions=MAX_CONCURRENT_SESSIONS,
    max_sessions_per_client=MAX_SESSIONS_PER_CLIENT,
)

if __name__ == "__main__":
    if not KEYCLOAK_TOKEN_ENDPOINT:
        raise RuntimeError("KEYCLOAK_TOKEN_ENDPOINT is not set - cannot authenticate agents to backend services")

    async def _run_with_cleanup():
        cleanup_task = asyncio.create_task(cleanup_inactive_sessions(SESSION_INACTIVITY_TIMEOUT))
        config = uvicorn.Config(
            app,
            host=os.getenv("MCP_SERVER_HOST", "0.0.0.0"),
            port=MCP_SERVER_PORT,
            root_path="",
        )
        server = uvicorn.Server(config)
        try:
            await server.serve()
        finally:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

    asyncio.run(_run_with_cleanup())
