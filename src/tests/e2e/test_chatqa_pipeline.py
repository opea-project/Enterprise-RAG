#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest
import requests
import time
from api_request_helper import InvalidChatqaResponseBody


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T32")
def test_chatqa_timeout(chatqa_api_helper):
    """
    Bot is usually very talkative when asked about AVX512.
    The aim is to check if the response is no longer than 60 seconds what may
    lead to closing the connection on the server side.
    """
    question = "What is AVX512?"
    start_time = time.time()
    try:
        chatqa_api_helper.call_chatqa(question)
    except requests.exceptions.ChunkedEncodingError:
        duration = time.time() - start_time
        pytest.fail(f"Request has been closed on the server side after {duration} seconds")


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T31")
def test_chatqa_response_body(chatqa_api_helper):
    """
    Check if response is in a form of a Server-sent event.
    See: https://html.spec.whatwg.org/multipage/server-sent-events.html
    """
    question = "How much is 123 + 123?"
    response = chatqa_api_helper.call_chatqa(question)
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response.text)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(e)


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T30")
def test_chatqa_response_status_code_and_header(chatqa_api_helper):
    """
    Check status code and headers in a simple, positive scenario
    """
    question = "Is the earth flat?"
    response = chatqa_api_helper.call_chatqa(question)
    content_type_header = response.headers.get("Content-Type")
    assert response.status_code == 200, "Invalid HTTP status code returned"
    assert content_type_header == "text/event-stream", "Unexpected Content-Type header in response"


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T29")
def test_chatqa_pass_empty_question(chatqa_api_helper):
    """
    Check if 'Bad request' is returned in case user makes an invalid request
    """
    question = ""
    response = chatqa_api_helper.call_chatqa(question)
    assert response.status_code == 400, "Got unexpected status code"


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T28")
def test_chatqa_ask_in_polish(chatqa_api_helper):
    """
    This is to reproduce a defect:
    When chatbot was asked in a language other than English, a JSON response
    was returned with some complaints on the missing fields in the request
    """
    question = "Jaki jest najwyższy wieżowiec na świecie?"
    response = chatqa_api_helper.call_chatqa(question)
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response.text)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(e)
