#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
from copy import deepcopy
import pytest
import requests
import statistics
import time
from helpers.api_request_helper import InvalidChatqaResponseBody


@allure.testcase("IEASG-T32")
def test_chatqa_timeout(chatqa_api_helper):
    """
    The aim is to check if the response is no longer than 60 seconds what may
    lead to closing the connection on the server side.
    """
    question = ("Give me a python script that does a lot of stuff using different libraries. Then do the same for the "
                "following languages: C, C++, Ruby, C#, Java, JavaScript, Go")
    start_time = time.time()
    try:
        response = chatqa_api_helper.call_chatqa(question)
    except requests.exceptions.ChunkedEncodingError:
        duration = time.time() - start_time
        pytest.fail(f"Request has been closed on the server side after {duration} seconds")
    print(f"Response: {chatqa_api_helper.format_response(response)}")


@pytest.mark.smoke
@allure.testcase("IEASG-T31")
def test_chatqa_response_body(chatqa_api_helper):
    """
    Check if response is in a form of a Server-sent event.
    See: https://html.spec.whatwg.org/multipage/server-sent-events.html
    """
    question = "How much is 123 + 123?"
    response = chatqa_api_helper.call_chatqa(question)
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))


@allure.testcase("IEASG-T30")
def test_chatqa_response_status_code_and_header(chatqa_api_helper):
    """
    Check status code and headers in a simple, positive scenario
    """
    question = "Is the earth flat?"
    response = chatqa_api_helper.call_chatqa(question)
    content_type_header = response.headers.get("Content-Type")
    assert response.status_code == 200, "Invalid HTTP status code returned"
    assert content_type_header == "text/event-stream", "Unexpected Content-Type header in response"


@allure.testcase("IEASG-T29")
def test_chatqa_pass_empty_question(chatqa_api_helper):
    """
    Check if 'Bad request' is returned in case user makes an invalid request
    """
    question = ""
    response = chatqa_api_helper.call_chatqa(question)
    assert response.status_code == 400, "Got unexpected status code"


@pytest.mark.smoke
@allure.testcase("IEASG-T28")
def test_chatqa_ask_in_polish(chatqa_api_helper):
    """
    This is to reproduce a defect:
    When chatbot was asked in a language other than English, a JSON response
    was returned with some complaints on the missing fields in the request
    """
    question = "Jaki jest najwyższy wieżowiec na świecie?"
    response = chatqa_api_helper.call_chatqa(question)
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))


@allure.testcase("IEASG-T49")
def test_chatqa_enable_streaming(chatqa_api_helper):
    """
    Set 'streaming' parameter to True and check the response
    """
    question = "Don't answer me."
    parameters = {"parameters": {"streaming": True}}
    response = chatqa_api_helper.call_chatqa(question, **parameters)
    assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))


@pytest.mark.smoke
@allure.testcase("IEASG-T57")
def test_chatqa_with_fingerprint_args(chatqa_api_helper, fingerprint_api_helper):
    """Make /v1/chatqa call with all the parameters from fingerprint service"""
    question = "What are the key advantages of x86 architecture?"
    fingerprint_resp = fingerprint_api_helper.append_arguments(question)
    arguments = fingerprint_resp.json()
    response = chatqa_api_helper.call_chatqa(question, **arguments)
    assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))

@pytest.mark.smoke
@allure.testcase("IEASG-T58")
def test_chatqa_with_modified_fingerprint_args(chatqa_api_helper, fingerprint_api_helper):
    """
    Retrieve current arguments from fingerprint microservice.
    Change a couple of them (including max_new_token set to 10) and make a call to /v1/chatqa.
    Verify if the response content is no more than 10 words.
    Retrieve current arguments once again. Check if arguments are not modified.
    """
    question = "How close to the sun have we ever been?"
    fingerprint_resp = fingerprint_api_helper.append_arguments(question)
    arguments = fingerprint_resp.json()
    old_arguments = deepcopy(arguments)
    arguments["parameters"]["max_new_tokens"] = 10
    arguments["parameters"]["top_k"] = 12
    arguments["parameters"]["fetch_k"] = 200
    response = chatqa_api_helper.call_chatqa(question, **arguments)
    assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
    try:
        response_text = chatqa_api_helper.format_response(response)
        print(f"ChatQA response: {response_text}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))
    assert len(response_text.split()) <= 10, \
        "/v1/chatqa API call made with max_new_tokens set to 10. Expecting the answer to be less than 10 words"
    refreshed_resp = fingerprint_api_helper.append_arguments(question)
    assert refreshed_resp.json() == old_arguments


@pytest.mark.smoke
@allure.testcase("IEASG-T42")
def test_chatqa_concurrent_requests(chatqa_api_helper):
    """
    Ask 100 concurrent questions. Measure min, max, avg response time.
    Check if all requests were processed successfully.
    """
    concurrent_requests = 100
    question = "How big is the universe?"
    execution_times = []
    questions = []
    failed_requests_counter = 0

    for _ in range(0, concurrent_requests):
        questions.append(question)

    results = chatqa_api_helper.call_chatqa_in_parallel(questions)
    for result in results:
        if result.exception is not None:
            print(result.exception)
            failed_requests_counter = + 1
        elif result.status_code != 200:
            print(f"Request failed with status code {result.status_code}. Response body: {result.text}")
            failed_requests_counter += 1
        else:
            execution_times.append(result.response_time)

    mean_time = statistics.mean(execution_times)
    max_time = max(execution_times)
    min_time = min(execution_times)

    print(f'Total requests: {len(questions)}')
    print(f'Failed requests: {failed_requests_counter}')
    print(f'Mean Execution Time: {mean_time:.4f} seconds')
    print(f'Longest Execution Time: {max_time:.4f} seconds')
    print(f'Shortest Execution Time: {min_time:.4f} seconds')
    assert failed_requests_counter == 0, "Some of the requests didn't return HTTP status code 200"
