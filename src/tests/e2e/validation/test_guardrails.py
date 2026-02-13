#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import json
import os
import pytest

from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR
from tests.e2e.helpers.guard_helper import GuardType, GuardQuestions as questions
from tests.e2e.validation.buildcfg import cfg

# Skip all tests if fingerprint is not deployed
if not cfg.get("fingerprint", {}).get("enabled"):
    pytestmark = pytest.mark.skip(reason="Fingerprint is not deployed")


@pytest.fixture(autouse=True)
def cleanup(guard_helper):
    yield
    guard_helper.disable_all_guards()


@pytest.mark.smoke
@allure.testcase("IEASG-T75")
def test_in_guard_ban_substrings(guard_helper):
    """
    Enable "ban_substring" input scanner and check if questions containing banned substrings are blocked or redacted.
    """
    guard_params = {
        "enabled": True,
        "substrings": ["malware", "virus"],
        "match_type": "word",
        "redact": False,
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

    # Check long substring
    long_substring = "a" * 1000
    guard_params = {"enabled": True, "substrings": [long_substring]}
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.LONG_PATTERN)
    guard_helper.assert_allowed(questions.SHORT_PATTERN)

    # Check special characters
    infinity_symbol = "\u221E"
    guard_params = {"enabled": True, "substrings": ["gżegżółka", infinity_symbol]}
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.COMMON_CUCKOO)
    guard_helper.assert_blocked(questions.INFINITY_SYMBOL)

    # Check case_sensitive = False
    guard_params = {"enabled": True, "substrings": ["VIRUS"], "case_sensitive": False}
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.MALWARE_AND_VIRUS)


@allure.testcase("IEASG-T244")
def test_in_guard_ban_substrings_when_string_injected_into_file(guard_helper, edp_helper):
    """
    Enable "ban_substrings" input scanner with "redact" parameter set to True.
    Upload a file containing one of the banned substrings.
    Ask a question containing the banned substring.
    Check if the answer does not contain information from the file.
    """
    guard_params = {"enabled": True, "substrings": ["Zerquilloo"], "case_sensitive": False, "redact": True}
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    _, response_text = guard_helper.call_chatqa(questions.ZERQUILLOO)
    assert "sound" not in response_text

    file = "word_zerquilloo_in_file.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file)
    edp_helper.upload_file_and_wait_for_ingestion(file_path)

    _, response_text = guard_helper.call_chatqa(questions.ZERQUILLOO)
    assert "sound" not in response_text, \
        "Answer should not contain information from the file because 'zerquilloo' word should be redacted"


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
    guard_helper.setup(GuardType.INPUT, "ban_topics", guard_params)
    for question in questions.MEDICAL_ADVICE:
        status_code, response = guard_helper.call_chatqa(question)
        if status_code != 466:
            questions_not_banned.append(question)

    guard_params["topics"] = ["violence", "attack", "war", "killing"]
    guard_helper.setup(GuardType.INPUT, "ban_topics", guard_params)
    for question in questions.VIOLENCE_QUESTIONS:
        status_code, response = guard_helper.call_chatqa(question)
        if status_code != 466:
            questions_not_banned.append(question)

    guard_params["topics"] = ["finance", "money", "stocks"]
    guard_helper.setup(GuardType.INPUT, "ban_topics", guard_params)
    for question in questions.FINANCE_QUESTIONS:
        status_code, response = guard_helper.call_chatqa(question)
        if status_code != 466:
            questions_not_banned.append(question)

    for question in questions.NON_VIOLENCE_QUESTIONS:
        status_code, response = guard_helper.call_chatqa(question)
        assert status_code == 200, "Question should not be blocked"
    assert questions_not_banned == [], "Some of the questions were not banned"


