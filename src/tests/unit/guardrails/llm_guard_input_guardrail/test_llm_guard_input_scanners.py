import pytest
from unittest.mock import patch
from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners import InputScannersConfig
from llm_guard.input_scanners import Anonymize, BanSubstrings

@pytest.fixture
def mock_input_scanners_config():
    return {
        "Anonymize": {"enabled": True, "param1": "value1"},
        "BanCode": {"enabled": False},
        "BanSubstrings": {"enabled": True, "param2": "value2"},
        # Add other necessary scanner configurations here
    }

@pytest.fixture
def input_scanners_config_instance(mock_input_scanners_config):
    with patch.object(InputScannersConfig, '_input_scanners_config', mock_input_scanners_config):
        return InputScannersConfig()

def test_create_enabled_input_scanners(input_scanners_config_instance):
    scanners = input_scanners_config_instance.create_enabled_input_scanners()
    assert len(scanners) == 2  # Only Anonymize and BanSubstrings are enabled
    assert isinstance(scanners[0], Anonymize)
    assert isinstance(scanners[1], BanSubstrings)

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners.logger')
def test_create_enabled_input_scanners_with_exception(mock_logger, input_scanners_config_instance):
    with patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners.Anonymize', side_effect=Exception("Test Exception")):
        scanners = input_scanners_config_instance.create_enabled_input_scanners()
        assert len(scanners) == 1  # Only BanSubstrings should be created
        assert isinstance(scanners[0], BanSubstrings)
        mock_logger.exception.assert_called_once_with("An unexpected error occured during creating output scanner Anonymize: Test Exception")