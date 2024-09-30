import pytest
from unittest.mock import patch
from comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail import OutputScannersConfig
from llm_guard.output_scanners import Anonymize, BanSubstrings

@pytest.fixture
def mock_output_scanners_config():
    return {
        "Anonymize": {"enabled": True, "param1": "value1"},
        "BanCode": {"enabled": False},
        "BanSubstrings": {"enabled": True, "param2": "value2"},
        # Add other necessary scanner configurations here
    }

@pytest.fixture
def output_scanners_config_instance(mock_output_scanners_config):
    with patch.object(OutputScannersConfig, '_output_scanners_config', mock_output_scanners_config):
        return OutputScannersConfig()

def test_create_enabled_output_scanners(output_scanners_config_instance):
    scanners = output_scanners_config_instance.create_enabled_output_scanners()
    assert len(scanners) == 2  # Only Anonymize and BanSubstrings are enabled
    assert isinstance(scanners[0], Anonymize)
    assert isinstance(scanners[1], BanSubstrings)

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.logger')
def test_create_enabled_output_scanners_with_exception(mock_logger, output_scanners_config_instance):
    with patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.Anonymize', side_effect=Exception("Test Exception")):
        scanners = output_scanners_config_instance.create_enabled_output_scanners()
        assert len(scanners) == 1  # Only BanSubstrings should be created
        assert isinstance(scanners[0], BanSubstrings)
        mock_logger.exception.assert_called_once_with("An unexpected error occured during creating output scanner Anonymize: Test Exception")