@allure.testcase("IEASG-T77")
def test_in_guard_code(guard_helper, code_snippets):
    """
    Enable "code" input scanner with some languages that should be blocked.
    Check if questions containing code snippets in a language from the list are rejected.
    Also, check if other languages are allowed.
    """
    guard_params = {
        "enabled": True,
        "languages": ["JavaScript", "Python", "Java", "C++"],
        "is_blocked": True,
        "threshold": 0.95
    }
    guard_helper.setup(GuardType.INPUT, "code", guard_params)

    # Questions with blocked languages should be blocked
    for language_key in ["javascript", "python", "python_with_plain_text", "c++", "python_v2", "c++_v2", "python_v3",
                         "java", "python_and_scala", "java_and_ruby"]:
        guard_helper.assert_blocked(code_snippets[language_key], reason="it is in language that is marked as blocked")

    # Questions with other languages should not be blocked
    for language_key in ["ruby", "scala"]:
        guard_helper.assert_allowed(
            code_snippets[language_key], reason="it is in language that is not marked as blocked")


@pytest.mark.xfail(reason="Feature not implemented yet - see IEASG-2040")
@allure.testcase("IEASG-T77")
def test_in_guards_invalid_input(guard_helper, code_snippets):
    """Try to set up input guards with invalid parameters. Check if 400 error is returned."""
    invalid_inputs_that_did_not_fail = {}
    invalid_input_examples = {
        "prompt_injection": [
            {"enabled": "True"},  # lacking use_onnx required parameter
            {"enabled": True, "use_onnx": True, "injection_model": "invalid_value"},
            {"enabled": True, "use_onnx": True, "injection_threshold": "string instead of float"},
            {"enabled": True, "use_onnx": True, "injection_threshold": 1.1},  # out of range
            {"enabled": True, "use_onnx": True, "injection_threshold": -1.1},  # out of range
            {"enabled": True, "use_onnx": True, "match_type": "invalid value"},
        ],
        "ban_substrings": [
            {"enabled": True},  # missing required substrings parameter
            {"enabled": True, "substrings": []},  # empty list
            {"enabled": True, "substrings": [" "]},  # empty substring
            {"enabled": True, "substrings": ["virus"], "match_type": "invalid value"},
            {"enabled": True, "substrings": ["virus"], "case_sensitive": "invalid value"},
            {"enabled": True, "substrings": ["virus"], "redact": "invalid value"},
            {"enabled": True, "substrings": ["virus"], "contains_all": "invalid value"},
        ],
        "code": [
            {"enabled": True,  "use_onnx": True},  # lacking required languages parameter
            {"enabled": True, "languages": [" "]},  # lacking required use_onnx parameter
            {"enabled": True, "use_onnx": True, "languages": [" "]},  # empty language
            {"enabled": True, "use_onnx": True, "languages": ["c++"]},  # lowercase language (should be C++)
            {"enabled": True, "use_onnx": True, "languages": ["C++"], "model": "invalid value"},
            {"enabled": True, "use_onnx": True, "languages": ["C++"], "is_blocked": "invalid value"},
            {"enabled": True, "use_onnx": True, "languages": ["C++"], "threshold": "invalid value"},
            {"enabled": True, "use_onnx": True, "languages": ["C++"], "threshold": 1.1},  # out of range
            {"enabled": True, "use_onnx": True, "languages": ["C++"], "threshold": -1.1},  # out of range
        ],
        "regex": [
            {"enabled": True},  # missing required patterns parameter
            {"enabled": True, "patterns": []},  # empty list
            {"enabled": True, "patterns": ["("]},  # invalid regex
            {"enabled": True, "patterns": ["\\"]},  # invalid regex
            {"enabled": True, "patterns": ["virus"], "is_blocked": "invalid value"},
            {"enabled": True, "patterns": ["virus"], "redact": "invalid value"},
            {"enabled": True, "patterns": ["virus"], "match_type": "invalid value"},
        ],
        "secrets": [
            {"enabled": True, "redact_mode": "invalid value"}
        ],
        "sentiment": [
            {"enabled": True, "lexicon": "invalid value"},
            {"enabled": True, "threshold": "string instead of float"},
            {"enabled": True, "threshold": 1.1},  # out of range
            {"enabled": True, "threshold": -1.1},  # out of range
        ],
        "token_limit": [
            {"enabled": True},  # missing required limit parameter
            {"enabled": True, "limit": "string instead of int"},
            {"enabled": True, "limit": -10},  # out of range
            {"enabled": True, "limit": 0},  # out of range
            {"enabled": True, "limit": 5000, "encoding_name": "invalid value"},
            {"enabled": True, "limit": 5000, "model_name": "invalid value"},
        ],
        "toxicity": [
            {"enabled": True},  # missing required use_onnx parameter
            {"enabled": True, "use_onnx": True, "threshold": "string instead of float"},
            {"enabled": True, "use_onnx": True, "threshold": 1.1},  # out of range
            {"enabled": True, "use_onnx": True, "threshold": -1.1},  # out of range
            {"enabled": True, "use_onnx": True, "model": "invalid value"},
            {"enabled": True, "use_onnx": True, "match_type": "invalid value"},
        ]
    }

    for guard_name, invalid_inputs in invalid_input_examples.items():
        for invalid_input in invalid_inputs:
            result = guard_helper.setup(GuardType.INPUT, guard_name, invalid_input)
            if result.status_code != 400:
                if invalid_inputs_that_did_not_fail.get(guard_name) is None:
                    invalid_inputs_that_did_not_fail[guard_name] = []
                invalid_inputs_that_did_not_fail[guard_name].append(invalid_input)

    assert invalid_inputs_that_did_not_fail == {}, \
        f"Some invalid inputs did not cause 400 error: {invalid_inputs_that_did_not_fail}"


