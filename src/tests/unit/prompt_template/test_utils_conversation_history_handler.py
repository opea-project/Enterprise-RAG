# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest

from unittest.mock import patch, Mock

from comps import (
    PrevQuestionDetails
)

from comps.prompt_template.utils.chat_history_handler import ChatHistoryHandler

def mock_default_input_data_short_history():
    return [
            PrevQuestionDetails(question="Previous question 1", answer="Previous answer 1"),
            PrevQuestionDetails(question="Previous question 2", answer="Previous answer 2"),
            ]

def mock_default_input_data_long_history():
    return [
            PrevQuestionDetails(question="Previous question 1", answer="Previous answer 1"),
            PrevQuestionDetails(question="Previous question 2", answer="Previous answer 2"),
            PrevQuestionDetails(question="Previous question 3", answer="Previous answer 3"),
            PrevQuestionDetails(question="Previous question 4", answer="Previous answer 4"),
            PrevQuestionDetails(question="Previous question 5", answer="Previous answer 5"),
            PrevQuestionDetails(question="Previous question 6", answer="Previous answer 6"),
            ]

def mock_api_response_short_history():
    return {
        "history": [
            {"question": "Previous question 1", "answer": "Previous answer 1"},
            {"question": "Previous question 2", "answer": "Previous answer 2"},
        ]
    }

def mock_api_response_long_history():
    return {
        "history": [
            {"question": "Previous question 1", "answer": "Previous answer 1"},
            {"question": "Previous question 2", "answer": "Previous answer 2"},
            {"question": "Previous question 3", "answer": "Previous answer 3"},
            {"question": "Previous question 4", "answer": "Previous answer 4"},
            {"question": "Previous question 5", "answer": "Previous answer 5"},
            {"question": "Previous question 6", "answer": "Previous answer 6"},
        ]
    }

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_init_with_valid_endpoint(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "chat_history service is healthy"
    mock_get.return_value = mock_response

    handler = ChatHistoryHandler("http://localhost:8080")
    assert handler.chat_history_endpoint == "http://localhost:8080"
    mock_get.assert_called_once_with("http://localhost:8080/v1/health_check", headers={"Content-Type": "application/json"})

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_init_with_invalid_endpoint(mock_get):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Service unavailable"
    mock_get.return_value = mock_response

    with pytest.raises(ValueError) as error:
        ChatHistoryHandler("http://localhost:8080")

    assert "Chat history service is not available" in str(error.value)

def test_chat_history_handler_init_without_endpoint():
    handler = ChatHistoryHandler()
    assert handler.chat_history_endpoint is None

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_naive_correct_parse_short_input(mock_get):
    health_response = Mock()
    health_response.status_code = 200
    health_response.text = "chat_history service is healthy"

    history_response = Mock()
    history_response.status_code = 200
    history_response.json.return_value = mock_api_response_short_history()

    mock_get.side_effect = [health_response, history_response]

    handler = ChatHistoryHandler("http://localhost:8080")
    parsed_output = handler.parse_chat_history("test_history_id", "naive", "test_token")

    assert parsed_output == "User: Previous question 1\nAssistant: Previous answer 1\nUser: Previous question 2\nAssistant: Previous answer 2"

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_naive_correct_parse_long_input(mock_get):
    health_response = Mock()
    health_response.status_code = 200
    health_response.text = "chat_history service is healthy"

    history_response = Mock()
    history_response.status_code = 200
    history_response.json.return_value = mock_api_response_long_history()

    mock_get.side_effect = [health_response, history_response]

    handler = ChatHistoryHandler("http://localhost:8080")
    parsed_output = handler.parse_chat_history("test_history_id", "naive", "test_token")

    assert parsed_output == "User: Previous question 4\nAssistant: Previous answer 4\nUser: Previous question 5\nAssistant: Previous answer 5\nUser: Previous question 6\nAssistant: Previous answer 6"

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_incorrect_type(mock_get):
    health_response = Mock()
    health_response.status_code = 200
    health_response.text = "chat_history service is healthy"

    history_response = Mock()
    history_response.status_code = 200
    history_response.json.return_value = mock_api_response_long_history()
    mock_get.side_effect = [ health_response, history_response ]

    handler = ChatHistoryHandler("http://localhost:8080")
    with pytest.raises(ValueError) as error:
        handler.parse_chat_history("test_history_id", "wrong_type", "test_token")

        assert "Incorrect ChatHistoryHandler parsing type." in str(error.value)

def test_chat_history_handler_none_history_id():
    handler = ChatHistoryHandler()
    parsed_output = handler.parse_chat_history(None, "naive", "test_token")
    assert parsed_output == ""

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_missing_access_token(mock_get):
    health_response = Mock()
    health_response.status_code = 200
    health_response.text = "chat_history service is healthy"
    mock_get.return_value = health_response

    handler = ChatHistoryHandler("http://localhost:8080")
    parsed_output = handler.parse_chat_history("test_history_id", "naive", "")
    assert parsed_output == ""

@patch('comps.prompt_template.utils.chat_history_handler.requests.get')
def test_chat_history_handler_bad_request(mock_get):
    health_response = Mock()
    health_response.status_code = 200
    health_response.text = "chat_history service is healthy"

    bad_response = Mock()
    bad_response.status_code = 400
    bad_response.text = "Bad request"

    mock_get.side_effect = [health_response, bad_response]

    handler = ChatHistoryHandler("http://localhost:8080")

    with pytest.raises(ValueError) as error:
        handler.retrieve_chat_history("test_history_id", "test_token")

    assert "Bad request while retrieving conversation history" in str(error.value)

def test_validate_chat_history_with_valid_data():
    handler = ChatHistoryHandler()
    con_history = mock_default_input_data_short_history()
    assert handler.validate_chat_history(con_history) is True

def test_validate_chat_history_with_none():
    handler = ChatHistoryHandler()
    assert handler.validate_chat_history(None) is False

def test_validate_chat_history_with_empty_list():
    handler = ChatHistoryHandler()
    assert handler.validate_chat_history([]) is False

def test_validate_chat_history_with_empty_strings():
    handler = ChatHistoryHandler()
    con_history = [PrevQuestionDetails(question="", answer="")]
    assert handler.validate_chat_history(con_history) is False
