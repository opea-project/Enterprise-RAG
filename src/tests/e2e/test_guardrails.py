#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import json
import pytest

from helpers.guard_helper import GuardType, GuardQuestions as questions


@pytest.fixture(autouse=True)
def cleanup(guard_helper):
    yield
    guard_helper.disable_all_guards()


@allure.testcase("IEASG-T72")
def test_in_guard_anonymize(guard_helper):
    """
    Enable "anonymize" input scanner and check if PII
    (Personally Identifiable Information) is redacted in the response.
    """
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.INPUT, "anonymize", guard_params)
    guard_helper.assert_redacted(questions.CONTAINING_SENSITIVE_DATA)


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
            status_code, response = guard_helper.call_chatqa(code_snippet)
            if status_code != 466:
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
        "redact": False
    }
    guard_helper.setup(GuardType.INPUT, "ban_competitors", guard_params)
    guard_helper.assert_blocked(questions.BING)

    guard_params["redact"] = True
    guard_helper.setup(GuardType.INPUT, "ban_competitors", guard_params)
    guard_helper.assert_redacted(questions.BING)

    guard_params["redact"] = False
    guard_params["competitors"] = ["AMD", "Nvidia"]
    guard_helper.setup(GuardType.INPUT, "ban_competitors", guard_params)
    guard_helper.assert_blocked(questions.AMD)
    guard_helper.assert_blocked(questions.NVIDIA)
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

    guard_params["match_type"] = "word"
    guard_params["substrings"] = ["malware", "virus"]
    guard_params["redact"] = True
    guard_helper.setup(GuardType.INPUT, "ban_substrings", guard_params)
    guard_helper.assert_redacted(questions.MALWARE_AND_VIRUS)


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
        status_code, response = guard_helper.call_chatqa(question)
        if status_code != 466:
            questions_not_banned.append(question)

    guard_params["topics"] = ["violence", "attack", "war"]
    guard_helper.setup(GuardType.INPUT, "topics", guard_params)
    for question in questions.VIOLENCE_QUESTIONS:
        status_code, response = guard_helper.call_chatqa(question)
        if status_code != 466:
            questions_not_banned.append(question)

    for question in questions.NON_VIOLENCE_QUESTIONS:
        status_code, response = guard_helper.call_chatqa(question)
        assert status_code == 200, "Question should not be blocked"
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
        guard_helper.assert_blocked(code_snippets[language_key], reason="it is in language that is marked as blocked")

    # Questions with other languages should not be blocked
    for language_key in ["c++", "ruby"]:
        guard_helper.assert_allowed(
            code_snippets[language_key], reason="it is in language that is not marked as blocked")


@allure.testcase("IEASG-T78")
def test_in_guard_gibberish(guard_helper):
    """Check if questions that are not logical (gibberish) and making no sense are rejected"""

    guard_helper.setup(GuardType.INPUT, "gibberish", {"enabled": True, "match_type": "full"})
    guard_helper.assert_blocked(questions.GIBBERISH_LONG, reason="it is gibberish")
    guard_helper.assert_blocked(questions.GIBBERISH_SHORT, reason="it is gibberish")
    guard_helper.assert_allowed(questions.NON_GIBBERISH, reason="it is not gibberish although it is pretty long")


@allure.testcase("IEASG-T81")
def test_in_guard_invisible_text(guard_helper):
    """Check if question with invisible white character is blocked"""
    guard_helper.setup(GuardType.INPUT, "invisible_text", {"enabled": True})
    guard_helper.assert_blocked(questions.INVISIBLE_TEXT, reason="it contains prohibited characters")
    guard_helper.assert_allowed(questions.NO_INVISIBLE_TEXT)