@allure.testcase("IEASG-T81")
def test_in_guard_invisible_text(guard_helper):
    """Check if question with invisible white character is blocked"""
    guard_helper.setup(GuardType.INPUT, "invisible_text", {"enabled": True})

    for question in questions.INVISIBLE_TEXTS:
        guard_helper.assert_blocked(question, reason="it contains prohibited characters")

    guard_helper.assert_allowed(questions.NO_INVISIBLE_TEXT)


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
    """Check if scanner detects the predefined regex expressions and blocks/allows questions accordingly"""
    guard_params = {
        "enabled": True,
        "redact": False,  # e2e will not test redact mode
        "patterns": [
            r"\d{5}"
        ],
    }
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.NUMBER_12345)

    # Check "is_blocked" parameter
    guard_params['is_blocked'] = False  # If True, patterns are treated as 'bad'; if False, as 'good'
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.NUMBER_991)
    guard_helper.assert_allowed(questions.NUMBER_13456)
    guard_params['is_blocked'] = True
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.NUMBER_13456)
    guard_helper.assert_allowed(questions.NUMBER_991)
    guard_helper.assert_allowed(questions.NUMBER_789_456)

    # Block email address
    guard_params["patterns"] = [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"]
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.JANE_EMAIL)
    guard_helper.assert_allowed(questions.MISSING_AT_SYMBOL)
    guard_helper.assert_allowed(questions.INVALID_DOMAIN_EMAIL)

    # Check unicode support
    guard_params["patterns"] = [r'\b\wą\w\b']  # words with 3 letters and "ą" inside
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.UNICODE_QUESTION)


@pytest.mark.smoke
@allure.testcase("IEASG-T85")
def test_in_guard_secrets(guard_helper):
    """Check if scanner detects secrets (like token, keys)"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.INPUT, "secrets", guard_params)
    guard_helper.assert_blocked(questions.GH_TOKEN)
    guard_helper.assert_blocked(questions.API_KEY)
    guard_helper.assert_allowed(questions.LEGIT)

    for sentences in questions.SECRETS_BLOCKED_SENTENCES:
        guard_helper.assert_blocked(sentences, reason="it contains secrets")

    for sentences in questions.SECRETS_SAFE_SENTENCES:
        guard_helper.assert_allowed(sentences, reason="it does not contain secrets")


@allure.testcase("IEASG-T86")
def test_in_guard_sentiment(guard_helper):
    """Check if sentiment scanner can properly identify negative sentiment in the question asked by the user"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.INPUT, "sentiment", guard_params)
    guard_helper.assert_blocked(questions.NEGATIVE_SENTIMENT)
    guard_helper.assert_allowed(questions.NEUTRAL_SENTIMENT)

    for sentence in questions.MORE_NEGATIVE_SENTIMET:
        guard_helper.assert_blocked(sentence, reason="it contains negative sentiment")

    for sentence in questions.MORE_NEUTRAL_SENTIMENT:
        guard_helper.assert_allowed(sentence, reason="it does not contain negative sentiment")

    guard_helper.assert_blocked(
        questions.MIXED_SENTIMENT, reason="Mixed sentiment should be blocked (most restrictive policy should win)")

    guard_params["threshold"] = 0.9
    guard_helper.setup(GuardType.INPUT, "sentiment", guard_params)
    guard_helper.assert_blocked(
        questions.NEUTRAL_SENTIMENT, reason="0.9 means very positive sentiment so neutral question should be blocked")


