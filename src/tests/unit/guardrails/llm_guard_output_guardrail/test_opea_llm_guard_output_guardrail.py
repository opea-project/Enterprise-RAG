import pytest
from unittest.mock import patch
from fastapi import HTTPException
from comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail import OPEALLMGuardOutputGuardrail
from comps import GeneratedDoc

@pytest.fixture
def mock_usv_config():
    return {
        "ANONYMIZE_ENABLED": "true",
        "BAN_CODE_ENABLED": "true",
        # Add other necessary configuration settings here
    }

@pytest.fixture
def mock_output_doc():
    return GeneratedDoc(
        text="This is a test output",
        prompt="This is a test prompt"
    )

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.OutputScannersConfig')
def test_init(mock_output_scanners_config, mock_usv_config):
    mock_output_scanners_config.return_value.create_enabled_output_scanners.return_value = ["scanner1", "scanner2"]
    guardrail = OPEALLMGuardOutputGuardrail(mock_usv_config)
    mock_output_scanners_config.assert_called_once_with(mock_usv_config)
    assert guardrail._scanners == ["scanner1", "scanner2"]

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.scan_output')
@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.output_scanners_configuration_changed')
def test_scan_llm_output_valid(mock_output_scanners_configuration_changed, mock_scan_output, mock_output_doc):
    mock_output_scanners_configuration_changed.return_value = False
    mock_scan_output.return_value = ("sanitized_output", {"scanner1": True}, {"scanner1": 0.9})

    guardrail = OPEALLMGuardOutputGuardrail({})
    guardrail._scanners = ["scanner1"]
    sanitized_output = guardrail.scan_llm_output(mock_output_doc)

    assert sanitized_output == "sanitized_output"

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.scan_output')
@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.output_scanners_configuration_changed')
def test_scan_llm_output_invalid(mock_output_scanners_configuration_changed, mock_scan_output, mock_output_doc):
    mock_output_scanners_configuration_changed.return_value = False
    mock_scan_output.return_value = ("sanitized_output", {"scanner1": False}, {"scanner1": 0.1})

    guardrail = OPEALLMGuardOutputGuardrail({})
    guardrail._scanners = ["scanner1"]

    with pytest.raises(HTTPException) as excinfo:
        guardrail.scan_llm_output(mock_output_doc)

    assert excinfo.value.status_code == 400
    assert "is not valid" in excinfo.value.detail

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.create_enabled_output_scanners')
@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.output_scanners_configuration_changed')
def test_scan_llm_output_configuration_changed(mock_output_scanners_configuration_changed, mock_create_enabled_output_scanners, mock_output_doc):
    mock_output_scanners_configuration_changed.return_value = True
    mock_create_enabled_output_scanners.return_value = ["scanner1"]

    guardrail = OPEALLMGuardOutputGuardrail({})
    guardrail._scanners = []

    guardrail.scan_llm_output(mock_output_doc)

    mock_create_enabled_output_scanners.assert_called_once()
    assert guardrail._scanners == ["scanner1"]