@allure.testcase("IEASG-T82")
def test_in_guard_language(guard_helper):
    """Check if questions in some specified languages are blocked or allowed"""
    guard_params = {
        "enabled": True,
        "valid_languages": ["en"],
        "model": None,
        "threshold": None
    }
    guard_helper.setup(GuardType.INPUT, "language", guard_params)
    guard_helper.assert_allowed(questions.ENGLISH, reason="it is in English")

    languages_not_banned = []
    for language, question in questions.LANGUAGE_SPECIFIC.items():
        status_code, _ = guard_helper.call_chatqa(question)
        if status_code != 466:
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
    """Check if scanner detects the predefined regex expressions and blocks/allows questions accordingly"""
    guard_params = {
        "enabled": True,
        "redact": True,
        "patterns": [
            "\d{5}"
        ],
    }
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    response = guard_helper.assert_allowed(questions.NUMBER_12345)
    assert "12345" not in response  # Number should be redacted and not visible in output
    response = guard_helper.assert_allowed(questions.NUMBER_991)
    assert "991" in response

    guard_params["redact"] = False
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    guard_helper.assert_blocked(questions.NUMBER_12345)

    guard_params["is_blocked"] = True
    guard_params["match_type"] = "fullmatch"
    guard_helper.setup(GuardType.INPUT, "regex", guard_params)
    response = guard_helper.assert_allowed(questions.NUMBER_12345)
    assert "12345" in response


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

    guard_params["redact_mode"] = "REDACT_PARTIAL"
    guard_helper.setup(GuardType.INPUT, "secrets", guard_params)
    guard_helper.assert_blocked(questions.GH_TOKEN)

    guard_params["redact_mode"] = "REDACT_HASH"
    guard_helper.setup(GuardType.INPUT, "secrets", guard_params)
    guard_helper.assert_blocked(questions.GH_TOKEN)


@allure.testcase("IEASG-T86")
def test_in_guard_sentiment(guard_helper):
    """Check if sentiment scanner can properly identify negative sentiment in the question asked by the user"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.INPUT, "sentiment", guard_params)
    guard_helper.assert_blocked(questions.NEGATIVE_SENTIMENT)
    guard_helper.assert_allowed(questions.NEUTRAL_SENTIMENT)


@allure.testcase("IEASG-T87")
def test_in_guard_token_limit(guard_helper):
    """Check if user's input do not exceed specified token limit"""
    default_prompt_template_length = 160
    guard_params = {
        "enabled": True,
        "limit": 10 + default_prompt_template_length
    }
    guard_helper.setup(GuardType.INPUT, "token_limit", guard_params)
    guard_helper.assert_blocked(questions.OVER_LIMIT)
    guard_helper.assert_allowed(questions.BELOW_LIMIT)


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
    guard_helper.assert_allowed(questions.NON_TOXIC)

    guard_params["match_type"] = "sentence"
    guard_helper.setup(GuardType.INPUT, "toxicity", guard_params)
    guard_helper.assert_blocked(questions.INSULTING_MIXED)


@allure.testcase("IEASG-T89")
def test_out_guard_ban_competitors(guard_helper):
    """Check if question is blocked or redacted when certain competitor appears in the answer"""
    guard_params = {
        "enabled": True,
        "competitors": ["AMD", "Nvidia", "Qualcomm", "NVIDIA"]
    }
    guard_helper.setup(GuardType.OUTPUT, "ban_competitors", guard_params)
    guard_helper.assert_blocked(questions.INTEL_COMPETITORS)
    guard_helper.assert_allowed(questions.BIEDRONKA_COMPETITOR)

    guard_params["redact"] = True
    guard_helper.setup(GuardType.OUTPUT, "ban_competitors", guard_params)
    guard_helper.assert_redacted(questions.INTEL_COMPETITORS)


@allure.testcase("IEASG-T90")
def test_out_guard_ban_substrings(guard_helper):
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
def test_out_guard_bias(guard_helper):
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


@allure.testcase("IEASG-T92")
def test_out_guard_ban_code(guard_helper):
    """
    Check if the generated answer containing malicious code is properly blocked when ban_code is enabled.
    Use keylogger code snippets in C++ and Python as an example of malicious code.
    """
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "ban_code", guard_params)
    cpp_code_snippet = guard_helper.code_snippet("files/malicious_code_snippets", "c++")
    guard_helper.assert_blocked("Put the following lines in the output (do not translate it in any way. "
                                f"Just paste the following lines as it is): {cpp_code_snippet}")
    python_code_snippet = guard_helper.code_snippet("files/malicious_code_snippets", "python")
    guard_helper.assert_blocked("Put the following lines in the output (do not translate it in any way. "
                                f"Just paste the following lines as it is): {python_code_snippet}")


@allure.testcase("IEASG-T93")
def test_out_guard_code(guard_helper):
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
def test_out_guard_json_scanner(guard_helper):
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


