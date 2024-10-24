# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail import OPEALLMGuardInputGuardrail
from comps import LLMParamsDoc
from comps.cores.proto.docarray import LLMGuardInputGuardrailParams, BanCodeModel

@pytest.fixture
def mock_usv_config():
    return {
        "BAN_CODE_ENABLED": True,
        "BAN_CODE_USE_ONNX": True,
        "BAN_CODE_MODEL": None,
        "BAN_CODE_THRESHOLD": None,
        "BAN_COMPETITORS_ENABLED": False,
        "BAN_COMPETITORS_USE_ONNX": True,
        "BAN_COMPETITORS_COMPETITORS": "Competitor1,Competitor2,Competitor3",
        "BAN_COMPETITORS_THRESHOLD": False,
        "BAN_COMPETITORS_REDACT": False,
        "BAN_COMPETITORS_MODEL": False,
        "BAN_SUBSTRINGS_ENABLED": True,
        "BAN_SUBSTRINGS_SUBSTRINGS": "backdoor,malware,virus",
        "BAN_SUBSTRINGS_MATCH_TYPE": None,
        "BAN_SUBSTRINGS_CASE_SENSITIVE": None,
        "BAN_SUBSTRINGS_REDACT": None,
        "BAN_SUBSTRINGS_CONTAINS_ALL": None
    }

@pytest.fixture
def mock_input_doc():
    ban_code_model = BanCodeModel(enabled=True, use_onnx=True, model=None, threshold=None)
    input_guardrail_params = LLMGuardInputGuardrailParams(ban_code=ban_code_model)

    return LLMParamsDoc(
        query="This is a test query",
        streaming=False,
        max_new_tokens=50,
        repetition_penalty=1.0,
        temperature=0.7,
        top_k=50,
        top_p=0.9,
        input_guardrail_params=input_guardrail_params
    )

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_init(mock_input_scanners_config, mock_usv_config):
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanCode", "BanCompetitors", "BanSubstrings"]
    guardrail = OPEALLMGuardInputGuardrail(mock_usv_config)
    mock_input_scanners_config.assert_called_once_with(mock_usv_config)
    assert guardrail._scanners == ["BanCode", "BanCompetitors", "BanSubstrings"]

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
def test_scan_llm_input_valid(mock_scan_prompt, mock_input_scanners_config, mock_input_doc):
    mock_scan_prompt.return_value = ("sanitized_query", {"BanCode": True}, {"BanCode": 0.9})
    mock_input_scanners_config.return_value.changed.return_value = False
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanCode"]

    guardrail = OPEALLMGuardInputGuardrail({})
    doc = guardrail.scan_llm_input(mock_input_doc)

    assert doc == mock_input_doc

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_scan_llm_input_invalid(mock_input_scanners_config, mock_scan_prompt, mock_input_doc):
    mock_scan_prompt.return_value = ("sanitized_query", {"BanCode": False}, {"BanCode": 0.1})
    mock_input_scanners_config.return_value.changed.return_value = False
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanCode"]

    guardrail = OPEALLMGuardInputGuardrail({})

    with pytest.raises(HTTPException) as excinfo:
        guardrail.scan_llm_input(mock_input_doc)

    assert excinfo.value.status_code == 466
    assert "cannot assist" in excinfo.value.detail

@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail.InputScannersConfig')
def test_scan_llm_input_configuration_changed(mock_input_scanners_config, mock_scan_prompt, mock_input_doc):
    mock_scan_prompt.return_value = ("sanitized_query", {"BanCode": True}, {"BanCode": 0.9})
    mock_input_scanners_config.return_value.changed.return_value = False
    mock_input_scanners_config.return_value.create_enabled_input_scanners.return_value = ["BanCode"]

    guardrail = OPEALLMGuardInputGuardrail({})

    guardrail.scan_llm_input(mock_input_doc)

    mock_input_scanners_config.return_value.create_enabled_input_scanners.call_count == 2
    assert guardrail._scanners == ["BanCode"]