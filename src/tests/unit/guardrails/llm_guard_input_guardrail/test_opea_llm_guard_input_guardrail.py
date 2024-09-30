import pytest
from unittest.mock import patch
from fastapi import HTTPException
from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail import OPEALLMGuardInputGuardrail
from comps import LLMParamsDoc

@pytest.fixture
def mock_usv_config():
    return {
        "ANONYMIZE_ENABLED": "true",
        "BAN_CODE_ENABLED": "true",
        # Add other necessary configuration settings here
    }

@pytest.fixture
def mock_input_doc():
    return LLMParamsDoc(
        query="This is a test query",
        streaming=False,
        max_new_tokens=50,
        repetition_penalty=1.0,
        temperature=0.7,
        top_k=50,
        top_p=0.9
    )

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_init(mock_input_scanners_config, mock_usv_config):
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["scanner1", "scanner2"]
    guardrail = OPEALLMGuardInputGuardrail(mock_usv_config)
    mock_input_scanners_config.assert_called_once_with(mock_usv_config)
    assert guardrail._scanners == ["scanner1", "scanner2"]

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.input_scanners_configuration_changed')
def test_scan_llm_input_valid(mock_input_scanners_configuration_changed, mock_scan_prompt, mock_input_doc):
    mock_input_scanners_configuration_changed.return_value = False
    mock_scan_prompt.return_value = ("sanitized_query", {"scanner1": True}, {"scanner1": 0.9})

    guardrail = OPEALLMGuardInputGuardrail({})
    guardrail._scanners = ["scanner1"]
    sanitized_query = guardrail.scan_llm_input(mock_input_doc)

    assert sanitized_query == "sanitized_query"

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.input_scanners_configuration_changed')
def test_scan_llm_input_invalid(mock_input_scanners_configuration_changed, mock_scan_prompt, mock_input_doc):
    mock_input_scanners_configuration_changed.return_value = False
    mock_scan_prompt.return_value = ("sanitized_query", {"scanner1": False}, {"scanner1": 0.1})

    guardrail = OPEALLMGuardInputGuardrail({})
    guardrail._scanners = ["scanner1"]

    with pytest.raises(HTTPException) as excinfo:
        guardrail.scan_llm_input(mock_input_doc)

    assert excinfo.value.status_code == 400
    assert "is not valid" in excinfo.value.detail

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.create_enabled_input_scanners')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.input_scanners_configuration_changed')
def test_scan_llm_input_configuration_changed(mock_input_scanners_configuration_changed, mock_create_enabled_input_scanners, mock_input_doc):
    mock_input_scanners_configuration_changed.return_value = True
    mock_create_enabled_input_scanners.return_value = ["scanner1"]

    guardrail = OPEALLMGuardInputGuardrail({})
    guardrail._scanners = []

    guardrail.scan_llm_input(mock_input_doc)

    mock_create_enabled_input_scanners.assert_called_once()
    assert guardrail._scanners == ["scanner1"]