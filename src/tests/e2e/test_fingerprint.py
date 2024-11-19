#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import json
import pytest


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
        print(f"Fingerprint response: {response_json}")
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
