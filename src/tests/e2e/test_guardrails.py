#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

from guard_helper import GuardHelper, GuardType, GuardQuestions as questions


@pytest.fixture
def guard_helper(chatqa_api_helper, fingerprint_api_helper):
    return GuardHelper(chatqa_api_helper, fingerprint_api_helper)


@allure.testcase("IEASG-T72")
def test_in_guard_anonymize(guard_helper):
    """
    Enable "anonymize" input scanner and check if questions with PII
    (Personally Identifiable Information) are rejected
    """
    # TODO: experiment with other parameters once anonymize scaner working as expected
    guard_params = {
        "enabled": True
        # "use_onnx":true,
        # "hidden_names":"None",
        # "allowed_names":"None",
        # "entity_types":"None",
        # "preamble":"None",
        # "regex_patterns":"None",
        # "use_faker":"None",
        # "recognizer_conf":"None",
        # "threshold":"None",
        # "language":"None"
    }
    guard_helper.setup(GuardType.INPUT, "anonymize", guard_params)
    guard_helper.assert_blocked(questions.CONTAINING_SENSITIVE_DATA)


@allure.testcase("IEASG-T73")
def test_in_guard_ban_code(guard_helper):
    """
    Enable "ban_code" input scanner and check if questions containing code samples are rejected.
    Check both (MODEL_SM and MODEL_TINY) models.
    """
    languages_not_banned = []
    models = ["MODEL_SM", "MODEL_TINY"]
    for model in models:
        guard_params = {
            "enabled": True,
            "use_onnx": True,
            "model": model,
            "threshold": 0.9
        }
        guard_helper.setup(GuardType.INPUT, "ban_code", guard_params)
        for language, code_snippet in guard_helper.code_snippets().items():
            response = guard_helper.call_chatqa(code_snippet)
            if response.status_code != 466:
                languages_not_banned.append(f"{language} ({model})")

    assert languages_not_banned == [], \
        f"Code snippets for the following languages: {languages_not_banned} were not banned"


@allure.testcase("IEASG-T74")
def test_in_guard_ban_competitors(guard_helper):
    """
    Enable "ban_competitors" input scanner with a custom list of competitors.
    Check if questions related to the competitors from the list are rejected.
    """
    guard_params = {
        "enabled": True,
        "use_onnx": True,
        "competitors": ["Bing"],
        "model": "MODEL_V1",
        "threshold": 0.5,
        "redact": True
    }
    guard_helper.setup(GuardType.INPUT, "ban_competitors", guard_params)
    guard_helper.assert_blocked(questions.BING)

    guard_params["competitors"] = ["AMD", "Nvidia"]
    guard_helper.setup(GuardType.INPUT, "ban_competitors", guard_params)
    guard_helper.assert_blocked(questions.AMD)
    guard_helper.assert_blocked(questions.NVIDIA)
    guard_helper.assert_blocked(questions.AMD_WITH_SUFFIX)
    guard_helper.assert_allowed(questions.INTEL)


@allure.testcase("IEASG-T75")
def test_in_guard_ban_substrings(guard_helper):
    """
    Enable "ban_substring" input scanner. Check if questions are rejected in the following scenarios:
    - case_sensitive = True (check if case_sensitive working as designed)
    - match_all = True (check if rejected only when all substrings are matched)
    - match_type (check "str" and "word" match type)
    """
    guard_params = {
        "enabled": True,
        "substrings": ["malware", "virus"],
        "match_type": "word",
        "redact": True,
        "case_sensitive": True,
        "contains_all": True
    }
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.MALWARE_AND_VIRUS)
    guard_helper.assert_allowed(questions.MALWARE_AND_VIRUS_CASE_SENSITIVE)
    guard_helper.assert_allowed(questions.MALWARE)
    guard_helper.assert_allowed(questions.MALWARE_AND_VIRUS_SUBSTRINGS)

    guard_params["substrings"] = ["run"]
    guard_params["match_type"] = "str"
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.CHECK_SUBSTRING_MATCH_TYPE)

    guard_params["substrings"] = ["run", "yell"]
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.CHECK_SUBSTRING_MATCH_TYPE_MULTIPLE_WORDS)


@allure.testcase("IEASG-T76")
def test_in_guard_ban_topics(guard_helper):
    """
    Enable "ban_topics " input scanner. Check if questions are rejected in the following scenarios:
    - for "violence", "attack", "war" topics - ask questions related to violence etc.
    - for "medical advice" - ask questions related to medical advice
    Also, check if questions not related to these topics are not rejected.
    """

    questions_not_banned = []
    guard_params = {
        "enabled": True,
        "topics": ["medical advice"],
        "threshold": 0.5,
        "model": "MODEL_BGE_M3_V2"
    }
    guard_helper.setup(GuardType.INPUT, "topics", guard_params)
    for question in questions.MEDICAL_ADVICE:
        response = guard_helper.call_chatqa(question)
        if response.status_code != 466:
            questions_not_banned.append(question)

    guard_params["topics"] = ["violence", "attack", "war"]
    guard_helper.setup(GuardType.INPUT, "topics", guard_params)
    for question in questions.VIOLENCE_QUESTIONS:
        response = guard_helper.call_chatqa(question)
        if response.status_code != 466:
            questions_not_banned.append(question)

    for question in questions.NON_VIOLENCE_QUESTIONS:
        response = guard_helper.call_chatqa(question)
        assert response.status_code == 200, "Question should not be blocked"
    assert questions_not_banned == [], "Some of the questions were not banned"


