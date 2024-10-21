# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_scanners import OutputScannersConfig
from llm_guard.output_scanners import JSON, BanSubstrings

@pytest.fixture
def mock_output_scanners_config():
    return {
        "JSON_SCANNER_ENABLED": "true",
        "REGEX_ENABLED": "false",
        "REGEX_PATTERNS": "Bearer [A-Za-z0-9-._~+/]+",
        "BAN_SUBSTRINGS_ENABLED": "true",
        "BAN_SUBSTRINGS_SUBSTRINGS": "backdoor,malware,virus"
        # Add other necessary scanner configurations here
    }

@pytest.fixture
def output_scanners_config_instance(mock_output_scanners_config):
    return OutputScannersConfig(mock_output_scanners_config)

def test_create_enabled_output_scanners(output_scanners_config_instance):
    scanners = output_scanners_config_instance.create_enabled_output_scanners()
    assert len(scanners) == 2  # Only JSONScanner and BanSubstrings are enabled
    assert isinstance(scanners[0], BanSubstrings)
    assert isinstance(scanners[1], JSON)

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_scanners.logger')
def test_create_enabled_output_scanners_with_exception(mock_logger, output_scanners_config_instance):
    with patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_scanners.JSON', side_effect=Exception("Test Exception")):
        scanners = output_scanners_config_instance.create_enabled_output_scanners()
        assert len(scanners) == 1  # Only BanSubstrings should be created
        assert isinstance(scanners[0], BanSubstrings)
        mock_logger.exception.assert_called_once_with("An unexpected error occured during creating output scanner json_scanner: Test Exception")

def test_validate_value(output_scanners_config_instance):
    assert output_scanners_config_instance._validate_value("true") is True
    assert output_scanners_config_instance._validate_value("false") is False
    assert output_scanners_config_instance._validate_value("123") == 123
    assert output_scanners_config_instance._validate_value("some_string") == "some_string"

def test_get_json_scanner_config_from_env(output_scanners_config_instance):
    config = output_scanners_config_instance._get_json_scanner_config_from_env({"JSON_SCANNER_ENABLED": "true"})
    assert config == {"json_scanner": {"enabled": True}}

def test_get_regex_config_from_env(output_scanners_config_instance):
    config = output_scanners_config_instance._get_regex_config_from_env({"REGEX_ENABLED": "true"})
    assert config == {"regex": {"enabled": True}}

def test_get_ban_substrings_config_from_env(output_scanners_config_instance):
    config = output_scanners_config_instance._get_ban_substrings_config_from_env({"BAN_SUBSTRINGS_ENABLED": "true"})
    assert config == {"ban_substrings": {"enabled": True}}

def test_changed(output_scanners_config_instance):
    current_config = {"id": "blah", "regex": {"id": "blah", "enabled": True}}
    new_current_config = {"id": "blah", "regex": {"id": "blah", "enabled": True}}
    output_scanners_config_instance._output_scanners_config.clear()
    assert output_scanners_config_instance.changed(current_config) is True
    assert output_scanners_config_instance._output_scanners_config == {"regex": {"enabled": True}}
    assert output_scanners_config_instance.changed(new_current_config) is False