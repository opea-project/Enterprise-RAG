# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch, Mock, AsyncMock

import pytest
from bson import ObjectId

from comps.cores.proto.docarray import ChatMessage, ChatHistoryName
from comps.chat_history.utils.opea_chat_history import OPEAChatHistoryConnector
from comps.chat_history.utils.documents import ChatHistoryDocument

@pytest.fixture
def test_class():
    return OPEAChatHistoryConnector(mongodb_host="localhost", mongodb_port=27017)

@pytest.fixture
def mock_chat_history():
    return [
        ChatMessage(question="What is AI?", answer="AI is artificial intelligence."),
        ChatMessage(question="How does ML work?", answer="ML uses algorithms to learn patterns.")
    ]

@pytest.fixture
def mock_chat_history_document():
    doc = Mock(spec=ChatHistoryDocument)
    doc.id = ObjectId("507f1f77bcf86cd799439011")
    doc.history = [
        ChatMessage(question="What is AI?", answer="AI is artificial intelligence."),
        ChatMessage(question="How does ML work?", answer="ML uses algorithms to learn patterns.")
    ]
    doc.user_id = "test-user-123"
    doc.history_name = "Test Chat Session"
    doc.save = AsyncMock()
    return doc

@pytest.fixture
def mock_chat_message_name():
    return ChatHistoryName(id="507f1f77bcf86cd799439011", history_name="Test Chat Session")