@allure.testcase("IEASG-T77")
def test_in_guard_code(guard_helper):
    """
    Enable "code" input scanner with some languages that should be blocked.
    Check if questions containing code snippets in a language from the list are rejected.
    Also, check if other languages are allowed.
    """
    guard_params = {
        "enabled": True,
        "languages": ["JavaScript", "Python"],
        "is_blocked": True,
        "threshold": 0.95
    }
    guard_helper.setup(GuardType.INPUT, "code", guard_params)
    code_snippets = guard_helper.code_snippets()

    # Python and JavaScript related questions should be blocked
    for language_key in ["javascript", "python", "python_with_plain_text"]:
        guard_helper.assert_blocked(code_snippets[language_key], "it is in language that is marked as blocked")

    # Questions with other languages should not be blocked
    for language_key in ["c++", "ruby"]:
        guard_helper.assert_allowed(
            code_snippets[language_key], "it is in language that is not marked as blocked")


@allure.testcase("IEASG-T78")
def test_in_guard_gibberish(guard_helper):
    """Check if questions that are not logical (gibberish) and making no sense are rejected"""

    guard_helper.setup(GuardType.INPUT, "gibberish", {"enabled": True, "match_type": "full"})
    guard_helper.assert_blocked(questions.GIBBERISH_LONG, "it is gibberish")
    guard_helper.assert_blocked(questions.GIBBERISH_SHORT, "it is gibberish")
    guard_helper.assert_allowed(questions.NON_GIBBERISH, "it is not gibberish although it is pretty long")


@allure.testcase("IEASG-T81")
def test_in_guard_invisible_text(guard_helper):
    """Check if question with invisible white character is blocked"""
    guard_helper.setup(GuardType.INPUT, "invisible_text", {"enabled": True})
    guard_helper.assert_blocked(questions.INVISIBLE_TEXT, "it contains prohibited characters")
    guard_helper.assert_allowed(questions.NO_INVISIBLE_TEXT)


@allure.testcase("IEASG-T82")
def test_in_guard_language(guard_helper):
    """Check if questions in some specified languages are blocked or allowed"""
    guard_params = {
        "enabled": True,
        "use_onnx": True,
        "valid_languages": ["en"],
        "model": None,
        "threshold": None,
        "match_type": None
    }
    guard_helper.setup(GuardType.INPUT, "language", guard_params)
    guard_helper.assert_allowed(questions.ENGLISH, "it is in English")

    languages_not_banned = []
    for language, question in questions.LANGUAGE_SPECIFIC.items():
        response = guard_helper.call_chatqa(question)
        if response.status_code != 466:
            languages_not_banned.append(language)
    assert languages_not_banned == [], f"Questions in the following languages: {languages_not_banned} were not banned."


@allure.testcase("IEASG-T83")
def test_in_guard_prompt_injection(guard_helper):
    """
    Check if prompt_injection guard can detect malicious input that can manipulate the AI into
    providing incorrect or harmful outputs.
    """
    guard_params = {
       "enabled": True,
       "use_onnx": True
    }
    guard_helper.setup(GuardType.INPUT, "prompt_injection", guard_params)
    guard_helper.assert_blocked(questions.DAN)
    guard_helper.assert_blocked(questions.EVIL)
    guard_helper.assert_blocked(questions.KEVIN)
    guard_helper.assert_allowed(questions.DRUNK_GUY)
    guard_helper.assert_allowed(questions.BILL_GATES)

    guard_params["match_type"] = "sentence"
    guard_helper.setup(GuardType.INPUT, "prompt_injection", guard_params)
    guard_helper.assert_blocked(questions.DAN)
    guard_helper.assert_blocked(questions.EVIL)
    guard_helper.assert_blocked(questions.KEVIN)


@allure.testcase("IEASG-T84")
def test_in_guard_regex(guard_helper):
    """Check is scanner detects the predefined regex expressions and blocks/allows questions accordingly"""
    guard_params = {
        "enabled": True,
        "patterns": [
            "Bearer [A-Za-z0-9-._~+/]+",
            "^\d{3}-\d{2}-\d{4}$"
        ],
    }
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.BEARER)
    guard_helper.assert_blocked(questions.SSN_NUMBER)

    guard_params["is_blocked"] = False
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_allowed(questions.SSN_NUMBER)

    guard_params["is_blocked"] = True
    guard_params["match_type"] = "fullmatch"
    guard_helper.assert_allowed(questions.SSN_NUMBER)
