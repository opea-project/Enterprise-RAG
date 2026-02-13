# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_scanners import DataprepScannersConfig
from llm_guard.input_scanners import BanSubstrings, InvisibleText

@pytest.fixture
def mock_dataprep_scanners_config():
    return {
        "BAN_SUBSTRINGS_ENABLED": "true",
        "BAN_SUBSTRINGS_SUBSTRINGS": "backdoor,malware,virus",
        "BAN_TOPICS_ENABLED": "false",
        "CODE_ENABLED": "false",
        "INVISIBLE_TEXT_ENABLED": "true",
        "LANGUAGE_ENABLED": "false",
        "PROMPT_INJECTION_ENABLED": "false",
        "REGEX_ENABLED": "false",
        "REGEX_PATTERNS": "Bearer [A-Za-z0-9-._~+/]+",
        "SECRETS_ENABLED": "false",
        "SENTIMENT_ENABLED": "false",
        "TOKEN_LIMIT_ENABLED": "false",
        "TOXICITY_ENABLED": "false"
    }

@pytest.fixture
def dataprep_scanners_config_instance(mock_dataprep_scanners_config):
    return DataprepScannersConfig(mock_dataprep_scanners_config)

def test_create_enabled_dataprep_scanners(dataprep_scanners_config_instance):
    scanners = dataprep_scanners_config_instance.create_enabled_dataprep_scanners()
    assert len(scanners) == 2  # Only InvisibleText and BanSubstrings are enabled
    assert isinstance(scanners[0], BanSubstrings)
    assert isinstance(scanners[1], InvisibleText)

@patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_scanners.logger')
def test_create_enabled_dataprep_scanners_with_exception(mock_logger, dataprep_scanners_config_instance):
    with patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_scanners.InvisibleText', side_effect=Exception("Test Exception")):
        with pytest.raises(Exception) as e:
            dataprep_scanners_config_instance.create_enabled_dataprep_scanners()
            assert "Some scanners failed to be created due to validation or unexpected errors. The details: {'invisible_text': 'An unexpected error occured during creating dataprep scanner invisible_text: Test Exception'}" in e.value.detail
        scanners = {k: v for k, v in dataprep_scanners_config_instance._dataprep_scanners_config.items() if v.get("enabled")}
        assert len(scanners.keys()) == 1  # Only BanSubstrings should be created
        assert list(scanners.keys())[0] == "ban_substrings"

def test_validate_value(dataprep_scanners_config_instance):
    assert dataprep_scanners_config_instance._validate_value("true") is True
    assert dataprep_scanners_config_instance._validate_value("false") is False
    assert dataprep_scanners_config_instance._validate_value("123") == 123
    assert dataprep_scanners_config_instance._validate_value("some_string") == "some_string"

def test_get_ban_substrings_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_ban_substrings_config_from_env({"BAN_SUBSTRINGS_ENABLED": "true"})
    assert config == {"ban_substrings": {"enabled": True}}

def test_get_ban_topics_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_ban_topics_config_from_env({"BAN_TOPICS_ENABLED": "false"})
    assert config == {"ban_topics": {"enabled": False}}

def test_get_code_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_code_config_from_env({"CODE_ENABLED": "false"})
    assert config == {"code": {"enabled": False}}

def test_get_invisible_text_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_invisible_text_config_from_env({"INVISIBLE_TEXT_ENABLED": "true"})
    assert config == {"invisible_text": {"enabled": True}}

def test_get_prompt_injection_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_prompt_injection_config_from_env({"PROMPT_INJECTION_ENABLED": "false"})
    assert config == {"prompt_injection": {"enabled": False}}

def test_get_regex_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_regex_config_from_env({"REGEX_ENABLED": "true", "REGEX_PATTERNS": "Bearer [A-Za-z0-9-._~+/]+"})
    assert config == {"regex": {"enabled": True, "patterns": "Bearer [A-Za-z0-9-._~+/]+"}}

def test_get_secrets_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_secrets_config_from_env({"SECRETS_ENABLED": "false"})
    assert config == {"secrets": {"enabled": False}}

def test_get_sentiment_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_sentiment_config_from_env({"SENTIMENT_ENABLED": "false"})
    assert config == {"sentiment": {"enabled": False}}

def test_get_token_limit_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_token_limit_config_from_env({"TOKEN_LIMIT_ENABLED": "false"})
    assert config == {"token_limit": {"enabled": False}}

def test_get_toxicity_config_from_env(dataprep_scanners_config_instance):
    config = dataprep_scanners_config_instance._get_toxicity_config_from_env({"TOXICITY_ENABLED": "false"})
    assert config == {"toxicity": {"enabled": False}}

def test_changed(dataprep_scanners_config_instance):
    current_config = {"id": "blah", "invisible_text": {"id": "blah", "enabled": True}}
    new_current_config = {"id": "blah", "invisible_text": {"id": "blah", "enabled": True}}
    dataprep_scanners_config_instance._dataprep_scanners_config.clear()
    assert dataprep_scanners_config_instance.changed(current_config) is True
    assert dataprep_scanners_config_instance._dataprep_scanners_config == {"invisible_text": {"enabled": True}}
    assert dataprep_scanners_config_instance.changed(new_current_config) is False