@allure.testcase("IEASG-T87")
def test_in_guard_token_limit(guard_helper):
    """Check if user's input do not exceed specified token limit"""
    guard_params = {
        "enabled": True,
        "limit": 10
    }
    guard_helper.setup(GuardType.INPUT, "token_limit", guard_params)
    guard_helper.assert_blocked(questions.OVER_LIMIT)
    guard_helper.assert_allowed(questions.BELOW_LIMIT)

    for sentence in questions.MORE_OVER_LIMIT:
        guard_helper.assert_blocked(sentence, reason="it exceeds token limit")


@allure.testcase("IEASG-T88")
def test_in_guard_toxicity(guard_helper):
    """Check if question contains toxic, harmful, or offensive content"""
    guard_params = {
        "enabled": True,
        "threshold": 0.35
    }
    guard_helper.setup(GuardType.INPUT, "toxicity", guard_params)
    guard_helper.assert_blocked(questions.LOW_TOXICITY)
    guard_helper.assert_blocked(questions.THREAT)
    guard_helper.assert_blocked(questions.INSULTING)
    for sentence in questions.MORE_TOXIC:
        guard_helper.assert_blocked(sentence, reason="it contains toxic content")

    guard_helper.assert_allowed(questions.NON_TOXIC)

    guard_params["match_type"] = "sentence"
    guard_helper.setup(GuardType.INPUT, "toxicity", guard_params)
    guard_helper.assert_blocked(questions.INSULTING_MIXED)


@allure.testcase("IEASG-T245")
def test_in_guard_mix(guard_helper, code_snippets):
    """
    Enable multiple input guards at the same time. One of the guards should block the question,
    another should allow it. Check if the question is blocked (most restrictive policy should win).
    """
    # Code scanner should block scala snippet
    guard_params = {
        "enabled": True,
        "languages": ["Scala"]
    }
    guard_helper.setup(GuardType.INPUT, "code", guard_params)

    # ban_substrings scanner should not block the question
    guard_params = {
        "enabled": True,
        "substrings": ["substring does not appear in the question"]
    }
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)

    guard_helper.assert_blocked(
        code_snippets["scala"], reason="Scala code was detected even though ban_substrings guard allowed the question")


@allure.testcase("IEASG-T90")
def disabled_test_out_guard_ban_substrings(guard_helper):
    """Check if question is blocked or redacted when certain words appears in the answer"""
    guard_params = {
        "enabled": True,
        "substrings": ["lewandowski", "mariusz"]
    }
    # Check contains_all
    guard_helper.setup(GuardType.OUTPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.LEWANDOWSKI)
    guard_params["contains_all"] = True
    guard_helper.setup(GuardType.OUTPUT, "ban_substrings", guard_params)
    guard_helper.assert_allowed(questions.LEWANDOWSKI)

    # Check redact
    guard_params["contains_all"] = False
    guard_params["redact"] = True
    guard_helper.setup(GuardType.OUTPUT, "ban_substrings", guard_params)
    guard_helper.assert_redacted(questions.LEWANDOWSKI)

    # Check case_sensitive
    guard_params["redact"] = False
    guard_params["substrings"] = ["lewanDowski"]
    guard_params["case_sensitive"] = True
    guard_helper.setup(GuardType.OUTPUT, "ban_substrings", guard_params)
    guard_helper.assert_allowed(questions.LEWANDOWSKI)

    # Check match_type
    guard_params["substrings"] = ["lewan"]
    guard_params["case_sensitive"] = False
    guard_params["match_type"] = "str"
    guard_helper.setup(GuardType.OUTPUT, "ban_substrings", guard_params)
    guard_helper.assert_blocked(questions.LEWANDOWSKI)
    guard_params["match_type"] = "word"
    guard_helper.setup(GuardType.OUTPUT, "ban_substrings", guard_params)
    guard_helper.assert_allowed(questions.LEWANDOWSKI)


