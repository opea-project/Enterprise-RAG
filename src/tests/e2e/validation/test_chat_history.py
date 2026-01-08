#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest

from tests.e2e.validation.buildcfg import cfg

# Skip all tests if chat_history is not deployed
if not cfg.get("chat_history", {}).get("enabled"):
    pytestmark = pytest.mark.skip(reason="Chat history is not deployed")

logger = logging.getLogger(__name__)
SIMPLE_CHAT_HISTORY = [
    {
    "question": "What is the capital of Poland?", "answer": "Warsaw.", "metadata": {}
    },
    {
    "question": "What is the capital of France?", "answer": "Paris.", "metadata": {}
    }
]


@pytest.fixture(autouse=True)
def cleanup(chat_history_helper):
    clean_all_history(chat_history_helper)
    yield
    clean_all_history(chat_history_helper)


@allure.testcase("IEASG-T209")
def test_save_chat_history(chat_history_helper):
    response = chat_history_helper.save_history(SIMPLE_CHAT_HISTORY)

    assert response.status_code == 200, f"Failed to save chat history, {response.text}"
    history_id = response.json().get("id")
    response = chat_history_helper.get_history_details(history_id)
    output_chat_history = response.json()["history"]
    assert output_chat_history == SIMPLE_CHAT_HISTORY, f"Chat history is not the same, {output_chat_history} =/= {SIMPLE_CHAT_HISTORY}"


@allure.testcase("IEASG-T214")
def test_append_chat_history(chat_history_helper):
    chat_history_appendage = [
        {
        "question": "What is your name?", "answer": "It is Arthur, King of the Brittons.", "metadata": {}
        },
        {
        "question": "What is your quest?", "answer": "To seek the Holy Grail.", "metadata": {}
        },
    ]
    response = chat_history_helper.save_history(SIMPLE_CHAT_HISTORY)
    history_id = response.json().get("id")
    response = chat_history_helper.get_history_details(history_id)
    output_chat_history = response.json()["history"]
    assert output_chat_history == SIMPLE_CHAT_HISTORY, f"Chat history is not the same, {output_chat_history} =/= {SIMPLE_CHAT_HISTORY}"
    
    response = chat_history_helper.save_history(chat_history_appendage, history_id)

    assert response.status_code == 200, f"Failed to save chat history, {response.text}"
    appended_history_id = response.json().get("id")
    assert appended_history_id == history_id, f"History Id's differ, id before append:{history_id}, id after append: {appended_history_id}"
    response = chat_history_helper.get_history_details(appended_history_id)
    output_appended_chat_history = response.json()["history"]
    for qna in chat_history_appendage:
        assert qna in output_appended_chat_history, f"Appened history missing from output, {output_appended_chat_history}"
    for qna in SIMPLE_CHAT_HISTORY:
        assert qna in output_appended_chat_history, f"Base history missing from output, {output_appended_chat_history}"


@allure.testcase("IEASG-T210")
def test_get_all_histories(chat_history_helper):
    additional_chat_history = [ 
        {
        "question": "What is the capital of Germany?", "answer": "Berlin.", "metadata": {}
        }
    ]
    response = chat_history_helper.save_history(SIMPLE_CHAT_HISTORY)
    history_id1 = response.json().get("id")
    response = chat_history_helper.save_history(additional_chat_history)
    history_id2 = response.json().get("id")
    response = chat_history_helper.get_all_histories()

    assert response.status_code == 200, f"Failed to get all chat history, {response.text}"
    for history in response.json():
        assert history["id"] == history_id1 or history["id"] == history_id2, \
            f"History list does not contain one or more histories, output: {response.json()}, id1: {history_id1}, id2: {history_id2}"


@allure.testcase("IEASG-T211")
def test_get_history_details(chat_history_helper):
    response = chat_history_helper.save_history(SIMPLE_CHAT_HISTORY)
    history_id = response.json().get("id")

    response = chat_history_helper.get_history_details(history_id)

    assert response.status_code == 200, f"Failed to get chat history, {response.text}"
    output_chat_history = response.json()["history"]
    assert output_chat_history == SIMPLE_CHAT_HISTORY, f"Chat history is not the same, {output_chat_history} =/= {SIMPLE_CHAT_HISTORY}"


@allure.testcase("IEASG-T212")
def test_change_history_name(chat_history_helper):
    response = chat_history_helper.save_history(SIMPLE_CHAT_HISTORY)
    history_id = response.json().get("id")

    new_history_name = "Changed history name"
    response = chat_history_helper.change_history_name(history_id, new_history_name)

    assert response.status_code == 200, f"Failed to change chat history name, {response.text}"
    response = chat_history_helper.get_history_details(history_id)
    assert response.json()["history_name"] == new_history_name, \
        f"History name is incorrect, history name: {response.json()["history_name"]}, expected name: {new_history_name}"


@allure.testcase("IEASG-T213")
def test_delete_history_by_id(chat_history_helper):
    response = chat_history_helper.save_history(SIMPLE_CHAT_HISTORY)
    assert response.status_code == 200, f"Failed to save chat history, {response.text}"
    history_id = response.json().get("id")

    response = chat_history_helper.delete_history_by_id(history_id)

    assert response.status_code == 200, f"Failed to delete chat history {history_id}, {response.text}"
    response = chat_history_helper.get_history_details(history_id)
    assert response.status_code == 400, f"Unexpected status of getting history details after deletion, {response.text}"


@allure.testcase("IEASG-T238")
def test_empty_history(chat_history_helper):
    """Check the behavior when empty conversation history is passed"""
    # Empty list
    response = chat_history_helper.save_history([])
    assert response.status_code == 422, (f"Unexpected status code returned: {response.status_code}. "
                                         f"Answer: {response.text}")

    # A list of empty values
    response = chat_history_helper.save_history([{"question": "", "answer": ""}])
    assert response.status_code == 422, (f"Unexpected status code returned: {response.status_code}. "
                                         f"Answer: {response.text}")

    # A list with empty dict
    response = chat_history_helper.save_history([{}])
    assert response.status_code == 422, (f"Unexpected status code returned: {response.status_code}. "
                                         f"Answer: {response.text}")


def clean_all_history(chat_history_helper):
    response = chat_history_helper.get_all_histories()
    for history in response.json():
        history_id = history.get("id")
        response = chat_history_helper.delete_history_by_id(history_id)
