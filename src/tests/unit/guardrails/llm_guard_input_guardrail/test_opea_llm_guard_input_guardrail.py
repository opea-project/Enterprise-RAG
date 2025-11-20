# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail import OPEALLMGuardInputGuardrail
from comps import LLMParamsDoc, LLMPromptTemplate
from comps.cores.proto.docarray import LLMGuardInputGuardrailParams, BanSubstringsModel

@pytest.fixture
def mock_usv_config():
    return {
        "BAN_SUBSTRINGS_ENABLED": True,
        "BAN_SUBSTRINGS_SUBSTRINGS": "backdoor,malware,virus",
        "BAN_SUBSTRINGS_MATCH_TYPE": None,
        "BAN_SUBSTRINGS_CASE_SENSITIVE": None,
        "BAN_SUBSTRINGS_REDACT": None,
        "BAN_SUBSTRINGS_CONTAINS_ALL": None
    }

@pytest.fixture
def mock_input_doc():
    ban_substrings_model = BanSubstringsModel(enabled=True, substrings=["backdoor", "malware", "virus"])
    input_guardrail_params = LLMGuardInputGuardrailParams(ban_substrings=ban_substrings_model)

    return LLMParamsDoc(
        messages=[LLMPromptTemplate(role="system", content="You are a helpful assistant"), LLMPromptTemplate(role="user", content="This is a test query")],
        stream=False,
        max_new_tokens=50,
        repetition_penalty=1.0,
        temperature=0.7,
        top_k=50,
        top_p=0.9,
        input_guardrail_params=input_guardrail_params
    )

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_init(mock_input_scanners_config, mock_usv_config):
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanSubstrings"]
    guardrail = OPEALLMGuardInputGuardrail(mock_usv_config)
    mock_input_scanners_config.assert_called_once_with(mock_usv_config)
    assert guardrail._scanners == ["BanSubstrings"]

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
def test_scan_llm_input_valid(mock_scan_prompt, mock_input_scanners_config, mock_input_doc):
    mock_scan_prompt.return_value = ("sanitized_query", {"BanSubstrings": True}, {"BanSubstrings": 0.9})
    mock_input_scanners_config.return_value.changed.return_value = False
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanSubstrings"]

    guardrail = OPEALLMGuardInputGuardrail({})
    doc = guardrail.scan_llm_input(mock_input_doc)

    assert doc == mock_input_doc

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_scan_llm_input_invalid(mock_input_scanners_config, mock_scan_prompt, mock_input_doc):
    mock_scan_prompt.return_value = ("sanitized_query", {"BanSubstrings": False}, {"BanSubstrings": 0.1})
    mock_input_scanners_config.return_value.changed.return_value = False
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanSubstrings"]

    guardrail = OPEALLMGuardInputGuardrail({})

    with pytest.raises(HTTPException) as excinfo:
        guardrail.scan_llm_input(mock_input_doc)

    assert excinfo.value.status_code == 466
    assert "cannot assist" in excinfo.value.detail

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_scan_llm_input_configuration_changed(mock_input_scanners_config, mock_scan_prompt, mock_input_doc):
    mock_scan_prompt.return_value = ("sanitized_query", {"BanSubstrings": True}, {"BanSubstrings": 0.9})
    mock_input_scanners_config.return_value.changed.return_value = False
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanSubstrings"]

    guardrail = OPEALLMGuardInputGuardrail({})

    guardrail.scan_llm_input(mock_input_doc)

    mock_input_scanners_config.return_value.create_enabled_input_scanners.call_count == 2
    assert guardrail._scanners == ["BanSubstrings"]