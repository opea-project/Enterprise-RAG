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
                "max_new_tokens": current_max_new_tokens + 1
            }
        }
    ]

    try:
        response = fingerprint_api_helper.change_arguments(body)
        assert response.status_code == 200, "Unexpected status code"
        new_arguments = fingerprint_api_helper.append_arguments("")
        new_value_max_new_tokens = new_arguments.json()["parameters"]["max_new_tokens"]
        assert new_value_max_new_tokens == current_max_new_tokens + 1
    finally:
        logger.info(f"Reverting max_new_tokens value to {current_max_new_tokens}")
        body = [
            {
                "name": "llm",
                "data": {
                    "max_new_tokens": current_max_new_tokens
                }
            }
        ]
        fingerprint_api_helper.change_arguments(body)


@pytest.mark.xfail(reason="Fix to be implemented")
@allure.testcase("IEASG-T152")
def test_fingerprint_empty_prompt_template(fingerprint_api_helper, chatqa_api_helper):
    """
    Make /v1/system_fingerprint/change_arguments API call with an empty system_prompt_template and user_prompt_template.
    Expect status code 400 because there are no "{initial_query}" and "{reranked_docs}" keywords in the template.
    """
    current_arguments = fingerprint_api_helper.append_arguments("")
    original_system_prompt_template = current_arguments.json()["parameters"]["system_prompt_template"]
    original_user_prompt_template = current_arguments.json()["parameters"]["user_prompt_template"]
    body = [{
        "name": "prompt_template",
        "data": {
            "system_prompt_template": "123",
            "user_prompt_template": "123"
        }
    }]
    response = fingerprint_api_helper.change_arguments(body)
    if response.status_code == 200:
        logger.debug(f"Reverting prompt template to the original values: system: {original_system_prompt_template} user: {original_user_prompt_template}")
        body = [{
            "name": "prompt_template",
            "data": {
                "system_prompt_template": original_system_prompt_template,
                "user_prompt_template": original_user_prompt_template
            }
        }]
        fingerprint_api_helper.change_arguments(body)
    assert response.status_code == 400, "Unexpected status code"


@pytest.mark.smoke
@allure.testcase("IEASG-T151")
def test_fingerprint_change_prompt_template(fingerprint_api_helper, chatqa_api_helper):
    """
    Change the system_prompt_template to include a specific number. Call ChatQA and check if the response contains the number.
    """
    current_arguments = fingerprint_api_helper.append_arguments("")
    original_system_prompt_template = current_arguments.json()["parameters"]["system_prompt_template"]
    body = [{
        "name": "prompt_template",
        "data": {
            "system_prompt_template": "You are easily identifiable assistant that always includes string '1234' "
                               "somewhere in your response, even if it's not naturally required. "
                               "Always generate an answer that will contain '1234'."
                               "This is critical: your answer must contain '1234' or it will be considered incorrect. \n### Search results: "
                               "{reranked_docs} \n\n"
        }
    }]
    change_prompt_response = fingerprint_api_helper.change_arguments(body)
    try:
        assert change_prompt_response.status_code == 200, "Unexpected status code for prompt template modification call"
        response = chatqa_api_helper.call_chatqa("What is the capital of France?")
        assert response.status_code == 200, "Unexpected status code when calling ChatQA with modified prompt template"
        chatbot_response = chatqa_api_helper.get_text(response)
        logger.info(f"ChatQA response after modifying prompt template: {chatbot_response}")
        assert "1234" in chatbot_response, "Response does not contain the expected number '1234'"
    finally:
        logger.info(f"Reverting prompt template to the original value: {original_system_prompt_template}")
        body = [{
            "name": "prompt_template",
            "data": {
                "system_prompt_template": original_system_prompt_template
            }
        }]
        fingerprint_api_helper.change_arguments(body)


@allure.testcase("IEASG-T240")
def test_fingerprint_regular_user_can_access_fingerprint_api(fingerprint_api_helper, temporarily_remove_regular_user_required_actions):
    """Verify that append_arguments and change_arguments APIs are not accessible by regular users"""
    # Test append_arguments API
    result = fingerprint_api_helper.append_arguments("", as_user=True)
    assert result.status_code == 403, "Regular user should not be able to call append_arguments"

    # Test change_arguments API
    current_arguments = fingerprint_api_helper.append_arguments("")
    current_max_new_tokens = current_arguments.json()["parameters"]["max_new_tokens"]
    body = [
        {
            "name": "llm",
            "data": {
                "max_new_tokens": current_max_new_tokens + 1
            }
        }
    ]
    response = fingerprint_api_helper.change_arguments(body, as_user=True)
    assert response.status_code == 403