@allure.testcase("IEASG-T91")
def disabled_test_out_guard_bias(guard_helper):
    """Check if output scanner detects biased statements in text"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "bias", guard_params)
    guard_helper.assert_blocked(questions.RIGHT_WING)
    guard_helper.assert_allowed(questions.TRAVEL_DESTINATION)

    guard_params["match_type"] = "sentence"
    guard_helper.setup(GuardType.OUTPUT, "bias", guard_params)
    guard_helper.assert_blocked(questions.RIGHT_WING)


@allure.testcase("IEASG-T93")
def disabled_test_out_guard_code(guard_helper):
    """
    Define a list of blocked languages. Then check if the output generated by LLM contains some code samples
    in these languages. If so, make sure the question is blocked. Check opposite case as well.
    """
    guard_params = {
        "enabled": True,
        "languages": ["C++", "Python"]
    }
    guard_helper.setup(GuardType.OUTPUT, "code", guard_params)
    guard_helper.assert_blocked(questions.CPP)
    guard_helper.assert_allowed(questions.SCALA)


@allure.testcase("IEASG-T94")
def disabled_test_out_guard_json_scanner(guard_helper):
    """
    Force the bot to return an invalid JSON object (containing syntax errors) in the output.
    Check if json_scanner repairs the JSON object and returns a valid JSON object.
    """
    guard_params = {
        "enabled": True,
        "redact": True
    }
    guard_helper.setup(GuardType.OUTPUT, "json_scanner", guard_params)
    status_code, response_text = guard_helper.call_chatqa(questions.INVALID_JSON)
    try:
        response = response_text.replace("DONE", "")
        json.loads(response)
    except json.JSONDecodeError:
        pytest.fail(f"Output should be a valid JSON object. Response: {response_text}")


@allure.testcase("IEASG-T98")
def disabled_test_out_guard_malicious_urls(guard_helper):
    """Check if malicious_urls output guard blocks answers that contain malicious urls"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "malicious_urls", guard_params)
    guard_helper.assert_blocked(questions.URLS_IN_RESPONSE)


@allure.testcase("IEASG-T99")
def disabled_test_out_guard_no_refusal(guard_helper):
    """
    Check if the response is rejected when it contains some kind of refusal
    (like 'I'm sorry, I cannot assist you with your prompt')
    """
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "no_refusal", guard_params)
    guard_helper.assert_allowed(questions.REFUSAL_NOT_EXPECTED)
    guard_helper.assert_blocked(questions.REFUSAL_IN_THE_OUTPUT)


@allure.testcase("IEASG-T100")
def disabled_test_out_guard_no_refusal_light(guard_helper):
    """
    Check if the response is rejected when it contains a refusal that is defined in a list of 'substrings'
    (like 'I'm sorry' or 'I can't provide')
    """
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "no_refusal_light", guard_params)
    guard_helper.assert_allowed(questions.REFUSAL_NOT_EXPECTED)
    guard_helper.assert_blocked(questions.REFUSAL_IN_THE_OUTPUT)


@allure.testcase("IEASG-T101")
def disabled_test_out_guard_reading_time(guard_helper):
    """
    Check if reading_time properly calculates the length of the answer generated by LLM.
    If the answer is longer than the maximum reading time, expect the response to be rejected.
    Also, if truncate flag is set to True, expect the response to be truncated.
    """
    guard_params = {
        "enabled": True
        # default reading time is set to 30 seconds
    }
    guard_helper.setup(GuardType.OUTPUT, "reading_time", guard_params)
    guard_helper.assert_blocked(questions.LONG_ANSWER)
    guard_helper.assert_allowed(questions.SHORT_ANSWER)
    guard_params["truncate"] = True
    guard_params["max_time"] = 0.2
    guard_helper.setup(GuardType.OUTPUT, "reading_time", guard_params)
    guard_helper.assert_truncated(questions.LONG_ANSWER)