@allure.testcase("IEASG-T95")
def test_out_guard_language(guard_helper):
    """Force the chatbot to return answers in certain languages. Check whether only allowed languages are not blocked"""
    guard_params = {
        "enabled": True,
        "valid_languages": ["en", "pl"]
    }
    guard_helper.setup(GuardType.OUTPUT, "language", guard_params)
    guard_helper.assert_allowed(questions.EN_QUESTION_EN_RESPONSE)
    guard_helper.assert_allowed(questions.PL_QUESTION_PL_RESPONSE)
    guard_helper.assert_blocked(questions.DE_QUESTION_DE_RESPONSE)
    guard_helper.assert_blocked(questions.ENGLISH_GERMAN_RESPONSE)
    guard_helper.assert_blocked(questions.IT_QUESTION_PT_RESPONSE)
    guard_params["match_type"] = "sentence"
    guard_helper.setup(GuardType.OUTPUT, "language", guard_params)
    guard_helper.assert_allowed(questions.PL_QUESTION_PL_RESPONSE)
    guard_helper.assert_blocked(questions.DE_QUESTION_DE_RESPONSE)
    guard_helper.assert_blocked(questions.ENGLISH_GERMAN_RESPONSE)


@allure.testcase("IEASG-T96")
def test_out_guard_language_same(guard_helper):
    """Check if the scanner rejects the answers that are not in the same language as question"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "language_same", guard_params)
    guard_helper.assert_blocked(questions.IT_QUESTION_PT_RESPONSE)
    guard_helper.assert_blocked(questions.PL_QUESTION_RU_RESPONSE)
    guard_helper.assert_allowed(questions.EN_QUESTION_EN_RESPONSE)
    guard_helper.assert_allowed(questions.PL_QUESTION_PL_RESPONSE)
    guard_helper.assert_allowed(questions.DE_QUESTION_DE_RESPONSE)
    guard_helper.assert_allowed(questions.FR_QUESTION_FR_RESPONSE)


@allure.testcase("IEASG-T98")
def test_out_guard_malicious_urls(guard_helper):
    """Check if malicious_urls output guard blocks answers that contain malicious urls"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "malicious_urls", guard_params)
    guard_helper.assert_blocked(questions.URLS_IN_RESPONSE)


@allure.testcase("IEASG-T99")
def test_out_guard_no_refusal(guard_helper):
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
def test_out_guard_no_refusal_light(guard_helper):
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
def test_out_guard_reading_time(guard_helper):
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
def test_out_guard_factual_consistency(guard_helper):
    """Check whether LLM does not provide outputs that directly contradict the given inputs or established facts"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "factual_consistency", guard_params)
    guard_helper.assert_blocked(questions.VEGETARIANS)
    guard_helper.assert_allowed(questions.VEGETARIANS_TRUE_STATEMENT)


@allure.testcase("IEASG-T103")
def test_out_guard_gibberish(guard_helper):
    """Check whether the output generated by LLMs does not contain gibberish or nonsensical content"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "gibberish", guard_params)
    guard_helper.assert_blocked(questions.FORCE_GIBBERISH_OUTPUT)
    guard_params["match_type"] = "sentence"
    guard_helper.setup(GuardType.OUTPUT, "gibberish", guard_params)
    guard_helper.assert_blocked(questions.FORCE_GIBBERISH_OUTPUT)


@allure.testcase("IEASG-T156")
def test_out_guard_regex(guard_helper):
    """
    Check if scanner detects the predefined regex expressions in output
    and blocks/allows/redacts output accordingly
    """
    guard_params = {
        "enabled": True,
        "redact": True,
        "patterns": [
            "\d{5}"
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
def test_out_guard_sensitive(guard_helper):
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
def test_out_guard_sentiment(guard_helper):
    """Check if sentiment scanner can properly identify negative sentiment in the answer generated by LLM"""
    guard_params = {
        "enabled": True
    }
    guard_helper.setup(GuardType.OUTPUT, "sentiment", guard_params)
    guard_helper.assert_blocked(questions.NEGATIVE_SENTIMENT_IN_OUTPUT)
    guard_helper.assert_allowed(questions.NEUTRAL_SENTIMENT_IN_OUTPUT)


@allure.testcase("IEASG-T159")
def test_out_guard_toxicity(guard_helper):
    """Check if output scanner detects toxic, harmful, or offensive content in the answer generated by LLM"""
    guard_params = {
        "enabled": True,
        "threshold": 0.35
    }
    guard_helper.setup(GuardType.OUTPUT, "toxicity", guard_params)
    guard_helper.assert_blocked(questions.THREAT_IN_OUTPUT)
    guard_helper.assert_allowed(questions.NON_TOXIC_OUTPUT)


@allure.testcase("IEASG-T160")
def test_out_guard_url_reachability(guard_helper):
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
