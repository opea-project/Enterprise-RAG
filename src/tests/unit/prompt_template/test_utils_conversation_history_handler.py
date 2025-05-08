# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest

from comps import (
    PrevQuestionDetails
)

from comps.prompt_template.utils.conversation_history_handler import ConversationHistoryHandler

@pytest.fixture
def mock_default_input_data_short_history():
    return [
            PrevQuestionDetails(question="Previous question 1", answer="Previous answer 1"),
            PrevQuestionDetails(question="Previous question 2", answer="Previous answer 2"),
            ]

@pytest.fixture
def mock_default_input_data_long_history():
    return [
            PrevQuestionDetails(question="Previous question 1", answer="Previous answer 1"),
            PrevQuestionDetails(question="Previous question 2", answer="Previous answer 2"),
            PrevQuestionDetails(question="Previous question 3", answer="Previous answer 3"),
            PrevQuestionDetails(question="Previous question 4", answer="Previous answer 4"),
            PrevQuestionDetails(question="Previous question 5", answer="Previous answer 5"),
            PrevQuestionDetails(question="Previous question 6", answer="Previous answer 6"),
            ]

def test_conversation_history_handler_naive_correct_parse_short_input(mock_default_input_data_short_history):
    handler = ConversationHistoryHandler()
    parsed_output = handler.parse_conversation_history(mock_default_input_data_short_history, "naive")

    assert parsed_output == "previous_question: Previous question 1 previous_answer: Previous answer 1 previous_question: Previous question 2 previous_answer: Previous answer 2"

def test_conversation_history_handler_naive_correct_parse_long_input(mock_default_input_data_long_history):
    handler = ConversationHistoryHandler()
    parsed_output = handler.parse_conversation_history(mock_default_input_data_long_history, "naive")

    assert parsed_output == "previous_question: Previous question 4 previous_answer: Previous answer 4 previous_question: Previous question 5 previous_answer: Previous answer 5 previous_question: Previous question 6 previous_answer: Previous answer 6"

def test_conversation_history_handler_incorrect_type(mock_default_input_data_short_history):
    handler = ConversationHistoryHandler()
    with pytest.raises(ValueError) as error:
        handler.parse_conversation_history(mock_default_input_data_long_history, "wrong_type")

        assert "Incorrect ConversationHistoryHandler parsing type." in str(error.value)