@allure.testcase("IEASG-T102")
def disabled_test_out_guard_factual_consistency(guard_helper):
    """Check whether LLM does not provide outputs that directly contradict the given inputs or established facts"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "factual_consistency", guard_params)
    guard_helper.assert_blocked(questions.VEGETARIANS)
    guard_helper.assert_allowed(questions.VEGETARIANS_TRUE_STATEMENT)


@allure.testcase("IEASG-T156")
def disabled_test_out_guard_regex(guard_helper):
    """
    Check if scanner detects the predefined regex expressions in output
    and blocks/allows/redacts output accordingly
    """
    guard_params = {
        "enabled": True,
        "redact": True,
        "patterns": [
            r"\d{5}"
        ],
    }
    guard_helper.setup(GuardType.OUTPUT, "regex", guard_params)
    response = guard_helper.assert_redacted(questions.NUMBER_12345_IN_OUTPUT)
    assert "12345" not in response  # Number should be redacted and not visible in output
    response = guard_helper.assert_allowed(questions.NUMBER_991_IN_OUTPUT)
    assert "991" in response

    guard_params["redact"] = False
    guard_helper.setup(GuardType.OUTPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.NUMBER_12345_IN_OUTPUT)

    guard_params["is_blocked"] = True
    guard_params["match_type"] = "fullmatch"
    guard_helper.setup(GuardType.OUTPUT, "regex", guard_params)
    response = guard_helper.assert_allowed(questions.NUMBER_12345_IN_OUTPUT)
    assert "12345" in response


@allure.testcase("IEASG-T157")
def disabled_test_out_guard_sensitive(guard_helper):
    """Check if sensitive data (like email, phone number) in the output is redacted or blocked"""
    guard_params = {
        "enabled": True,
        "entity_types": ["PERSON", "EMAIL_ADDRESS"]
    }
    guard_helper.setup(GuardType.OUTPUT, "sensitive", guard_params)
    guard_helper.assert_blocked(questions.EMAIL_IN_OUTPUT)

    guard_params["redact"] = True
    guard_helper.setup(GuardType.OUTPUT, "sensitive", guard_params)
    _, response = guard_helper.call_chatqa(questions.EMAIL_IN_OUTPUT)
    assert "<PERSON>" in response, "Person in output should be anonymized"
    assert "<EMAIL_ADDRESS>" in response, "Email in output should be anonymized"
    assert "gmail" not in response


@allure.testcase("IEASG-T158")
def disabled_test_out_guard_sentiment(guard_helper):
    """Check if sentiment scanner can properly identify negative sentiment in the answer generated by LLM"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "sentiment", guard_params)
    guard_helper.assert_blocked(questions.NEGATIVE_SENTIMENT_IN_OUTPUT)
    guard_helper.assert_allowed(questions.NEUTRAL_SENTIMENT_IN_OUTPUT)


@allure.testcase("IEASG-T159")
def disabled_test_out_guard_toxicity(guard_helper):
    """Check if output scanner detects toxic, harmful, or offensive content in the answer generated by LLM"""
    guard_params = {
        "enabled": True,
        "threshold": 0.35
    }
    guard_helper.setup(GuardType.OUTPUT, "toxicity", guard_params)
    guard_helper.assert_blocked(questions.THREAT_IN_OUTPUT)
    guard_helper.assert_allowed(questions.NON_TOXIC_OUTPUT)


@allure.testcase("IEASG-T160")
def disabled_test_out_guard_url_reachability(guard_helper):
    """Check if url_reachability scanner can detect unreachable URLs in the output"""
    guard_params = {
        "enabled": True,
        "success_status_codes": [200]
    }
    guard_helper.setup(GuardType.OUTPUT, "url_reachability", guard_params)
    guard_helper.assert_blocked(questions.URL_NOT_REACHABLE)
    guard_helper.assert_allowed(questions.URL_REACHABLE)

    guard_params["success_status_codes"] = [201, 202]
    guard_helper.setup(GuardType.OUTPUT, "url_reachability", guard_params)
    guard_helper.assert_blocked(questions.URL_REACHABLE)