def test_opea_chat_history_connector_initialization_succeeds():
    connector = OPEAChatHistoryConnector(mongodb_host="localhost", mongodb_port=27017)
    assert isinstance(connector, OPEAChatHistoryConnector), "Instance was not created successfully."


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.ChatHistoryDocument')
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.insert')
async def test_create_new_history_succeeds(mock_insert, mock_document_class, test_class, mock_chat_history):
    mock_insert.return_value = ObjectId("507f1f77bcf86cd799439011")

    mock_document_instance = Mock()
    mock_document_instance.history = mock_chat_history
    mock_document_instance.user_id = "test-user-123"
    mock_document_instance.history_name = " Chat randomname"
    mock_document_class.return_value = mock_document_instance

    result = await test_class.create_new_history(mock_chat_history, "test-user-123")

    assert result is not None, "Result should not be None"
    assert isinstance(result, ChatHistoryName), "Result should be ChatHistoryName instance"
    assert result.id == "507f1f77bcf86cd799439011", "ID should match mock ObjectId"
    assert "Chat" in result.history_name, "History name should contain 'Chat'"
    mock_insert.assert_called_once_with(mock_document_instance)
    mock_document_class.assert_called_once()


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.ChatHistoryDocument')
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.insert')
async def test_create_new_history_raises_exception_on_insert_failure(mock_insert, mock_document_class, test_class, mock_chat_history):
    """Test that create_new_history raises exception when insert fails."""
    mock_insert.side_effect = Exception("Database error")
    mock_document_class.return_value = Mock()

    with pytest.raises(Exception, match="Error inserting history: What is AI\\? for user_id: test-user-123: Database error"):
        await test_class.create_new_history(mock_chat_history, "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_append_history_succeeds(mock_get_by_id, test_class, mock_chat_history, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    new_chat = [ChatMessage(question="What is DL?", answer="DL is deep learning.")]
    result = await test_class.append_history("507f1f77bcf86cd799439011", new_chat, "test-user-123")

    assert result is not None, "Result should not be None"
    assert isinstance(result, ChatHistoryName), "Result should be ChatHistoryName instance"
    assert result.id == "507f1f77bcf86cd799439011", "ID should match"
    mock_chat_history_document.save.assert_called_once()


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_append_history_raises_exception_when_history_not_found(mock_get_by_id, test_class):
    mock_get_by_id.return_value = None

    new_chat = [ChatMessage(question="What is DL?", answer="DL is deep learning.")]

    with pytest.raises(ValueError, match="Error updating history with id: 507f1f77bcf86cd799439011: Chat history with id 507f1f77bcf86cd799439011 not found."):
        await test_class.append_history("507f1f77bcf86cd799439011", new_chat, "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_append_history_raises_exception_when_user_id_mismatch(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    new_chat = [ChatMessage(question="What is DL?", answer="DL is deep learning.")]

    with pytest.raises(ValueError, match="Error updating history with id: 507f1f77bcf86cd799439011: User ID different-user does not match the history's user ID test-user-123."):
        await test_class.append_history("507f1f77bcf86cd799439011", new_chat, "different-user")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_append_history_raises_exception_on_save_failure(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document
    mock_chat_history_document.save = AsyncMock(side_effect=Exception("Save failed"))

    new_chat = [ChatMessage(question="What is DL?", answer="DL is deep learning.")]

    with pytest.raises(Exception, match="Error updating history with id: 507f1f77bcf86cd799439011: Save failed"):
        await test_class.append_history("507f1f77bcf86cd799439011", new_chat, "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_change_history_name_succeeds(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    await test_class.change_history_name("507f1f77bcf86cd799439011", "New Chat Name", "test-user-123")

    assert mock_chat_history_document.history_name == "New Chat Name", "History name should be updated"
    mock_chat_history_document.save.assert_called_once()


@pytest.mark.parametrize("history_name, expected_message", [
    (None, "Error changing history name with id: 507f1f77bcf86cd799439011: History name cannot be empty."),
    ("", "Error changing history name with id: 507f1f77bcf86cd799439011: History name cannot be empty."),
    ("   ", "Error changing history name with id: 507f1f77bcf86cd799439011: History name cannot be empty."),
])
@pytest.mark.asyncio
async def test_change_history_name_raises_exception_when_name_is_empty(test_class, history_name, expected_message):
    """Test that change_history_name raises exception when name is empty."""
    with pytest.raises(ValueError, match=expected_message):
        await test_class.change_history_name("507f1f77bcf86cd799439011", history_name, "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_change_history_name_raises_exception_when_history_not_found(mock_get_by_id, test_class):
    mock_get_by_id.return_value = None

    with pytest.raises(ValueError, match="Error changing history name with id: 507f1f77bcf86cd799439011: Chat history with id 507f1f77bcf86cd799439011 not found."):
        await test_class.change_history_name("507f1f77bcf86cd799439011", "New Name", "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_change_history_name_raises_exception_when_user_id_mismatch(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    with pytest.raises(ValueError, match="Error changing history name with id: 507f1f77bcf86cd799439011: User ID different-user does not match the history's user ID test-user-123."):
        await test_class.change_history_name("507f1f77bcf86cd799439011", "New Name", "different-user")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.delete')
async def test_delete_history_succeeds(mock_delete, mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document
    mock_delete.return_value = None

    await test_class.delete_history("507f1f77bcf86cd799439011", "test-user-123")

    mock_delete.assert_called_once_with(ChatHistoryDocument, "507f1f77bcf86cd799439011")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_delete_history_raises_exception_when_history_not_found(mock_get_by_id, test_class):
    mock_get_by_id.return_value = None

    with pytest.raises(Exception, match="Error deleting history with id: 507f1f77bcf86cd799439011: Chat history with id 507f1f77bcf86cd799439011 not found."):
        await test_class.delete_history("507f1f77bcf86cd799439011", "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_delete_history_raises_exception_when_user_id_mismatch(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    with pytest.raises(Exception, match="Error deleting history with id: 507f1f77bcf86cd799439011: User ID different-user does not match the history's user ID test-user-123."):
        await test_class.delete_history("507f1f77bcf86cd799439011", "different-user")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.ChatHistoryDocument')
async def test_get_all_histories_for_user_succeeds(mock_chat_history_document, test_class):
    """Test successful retrieval of all histories for a user."""
    mock_histories = [
        Mock(id=ObjectId("507f1f77bcf86cd799439011"), history_name="Chat 1"),
        Mock(id=ObjectId("507f1f77bcf86cd799439012"), history_name="Chat 2")
    ]

    # Mock the chained method calls: ChatHistoryDocument.find().to_list()
    mock_find_result = Mock()
    mock_find_result.to_list = AsyncMock(return_value=mock_histories)
    mock_chat_history_document.find.return_value = mock_find_result

    result = await test_class.get_all_histories_for_user("test-user-123")

    assert result is not None, "Result should not be None"
    assert len(result) == 2, "Should return 2 histories"
    assert all(isinstance(item, ChatHistoryName) for item in result), "All items should be ChatHistoryName instances"
    assert result[0].id == "507f1f77bcf86cd799439011", "First item ID should match"
    assert result[0].history_name == "Chat 1", "First item name should match"

    mock_chat_history_document.find.assert_called_once()
    mock_find_result.to_list.assert_called_once()


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.ChatHistoryDocument')
async def test_get_all_histories_for_user_raises_exception_on_find_failure(mock_find, test_class):
    mock_find.find.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Error retrieving histories for user: test-user-123: Database error"):
        await test_class.get_all_histories_for_user("test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_get_history_by_id_succeeds(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    result = await test_class.get_history_by_id("507f1f77bcf86cd799439011", "test-user-123")

    assert result is not None, "Result should not be None"
    assert result.user_id == "test-user-123", "User ID should match"


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_get_history_by_id_raises_exception_when_history_not_found(mock_get_by_id, test_class):
    mock_get_by_id.return_value = None

    with pytest.raises(ValueError, match="Error retrieving history for user: test-user-123 with id: 507f1f77bcf86cd799439011: Chat history with id 507f1f77bcf86cd799439011 not found."):
        await test_class.get_history_by_id("507f1f77bcf86cd799439011", "test-user-123")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_get_history_by_id_raises_exception_when_user_id_mismatch(mock_get_by_id, test_class, mock_chat_history_document):
    mock_get_by_id.return_value = mock_chat_history_document

    with pytest.raises(ValueError, match="Error retrieving history for user: different-user with id: 507f1f77bcf86cd799439011: User ID different-user does not match the history's user ID test-user-123."):
        await test_class.get_history_by_id("507f1f77bcf86cd799439011", "different-user")


@pytest.mark.asyncio
@patch('comps.chat_history.utils.opea_chat_history.OPEAChatHistoryConnector.get_by_id')
async def test_get_history_by_id_raises_exception_on_get_failure(mock_get_by_id, test_class):
    mock_get_by_id.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Error retrieving history for user: test-user-123 with id: 507f1f77bcf86cd799439011: Database error"):
        await test_class.get_history_by_id("507f1f77bcf86cd799439011", "test-user-123")
