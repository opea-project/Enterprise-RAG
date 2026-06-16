#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import logging
import os

import allure
import pytest

from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

if not cfg.get("mcp", {}).get("enabled"):
    pytestmark = pytest.mark.skip(reason="MCP gateway is not deployed")

logger = logging.getLogger(__name__)

MCP_TEST_FILE = "test_mcp.txt"
MCP_TEST_FILE_PATH = os.path.join(DATAPREP_UPLOAD_DIR, MCP_TEST_FILE)


def extract_chunks(result):
    """Extract document chunks from retrieve_context response.

    MCP gateway returns different structures depending on whether reranker is used:
      - reranker=False: {"retrieved_docs": [...], ...}
      - reranker=True: {"data": {"reranked_docs": [...]}, ...}

    This helper normalizes both formats to a list of chunk dicts.
    """
    if not isinstance(result, dict):
        return result if isinstance(result, list) else []
    # Reranker path
    if "data" in result and isinstance(result["data"], dict):
        return result["data"].get("reranked_docs", [])
    # Non-reranker path
    return result.get("retrieved_docs", [])


@pytest.fixture(scope="module")
def ingested_document(mcp_helper, edp_helper):
    """Upload a test document via MCP and wait for ingestion to complete.

    Used by retrieve_context tests to guarantee there is searchable content
    in the knowledge base. Runs once per module (shared across all tests in
    this file that request it).

    Uses edp_helper.wait_for_file_upload() for robust status polling (handles
    error states, proper timeouts, status flow comparison).

    Fails if ingest_file is unavailable or ingestion does not complete — tests
    depending on this fixture will show as errors in the report.
    """
    with open(MCP_TEST_FILE_PATH, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    success, result = mcp_helper.call_tool("ingest_file", {
        "bucket": "default",
        "filename": MCP_TEST_FILE,
        "content_base64": content_b64,
        "content_type": "text/plain",
    })
    assert success, f"ingest_file failed: {str(result)[:200]}"

    edp_helper.wait_for_file_upload(MCP_TEST_FILE, "ingested", timeout=120)
    return MCP_TEST_FILE


@allure.testcase("IEASG-T628")
def test_mcp_health(mcp_helper):
    """Verify that the MCP gateway health endpoint responds."""
    status_code = mcp_helper.check_health()
    assert status_code == 200, f"MCP gateway health check returned {status_code}"


@allure.testcase("IEASG-T629")
def test_mcp_list_tools(mcp_helper):
    """Verify that the MCP gateway exposes all expected tools via SSE connection."""
    tool_names = mcp_helper.list_tools()
    logger.info(f"MCP tools discovered: {tool_names}")
    expected_tools = ["retrieve_context", "list_buckets", "ingest_file", "ingest_url", "check_ingestion_status"]
    for tool in expected_tools:
        assert tool in tool_names, f"{tool} tool not registered"


@allure.testcase("IEASG-T630")
def test_mcp_auth_invalid_credentials(mcp_helper):
    """Verify that invalid credentials are rejected by the MCP gateway.

    Opens a separate SSE connection (not the persistent test session) with
    fake client_id/secret. The gateway should refuse the handshake — either
    by closing the connection or returning an auth error.
    """
    rejected = mcp_helper.connect_with_invalid_credentials()
    assert rejected, "MCP gateway accepted invalid credentials"


@allure.testcase("IEASG-T631")
def test_mcp_list_buckets(mcp_helper):
    """Verify that list_buckets tool returns bucket names from EDP."""
    success, result = mcp_helper.call_tool("list_buckets", {})
    assert success, f"list_buckets failed: {result}"
    logger.info(f"Buckets: {result}")
    assert isinstance(result, list), f"Expected list of buckets, got {type(result)}"
    assert len(result) > 0, "Expected at least one bucket"
    assert "default" in result, "'default' bucket must always exist"


@allure.testcase("IEASG-T632")
def test_mcp_retrieve_context(mcp_helper, ingested_document):
    """Verify that retrieve_context returns relevant chunks from an ingested document."""
    success, result = mcp_helper.call_tool("retrieve_context", {
        "query": "Retrieval-Augmented Generation knowledge base",
        "k": 3,
        "reranker": False,
    })
    assert success, f"retrieve_context failed: {result}"
    chunks = extract_chunks(result)
    assert isinstance(chunks, list) and len(chunks) > 0, "Expected at least one chunk from ingested document"
    first_chunk_text = chunks[0].get("text", "") if isinstance(chunks[0], dict) else str(chunks[0])
    logger.info(f"retrieve_context returned {len(chunks)} chunk(s), first: {first_chunk_text[:150]}")
    assert any(word in first_chunk_text.lower() for word in ["retrieval", "rag", "knowledge"]), \
        f"Chunk content does not match query topic: {first_chunk_text[:200]}"



@allure.testcase("IEASG-T633")
def test_mcp_retrieve_context_top_n_limits_results(mcp_helper, ingested_document):
    """Verify that top_n parameter limits the number of returned chunks.

    Calls retrieve_context twice with top_n=1 and top_n=5 on the same query.
    The first call must return at most 1 chunk, and the second must return
    more (or equal, if only 1 chunk exists) — proving top_n is respected.
    """
    query = "Retrieval-Augmented Generation knowledge base"

    success_1, result_1 = mcp_helper.call_tool("retrieve_context", {
        "query": query, "top_n": 1, "reranker": True,
    })
    assert success_1, f"retrieve_context (top_n=1) failed: {result_1}"
    chunks_1 = extract_chunks(result_1)

    success_5, result_5 = mcp_helper.call_tool("retrieve_context", {
        "query": query, "top_n": 5, "reranker": True,
    })
    assert success_5, f"retrieve_context (top_n=5) failed: {result_5}"
    chunks_5 = extract_chunks(result_5)

    logger.info(f"top_n=1 returned {len(chunks_1)} chunk(s), top_n=5 returned {len(chunks_5)} chunk(s)")
    assert len(chunks_1) <= 1, f"top_n=1 should return at most 1 chunk, got {len(chunks_1)}"
    assert len(chunks_5) >= len(chunks_1), "top_n=5 should return at least as many chunks as top_n=1"


@allure.testcase("IEASG-T634")
def test_mcp_ingest_file(mcp_helper):
    """Verify that ingest_file uploads a document and it appears in ingestion status."""
    tool_names = mcp_helper.list_tools()
    if "ingest_file" not in tool_names:
        pytest.skip("ingest_file tool not registered on this deployment")

    filename = "mcp_e2e_ingest_test.txt"
    with open(MCP_TEST_FILE_PATH, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    success, result = mcp_helper.call_tool("ingest_file", {
        "bucket": "default",
        "filename": filename,
        "content_base64": content_b64,
        "content_type": "text/plain",
    })
    assert success, f"ingest_file failed: {result}"
    logger.info(f"ingest_file result: {result}")

    ok, status_result = mcp_helper.call_tool("check_ingestion_status", {
        "bucket": "default",
        "filename": filename,
    })
    assert ok, f"check_ingestion_status failed after ingest: {status_result}"
    assert isinstance(status_result, list) and len(status_result) > 0, \
        f"Ingested file not found in status: {status_result}"
    file_entry = status_result[0]
    logger.info(f"Ingested file status: {file_entry.get('status')}, chunks: {file_entry.get('chunks_processed')}")


@allure.testcase("IEASG-T635")
def test_mcp_check_ingestion_status(mcp_helper, ingested_document):
    """Verify that check_ingestion_status returns correct file metadata.

    Uses the document uploaded by ingested_document fixture — queries its
    status and verifies the response contains expected fields and the file
    shows as ingested.
    """
    success, result = mcp_helper.call_tool("check_ingestion_status", {
        "bucket": "default",
        "filename": ingested_document,
    })
    assert success, f"check_ingestion_status failed: {result}"
    assert isinstance(result, list) and len(result) > 0, \
        f"Expected file entry in status response, got: {result}"
    file_entry = result[0]
    logger.info(f"Ingestion status entry: {file_entry}")
    assert file_entry.get("status") == "ingested", \
        f"Expected status 'ingested', got '{file_entry.get('status')}'"
    assert file_entry.get("object_name", "").endswith(ingested_document), \
        f"Expected filename '{ingested_document}' in object_name, got '{file_entry.get('object_name')}'"
    assert file_entry.get("chunks_processed", 0) > 0, \
        f"Expected chunks_processed > 0, got {file_entry.get('chunks_processed')}"


@allure.testcase("IEASG-T636")
def test_mcp_ingest_url(mcp_helper):
    """Verify that ingest_url tool queues a URL and returns a link ID."""
    tool_names = mcp_helper.list_tools()
    if "ingest_url" not in tool_names:
        pytest.skip("ingest_url tool not registered on this deployment")

    success, result = mcp_helper.call_tool("ingest_url", {
        "url": "https://www.intel.com/content/www/us/en/newsroom/resources/press-kit.html",
    })
    assert success, f"ingest_url failed: {result}"
    logger.info(f"ingest_url result: {result}")
    assert isinstance(result, dict), f"Expected dict with link ID, got {type(result)}"
    assert "id" in result or "message" in result, \
        f"Response should contain 'id' or 'message' confirming ingestion was queued: {result}"



@allure.testcase("IEASG-T637")
def test_mcp_retrieve_context_with_reranker(mcp_helper, ingested_document):
    """Verify that retrieve_context works with reranker enabled.

    Reranker is a separate model that re-scores retrieved chunks for relevance.
    This tests a different code path than reranker=False (which only does
    vector similarity). Both should return successfully.
    """
    success, result = mcp_helper.call_tool("retrieve_context", {
        "query": "Retrieval-Augmented Generation knowledge base",
        "top_n": 3,
        "reranker": True,
    })
    assert success, f"retrieve_context with reranker failed: {result}"
    chunks = extract_chunks(result)
    logger.info(f"retrieve_context (reranker=True) returned {len(chunks)} chunk(s)")
    assert isinstance(chunks, list), f"Expected list of chunks, got {type(chunks)}"
    assert len(chunks) > 0, "Expected at least one chunk from ingested document"


@allure.testcase("IEASG-T638")
def test_mcp_retrieve_context_empty_query(mcp_helper):
    """Verify that retrieve_context handles an empty query gracefully.

    Either returns an empty chunk list or a meaningful error — but must not
    crash the gateway or return a 500.
    """
    success, result = mcp_helper.call_tool("retrieve_context", {
        "query": "",
        "top_n": 3,
        "reranker": False,
    })
    if success:
        chunks = extract_chunks(result)
        logger.info(f"Empty query returned {len(chunks)} chunk(s)")
        assert isinstance(chunks, list), f"Expected list, got {type(chunks)}"
    else:
        error_text = str(result).lower()
        logger.info(f"Empty query returned error: {error_text[:200]}")
        assert "500" not in error_text, f"Gateway crashed with 500 on empty query: {error_text[:200]}"



@allure.testcase("IEASG-T639")
def test_mcp_ingest_file_invalid_bucket(mcp_helper):
    """Verify that ingest_file with a non-existent bucket returns a clear error."""
    tool_names = mcp_helper.list_tools()
    if "ingest_file" not in tool_names:
        pytest.skip("ingest_file tool not registered on this deployment")

    content_b64 = base64.b64encode(b"test content").decode()
    success, result = mcp_helper.call_tool("ingest_file", {
        "bucket": "nonexistent-bucket-xyz-12345",
        "filename": "test.txt",
        "content_base64": content_b64,
        "content_type": "text/plain",
    })
    assert not success, "ingest_file should fail for non-existent bucket"
    error_text = str(result)
    logger.info(f"Invalid bucket error: {error_text[:200]}")


@allure.testcase("IEASG-T640")
def test_mcp_ingest_file_empty_content(mcp_helper):
    """Verify that ingest_file with empty base64 content returns an error."""
    tool_names = mcp_helper.list_tools()
    if "ingest_file" not in tool_names:
        pytest.skip("ingest_file tool not registered on this deployment")

    success, result = mcp_helper.call_tool("ingest_file", {
        "bucket": "default",
        "filename": "empty_file.txt",
        "content_base64": "",
        "content_type": "text/plain",
    })
    assert not success, "ingest_file should fail for empty content"
    error_text = str(result)
    logger.info(f"Empty content error: {error_text[:200]}")


@allure.testcase("IEASG-T641")
def test_mcp_check_ingestion_status_nonexistent_file(mcp_helper):
    """Verify that check_ingestion_status returns empty list for a file that does not exist."""
    success, result = mcp_helper.call_tool("check_ingestion_status", {
        "bucket": "default",
        "filename": "nonexistent_file_xyz.txt",
    })
    assert success, f"check_ingestion_status failed: {result}"
    if result is None:
        result = []
    logger.info(f"Nonexistent file query returned {len(result)} file(s)")
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert len(result) == 0, "Expected empty list for nonexistent file"



@allure.testcase("IEASG-T642")
def test_mcp_retrieve_context_search_type_siblings(mcp_helper, ingested_document):
    """Verify that retrieve_context with siblings search type returns additional context.

    This search type returns not just the matching chunks but also their neighbors
    (preceding/following chunks from the same document) for better context continuity.
    The response should include a 'sibling_docs' field alongside 'retrieved_docs'.
    """
    success, result = mcp_helper.call_tool("retrieve_context", {
        "query": "Retrieval-Augmented Generation knowledge base",
        "top_n": 3,
        "reranker": False,
        "search_type": "similarity_search_with_siblings",
    })
    assert success, f"retrieve_context with siblings search failed: {result}"
    assert isinstance(result, dict), f"Expected dict with retrieved_docs and sibling_docs, got {type(result)}"
    chunks = extract_chunks(result)
    sibling_docs = result.get("sibling_docs")
    logger.info(f"Siblings search returned {len(chunks)} chunk(s), sibling_docs: {sibling_docs}")
    assert isinstance(chunks, list) and len(chunks) > 0, "Expected at least one chunk from ingested document"
    assert sibling_docs is not None, "Expected sibling_docs field in response for siblings search type"


