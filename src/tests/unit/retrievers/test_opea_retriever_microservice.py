# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, patch
from comps.cores.proto.docarray import EmbedDoc, EmbedDocList, SearchedDoc, TextDoc
from comps.retrievers.utils.opea_retriever import OPEARetriever
import pytest
from fastapi.exceptions import HTTPException
from comps.cores.utils.utils import sanitize_env
import os


def test_decorator(*args, **kwargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_normal_retriever_rbac_enabled():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "false", "VECTOR_DB_RBAC": "true"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            OPEARetriever._instance = None  # Reset the singleton instance for testing
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=str(os.getenv('VECTOR_DB_RBAC')).lower() in ['true', '1', 't', 'y', 'yes']
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.retrieve', side_effect=[SearchedDoc(retrieved_docs=[
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1,
                        "file_id": "456",
                        "vector_distance": 0.9
                    })], user_prompt="")]):
                    with patch('comps.retrievers.opea_retriever_microservice.retriever.generate_rbac') as mock_generate_rbac:
                        from comps.retrievers.opea_retriever_microservice import process, retriever

                        embeddoc = EmbedDoc(
                            text="Test document",
                            embedding=[0.1, 0.2, 0.3]
                        )

                        embeddocs = EmbedDocList(docs=[embeddoc, embeddoc])

                        # Call the undecorated process function
                        # Call the process function
                        mock_request = AsyncMock()
                        mock_request.headers = {"Authorization": "abcd"}
                        result = await process(input=embeddocs, request=mock_request)

                        # Assert that generate_rbac was called
                        assert retriever.rbac_enabled is True
                        mock_generate_rbac.assert_called_once()

                        # Assert that the result is of the expected type
                        assert isinstance(result, SearchedDoc)
                        assert len(result.retrieved_docs) == 1

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_normal_retriever_rbac_disabled():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "false", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            OPEARetriever._instance = None  # Reset the singleton instance for testing
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=str(os.getenv('VECTOR_DB_RBAC')).lower() in ['true', '1', 't', 'y', 'yes']
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.retrieve', side_effect=[SearchedDoc(retrieved_docs=[
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1,
                        "file_id": "456",
                        "vector_distance": 0.9
                    })], user_prompt="")]):
                    with patch('comps.retrievers.opea_retriever_microservice.retriever.generate_rbac') as mock_generate_rbac:
                        from comps.retrievers.opea_retriever_microservice import process, retriever

                        embeddoc = EmbedDoc(
                            text="Test document",
                            embedding=[0.1, 0.2, 0.3]
                        )

                        embeddocs = EmbedDocList(docs=[embeddoc, embeddoc])

                        # Call the undecorated process function
                        # Call the process function
                        mock_request = AsyncMock()
                        mock_request.headers = {"Authorization": "abcd"}
                        result = await process(input=embeddocs, request=mock_request)

                        # Assert that generate_rbac was called
                        assert retriever.rbac_enabled is False
                        mock_generate_rbac.assert_not_called()

                        # Assert that the result is of the expected type
                        assert isinstance(result, SearchedDoc)
                        assert len(result.retrieved_docs) == 1

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_normal_retriever_multiple_embeddocs():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "false", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=False
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.retrieve', side_effect=[SearchedDoc(retrieved_docs=[
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1,
                        "file_id": "456",
                        "vector_distance": 0.9
                    }),
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1,
                        "link_id": "https://example.com/link",
                        "vector_distance": 0.9
                    })
                ], user_prompt="")]):
                    from comps.retrievers.opea_retriever_microservice import process

                    embeddoc = EmbedDoc(
                        text="Test document",
                        embedding=[0.1, 0.2, 0.3]
                    )

                    embeddocs = EmbedDocList(docs=[embeddoc, embeddoc])

                    # Call the undecorated process function
                    result = await process(input=embeddocs, request=AsyncMock())

                    # Assert that the result is of the expected type
                    assert isinstance(result, SearchedDoc)
                    assert len(result.retrieved_docs) == 2

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_normal_retriever():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "false", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=False
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.retrieve', side_effect=[SearchedDoc(retrieved_docs=[
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1,
                        "file_id": "456",
                        "vector_distance": 0.9
                    }),
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1,
                        "link_id": "https://example.com/link",
                        "vector_distance": 0.9
                    })
                ], user_prompt="")]):
                    from comps.retrievers.opea_retriever_microservice import process

                    embeddoc = EmbedDoc(
                        text="Test document",
                        embedding=[0.1, 0.2, 0.3]
                    )

                    # Call the undecorated process function
                    result = await process(input=embeddoc, request=AsyncMock())

                    # Assert that the result is of the expected type
                    assert isinstance(result, SearchedDoc)
                    assert len(result.retrieved_docs) == 2

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_hierarchical_retriever():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "true", "K_SUMMARIES": "1", "K_CHUNKS": "1", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=False
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.hierarchical_retrieve', side_effect=[SearchedDoc(retrieved_docs=[
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1
                    })
                ], user_prompt=""),
                SearchedDoc(retrieved_docs=[
                    TextDoc(text="aaa", metadata={
                        "doc_id": "123",
                        "page": 1
                    })
                ], user_prompt="")]):
                    from comps.retrievers.opea_retriever_microservice import process

                    embeddoc = EmbedDoc(
                        text="Test document",
                        embedding=[0.1, 0.2, 0.3]
                    )

                    # Call the undecorated process function
                    result = await process(input=embeddoc, request=AsyncMock())

                    # Assert that the result is of the expected type
                    assert isinstance(result, SearchedDoc)
                    assert len(result.retrieved_docs) == 1

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_hierarchical_retriever_wrong_input():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "true", "K_SUMMARIES": "1", "K_CHUNKS": "1", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=False
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.hierarchical_retrieve', side_effect=ValueError("Invalid input")):
                    from comps.retrievers.opea_retriever_microservice import process

                    embeddoc = EmbedDoc(
                        text="Test document",
                        embedding=[0.1, 0.2, 0.3]
                    )

                    # Call the undecorated process function
                    with pytest.raises(HTTPException) as excinfo:
                        await process(input=embeddoc, request=AsyncMock())
                    assert "A ValueError occured while validating the input in retriever" in str(excinfo.value)

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_hierarchical_retriever_not_implemented():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "true", "K_SUMMARIES": "1", "K_CHUNKS": "1", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=False
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.hierarchical_retrieve', side_effect=NotImplementedError):
                    from comps.retrievers.opea_retriever_microservice import process

                    embeddoc = EmbedDoc(
                        text="Test document",
                        embedding=[0.1, 0.2, 0.3]
                    )

                    # Call the undecorated process function
                    with pytest.raises(HTTPException) as excinfo:
                        await process(input=embeddoc, request=AsyncMock())
                    assert "A NotImplementedError occured in retriever" in str(excinfo.value)

@pytest.mark.asyncio
@patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator)
async def test_call_process_hierarchical_retriever_generic_exception():
    with patch.dict("os.environ", {"VECTOR_STORE": "redis", "USE_HIERARCHICAL_INDICES": "true", "K_SUMMARIES": "1", "K_CHUNKS": "1", "VECTOR_DB_RBAC": "false"}):
        with patch('comps.cores.mega.micro_service.register_microservice', new=test_decorator):
            with patch('comps.retrievers.opea_retriever_microservice.retriever', new=OPEARetriever(
                vector_store=sanitize_env(os.getenv("VECTOR_STORE")),
                rbac_enabled=False
            )):
                with patch('comps.retrievers.opea_retriever_microservice.retriever.hierarchical_retrieve', side_effect=Exception):
                    from comps.retrievers.opea_retriever_microservice import process

                    embeddoc = EmbedDoc(
                        text="Test document",
                        embedding=[0.1, 0.2, 0.3]
                    )

                    # Call the undecorated process function
                    with pytest.raises(HTTPException) as excinfo:
                        await process(input=embeddoc, request=AsyncMock())
                    assert "An Error while retrieving documents" in str(excinfo.value)
