#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import json
import logging
import pytest

logger = logging.getLogger(__name__)


@pytest.mark.smoke
@allure.testcase("IEASG-T51")
def test_fingerprint_append_arguments(fingerprint_api_helper):
    """
    Do the simple call to /v1/append_arguments. Check:
    - status code
    - headers
    - body is a JSON object
    - body contains the original text passed as a parameter
    """
    text = "qwerty"
    response = fingerprint_api_helper.append_arguments(text)
    assert response.status_code == 200, "Unexpected status code"
    assert response.headers.get("Content-Type") == "application/json"
    try:
        response_json = response.json()
        logger.info(f"Fingerprint response: {response_json}")
    except json.decoder.JSONDecodeError:
        pytest.fail("Response is not a valid JSON")
    assert response_json.get("text") == text


@pytest.mark.smoke
@allure.testcase("IEASG-T52")
def test_fingerprint_parameters_modification(fingerprint_api_helper):
    """
    Fingerprint append_arguments API call returns some defined structure of data:
    {
        "parameters": {"max_new_tokens": 1024, ... }
    }
    Try to override max_new_tokens - it should not be changed in the response
    """
    invalid_body = {"parameters": {"max_new_tokens": 666}}
    response = fingerprint_api_helper.append_arguments_custom_body(invalid_body)
    max_new_tokens = response.json().get("parameters").get("max_new_tokens")
    assert max_new_tokens != 666, "'append argument' API call should not modify parameters"


@pytest.mark.smoke
@allure.testcase("IEASG-T53")
def test_fingerprint_change_arguments(fingerprint_api_helper):
    """
    Retrieve current value for max_new_tokens and increase its value by 1.
    Verify if the operation succeeded.
    """
    current_arguments = fingerprint_api_helper.append_arguments("")
    current_max_new_tokens = current_arguments.json()["parameters"]["max_new_tokens"]

    body = [
        {
            "name": "llm",
            "data": {
                "max_new_tokens": current_max_new_tokens + 1,
                "top_k": 10
            }
        }
    ]

    response = fingerprint_api_helper.change_arguments(body)
    assert response.status_code == 200, "Unexpected status code"
    new_arguments = fingerprint_api_helper.append_arguments("")
    new_value_max_new_tokens = new_arguments.json()["parameters"]["max_new_tokens"]
    assert new_value_max_new_tokens == current_max_new_tokens + 1


@allure.testcase("IEASG-T152")
def test_fingerprint_empty_prompt_template(fingerprint_api_helper, chatqa_api_helper):
    """
    Make /v1/system_fingerprint/change_arguments API call with an empty prompt_template.
    Expect status code 400 because there are no "{initial_query}" and "{reranked_docs}" keywords in the template.
    """
    current_arguments = fingerprint_api_helper.append_arguments("")
    original_prompt_template = current_arguments.json()["parameters"]["prompt_template"]
    body = [{
        "name": "prompt_template",
        "data": {
            "prompt_template": "123"
        }
    }]
    response = fingerprint_api_helper.change_arguments(body)
    if response.status_code == 200:
        logger.debug(f"Reverting prompt template to the original value: {original_prompt_template}")
        body = [{
            "name": "prompt_template",
            "data": {
                "prompt_template": original_prompt_template
            }
        }]
        fingerprint_api_helper.change_arguments(body)
    assert response.status_code == 400, "Unexpected status code"


@allure.testcase("IEASG-T151")
def test_fingerprint_change_prompt_template(fingerprint_api_helper, chatqa_api_helper):
    """
    Change the prompt_template to include a specific number. Call ChatQA and check if the response contains the number.
    """
    current_arguments = fingerprint_api_helper.append_arguments("")
    original_prompt_template = current_arguments.json()["parameters"]["prompt_template"]
    body = [{
        "name": "prompt_template",
        "data": {
            "prompt_template": "### Always include number '1234' in your response so that I can identify you. \n\n### Search results: {reranked_docs} \n\n### Question: {initial_query} \n\n### Answer: \n"
        }
    }]
    change_prompt_response = fingerprint_api_helper.change_arguments(body)
    try:
        assert change_prompt_response.status_code == 200, "Unexpected status code for prompt template modification call"
        response = chatqa_api_helper.call_chatqa("What is the capital of France?")
        assert response.status_code == 200, "Unexpected status code when calling ChatQA with modified prompt template"
        chatbot_response = chatqa_api_helper.format_response(response)
        logger.info(f"ChatQA response after modifying prompt template: {chatbot_response}")
        assert "1234" in chatbot_response, "Response does not contain the expected number '1234'"
    finally:
        logger.info(f"Reverting prompt template to the original value: {original_prompt_template}")
        body = [{
            "name": "prompt_template",
            "data": {
                "prompt_template": original_prompt_template
            }
        }]
        fingerprint_api_helper.change_arguments(body)
