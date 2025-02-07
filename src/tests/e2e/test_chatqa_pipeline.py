#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
from copy import deepcopy
import json
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


@pytest.mark.smoke
@allure.testcase("IEASG-T31")
def test_chatqa_disable_streaming(chatqa_api_helper, fingerprint_api_helper):
    """
    Disable streaming. Check that the response is in JSON format. Check headers.
    """
    fingerprint_api_helper.set_streaming(False)
    response = chatqa_api_helper.call_chatqa("How much is 123 + 123?")
    assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
    assert "application/json" in response.headers.get("Content-Type"), \
        f"Unexpected Content-Type in the response. Headers: {response.headers}"
    try:
        response.json()
    except json.decoder.JSONDecodeError:
        pytest.fail(f"Response is not a valid JSON: {response.text}")


@allure.testcase("IEASG-T49")
def test_chatqa_enable_streaming(chatqa_api_helper, fingerprint_api_helper):
    """
    Enable streaming. Check that the response is in 'Server-Sent Events' format. Check headers.
    """
    fingerprint_api_helper.set_streaming(True)
    response = chatqa_api_helper.call_chatqa("Don't answer me.")
    assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
    assert "text/event-stream" in response.headers.get("Content-Type"), \
        f"Unexpected Content-Type in the response. Headers: {response.headers}"
    try:
        print(f"ChatQA response: {chatqa_api_helper.format_response(response)}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))


@pytest.mark.smoke
@allure.testcase("IEASG-T57")
def test_chatqa_change_max_new_tokens(chatqa_api_helper, fingerprint_api_helper):
    """
    Make /change_arguments API call to change max_new_tokens value.
    Make /chatqa API call to check if the value has been applied correctly.
    """
    fingerprint_api_helper.set_llm_parameters(max_new_tokens=5)
    question = "What are the key advantages of x86 architecture?"
    try:
        response = chatqa_api_helper.call_chatqa(question)
        assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
        try:
            response_text = chatqa_api_helper.format_response(response)
            print(f"ChatQA response: {response_text}")
        except InvalidChatqaResponseBody as e:
            pytest.fail(str(e))
        assert len(response_text.split()) <= 5
    finally:
        print("Reverting max_new_tokens value to 1024")
        fingerprint_api_helper.set_llm_parameters(max_new_tokens=1024)


@pytest.mark.smoke
@allure.testcase("IEASG-T58")
def test_chatqa_api_call_with_additional_parameters(chatqa_api_helper, fingerprint_api_helper):
    """
    Check that additional parameters passed to /v1/chatqa are not taken into account.
    Parameters may be modified with /change_arguments API call only.
    """
    question = "How close to the sun have we ever been?"
    fingerprint_resp = fingerprint_api_helper.append_arguments(question)
    arguments = fingerprint_resp.json()
    old_arguments = deepcopy(arguments)
    arguments["parameters"]["max_new_tokens"] = 5
    arguments["parameters"]["top_k"] = 12
    arguments["parameters"]["fetch_k"] = 200
    response = chatqa_api_helper.call_chatqa(question, **arguments)
    assert response.status_code == 200, f"Unexpected status code returned: {response.status_code}"
    try:
        response_text = chatqa_api_helper.format_response(response)
        print(f"ChatQA response: {response_text}")
    except InvalidChatqaResponseBody as e:
        pytest.fail(str(e))
    assert len(response_text.split()) > 5, \
        ("/v1/chatqa API call made with max_new_tokens set to 5. Expecting that additional parameters are not "
         "taken into account. Parameters may be modified with /change_arguments API call only.")
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
