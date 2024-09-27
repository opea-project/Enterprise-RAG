# ruff: noqa: E711, E712
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# test_opea_prompt_registry.py

import pytest
from unittest.mock import AsyncMock, patch
from comps.prompt_registry.utils.opea_prompt_registry import OPEAPromptRegistryConnector
from comps.prompt_registry.utils.documents import PromptDocument

@pytest.fixture
def mock_mongo_connector():
    with patch("comps.cores.utils.mongodb.motor.AsyncIOMotorClient", return_value=None) as mock:
        yield mock

@pytest.fixture
def mock_prompt_document():
    with patch("comps.prompt_registry.utils.opea_prompt_registry.PromptDocument") as mock:
        yield mock

@pytest.fixture
def prompt_document_mock_factory():
    def create_mock():
        return AsyncMock()
    return create_mock

@pytest.fixture
def connector(mock_mongo_connector):
    mongodb_host = "localhost"
    mongodb_port = 27017

    connector = OPEAPromptRegistryConnector(mongodb_host, mongodb_port)
    return connector

def test_initialize_connector(mock_mongo_connector):
    mongodb_host = "localhost"
    mongodb_port = 27017

    connector = OPEAPromptRegistryConnector(mongodb_host, mongodb_port)

    assert connector.host == mongodb_host
    assert connector.port == mongodb_port
    assert connector.documents == [PromptDocument]
    assert connector.db_name == "OPEA"

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.insert", return_value="mock_id")
async def test_insert_prompt(mock_insert, connector, mock_prompt_document):
    prompt_text = "Test prompt"
    filename = "test_file.txt"

    mock_document = mock_prompt_document.return_value
    mock_document.prompt_text = prompt_text
    mock_document.filename = filename

    result = await connector.insert_prompt(prompt_text, filename)

    mock_prompt_document.assert_called_once_with(prompt_text=prompt_text, filename=filename)
    mock_insert.assert_called_once_with(mock_document)
    assert result == "mock_id"

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.insert", side_effect=ValueError("Document not found in the list of documents."))
async def test_insert_prompt_error_handling(mock_insert, connector, mock_prompt_document):
    prompt_text = "Test prompt"
    filename = "test_file.txt"

    mock_document = mock_prompt_document.return_value
    mock_document.prompt_text = prompt_text
    mock_document.filename = filename

    with pytest.raises(Exception) as exc_info:
        await connector.insert_prompt(prompt_text, filename)
        assert "Error inserting prompt" in str(exc_info.value)

    mock_prompt_document.assert_called_once_with(prompt_text=prompt_text, filename=filename)
    mock_insert.assert_called_once_with(mock_document)

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.delete", return_value=None)
async def test_delete_prompt(mock_delete, connector):
    prompt_id = "mock_id"

    await connector.delete_prompt(prompt_id)
    mock_delete.assert_called_once_with(PromptDocument, prompt_id)

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.delete", side_effect=ValueError("Document not found in the list of documents."))
async def test_delete_prompt_error_handling(mock_delete, connector):
    prompt_id = "mock_id"

    with pytest.raises(Exception) as exc_info:
        await connector.delete_prompt(prompt_id)
        assert "Error deleting prompt with id" in str(exc_info.value)

    mock_delete.assert_called_once_with(PromptDocument, prompt_id)

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.get_all", return_value=["mock_prompt1", "mock_prompt2"])
async def test_get_all_prompts(mock_get_all, connector):
    result = await connector.get_all_prompts()

    mock_get_all.assert_called_once_with(PromptDocument)
    assert result == ["mock_prompt1", "mock_prompt2"]

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.get_all", side_effect=ValueError("Document not found in the list of documents."))
async def test_get_all_prompts_error_handling(mock_get_all, connector):
    with pytest.raises(Exception) as exc_info:
        await connector.get_all_prompts()
        assert "Error retrieving prompts" in str(exc_info.value)

    mock_get_all.assert_called_once_with(PromptDocument)

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.get_by_id", return_value="mock_prompt1")
async def test_get_prompt_by_id(mock_get_by_id, connector):
    prompt_id = "mock_id"
    result = await connector.get_prompt_by_id(prompt_id)

    mock_get_by_id.assert_called_once_with(PromptDocument, prompt_id)
    assert result == "mock_prompt1"

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.get_by_id", side_effect=ValueError("Document not found in the list of documents."))
async def test_get_prompt_by_id_error_handling(mock_get_by_id, connector):
    prompt_id = "mock_id"
    with pytest.raises(Exception) as exc_info:
        await connector.get_prompt_by_id(prompt_id)
        assert "Error retrieving prompts" in str(exc_info.value)

    mock_get_by_id.assert_called_once_with(PromptDocument, prompt_id)

