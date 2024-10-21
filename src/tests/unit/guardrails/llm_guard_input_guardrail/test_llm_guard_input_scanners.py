# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners import InputScannersConfig
from llm_guard.input_scanners import BanSubstrings, InvisibleText

@pytest.fixture
def mock_input_scanners_config():
    return {
        "INVISIBLE_TEXT_ENABLED": "true",
        "REGEX_ENABLED": "false",
        "REGEX_PATTERNS": "Bearer [A-Za-z0-9-._~+/]+",
        "BAN_SUBSTRINGS_ENABLED": "true",
        "BAN_SUBSTRINGS_SUBSTRINGS": "backdoor,malware,virus"
        # Add other necessary scanner configurations here
    }

@pytest.fixture
def input_scanners_config_instance(mock_input_scanners_config):
    return InputScannersConfig(mock_input_scanners_config)

def test_create_enabled_input_scanners(input_scanners_config_instance):
    scanners = input_scanners_config_instance.create_enabled_input_scanners()
    assert len(scanners) == 2  # Only InvisibleText and BanSubstrings are enabled
    assert isinstance(scanners[0], BanSubstrings)
    assert isinstance(scanners[1], InvisibleText)

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners.logger')
def test_create_enabled_input_scanners_with_exception(mock_logger, input_scanners_config_instance):
    with patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners.InvisibleText', side_effect=Exception("Test Exception")):
        scanners = input_scanners_config_instance.create_enabled_input_scanners()
        assert len(scanners) == 1  # Only BanSubstrings should be created
        assert isinstance(scanners[0], BanSubstrings)
        mock_logger.exception.assert_called_once_with("An unexpected error occured during creating input scanner invisible_text: Test Exception")

def test_validate_value(input_scanners_config_instance):
    assert input_scanners_config_instance._validate_value("true") is True
    assert input_scanners_config_instance._validate_value("false") is False
    assert input_scanners_config_instance._validate_value("123") == 123
    assert input_scanners_config_instance._validate_value("some_string") == "some_string"

def test_get_invisible_text_config_from_env(input_scanners_config_instance):
    config = input_scanners_config_instance._get_invisible_text_config_from_env({"INVISIBLE_TEXT_ENABLED": "true"})
    assert config == {"invisible_text": {"enabled": True}}

def test_get_regex_config_from_env(input_scanners_config_instance):
    config = input_scanners_config_instance._get_regex_config_from_env({"REGEX_ENABLED": "true"})
    assert config == {"regex": {"enabled": True}}

def test_get_ban_substrings_config_from_env(input_scanners_config_instance):
    config = input_scanners_config_instance._get_ban_substrings_config_from_env({"BAN_SUBSTRINGS_ENABLED": "true"})
    assert config == {"ban_substrings": {"enabled": True}}

def test_changed(input_scanners_config_instance):
    current_config = {"id": "blah", "invisible_text": {"id": "blah", "enabled": True}}
    new_current_config = {"id": "blah", "invisible_text": {"id": "blah", "enabled": True}}
    input_scanners_config_instance._input_scanners_config.clear()
    assert input_scanners_config_instance.changed(current_config) is True
    assert input_scanners_config_instance._input_scanners_config == {"invisible_text": {"enabled": True}}
    assert input_scanners_config_instance.changed(new_current_config) is False