@pytest.mark.asyncio
async def test_get_prompts_by_filename(connector, prompt_document_mock_factory, mock_prompt_document):
    filename = "filename"

    mock_document = prompt_document_mock_factory()
    mock_document.prompt_text = "prompt_text"
    mock_document.filename = "filename"
    mock_document2 = prompt_document_mock_factory()
    mock_document2.prompt_text = "prompt_text"
    mock_document2.filename = "filename2"

    with patch("comps.prompt_registry.utils.opea_prompt_registry.PromptDocument.find") as mock_find:
        mock_to_list = AsyncMock(return_value=[mock_document])
        mock_find.return_value.to_list = mock_to_list

        result = await connector.get_prompts_by_filename(filename)
        mock_find.assert_called_once()

    assert result == [mock_document]

@pytest.mark.asyncio
@patch("comps.prompt_registry.utils.opea_prompt_registry.PromptDocument.find", side_effect=Exception("exception"))
async def test_get_prompts_by_filename_error_handling(mock_find, connector):
    prompt_id = "mock_id"
    with pytest.raises(Exception) as exc_info:
        await connector.get_prompts_by_filename(prompt_id)
        assert "Error retrieving prompts for filename" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_prompts_by_text(connector, prompt_document_mock_factory):
    text = "mock_text"

    mock_document = prompt_document_mock_factory()
    mock_document.prompt_text = "prompt_text"
    mock_document.filename = "filename"
    mock_document2 = prompt_document_mock_factory()
    mock_document2.prompt_text = "mock_text hello"
    mock_document2.filename = "filename"

    with patch("comps.cores.utils.mongodb.OPEAMongoConnector.get_all", return_value=[mock_document, mock_document2]) as mock_get_all:
        result = await connector.get_prompts_by_text(text)

        mock_get_all.assert_called_once_with(PromptDocument)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == mock_document2
    assert result[0].prompt_text == "mock_text hello"
    assert result[0].filename == "filename"

@pytest.mark.asyncio
@patch("comps.cores.utils.mongodb.OPEAMongoConnector.get_all", side_effect=ValueError("Document not found in the list of documents."))
async def test_get_prompts_by_text_error_handling(mock_get_all, connector):
    text = "mock_text"
    with pytest.raises(Exception) as exc_info:
        await connector.get_prompts_by_text(text)
        assert "Error retrieving prompts for text" in str(exc_info.value)

    mock_get_all.assert_called_once_with(PromptDocument)

@pytest.mark.asyncio
async def test_get_prompts_by_filename_and_text(connector, prompt_document_mock_factory, mock_prompt_document):
    filename = "filename"
    text = "mock_text"

    mock_document = prompt_document_mock_factory()
    mock_document.prompt_text = "prompt_text"
    mock_document.filename = "filename"
    mock_document2 = prompt_document_mock_factory()
    mock_document2.prompt_text = "prompt_text"
    mock_document2.filename = "filename2"

    with patch("comps.prompt_registry.utils.opea_prompt_registry.PromptDocument.find") as mock_find:
        mock_to_list = AsyncMock(return_value=[mock_document])
        mock_find.return_value.to_list = mock_to_list
        result = await connector.get_prompts_by_filename_and_text(filename, text)

        mock_find.assert_called_once()

    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.asyncio
@patch("comps.prompt_registry.utils.opea_prompt_registry.PromptDocument.find", side_effect=Exception("exception"))
async def test_get_prompts_by_filename_and_text_error_handling(mock_find, connector):
    filename = "filename"
    text = "mock_text"
    with pytest.raises(Exception) as exc_info:
        await connector.get_prompts_by_filename_and_text(filename, text)
        assert "Error retrieving prompts for text" in str(exc_info.value)
