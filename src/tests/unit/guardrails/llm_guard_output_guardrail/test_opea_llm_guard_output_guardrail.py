# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail import OPEALLMGuardOutputGuardrail
from comps import GeneratedDoc
from comps.cores.proto.docarray import LLMGuardOutputGuardrailParams, BanSubstringsModel

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
def mock_output_doc():
    ban_substrings_model = BanSubstringsModel(enabled=True, substrings=["backdoor", "malware", "virus"])
    output_guardrail_params = LLMGuardOutputGuardrailParams(ban_substrings=ban_substrings_model)
    return GeneratedDoc(
        text="This is a test output",
        prompt="This is a test prompt",
        output_guardrail_params=output_guardrail_params
    )

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.OutputScannersConfig')
def test_init(mock_output_scanners_config, mock_usv_config):
    mock_output_scanners_config.return_value.create_enabled_output_scanners.return_value = ["BanSubstrings"]
    guardrail = OPEALLMGuardOutputGuardrail(mock_usv_config)
    mock_output_scanners_config.assert_called_once_with(mock_usv_config)
    assert guardrail._scanners == ["BanSubstrings"]

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.OutputScannersConfig')
@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.scan_output')
def test_scan_llm_output_valid(mock_scan_output, mock_output_scanners_config, mock_output_doc):
    mock_scan_output.return_value = ("This is a test output", {"BanSubstrings": True}, {"BanSubstrings": 0.9})
    mock_output_scanners_config.return_value.changed.return_value = False
    mock_output_scanners_config.return_value.create_enabled_output_scanners.return_value = ["BanSubstrings"]

    guardrail = OPEALLMGuardOutputGuardrail({})
    santized_output = guardrail.scan_llm_output(mock_output_doc)

    assert santized_output == mock_output_doc.text

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.OutputScannersConfig')
@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.scan_output')
def test_scan_llm_output_invalid(mock_scan_output, mock_output_scanners_config, mock_output_doc):
    mock_scan_output.return_value = ("This is a test output", {"BanSubstrings": False}, {"BanSubstrings": 0.1})
    mock_output_scanners_config.return_value.changed.return_value = False
    mock_output_scanners_config.return_value.create_enabled_output_scanners.return_value = ["BanSubstrings"]

    guardrail = OPEALLMGuardOutputGuardrail({})

    with pytest.raises(HTTPException) as excinfo:
        guardrail.scan_llm_output(mock_output_doc)

    assert excinfo.value.status_code == 466
    assert "is not valid" in excinfo.value.detail

@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.OutputScannersConfig')
@patch('comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail.scan_output')
def test_scan_llm_output_configuration_changed(mock_scan_output, mock_output_scanners_config, mock_output_doc):
    mock_scan_output.return_value = ("This is a test output", {"BanSubstrings": True}, {"BanSubstrings": 0.9})
    mock_output_scanners_config.return_value.changed.return_value = True
    mock_output_scanners_config.return_value.create_enabled_output_scanners.return_value = ["BanSubstrings"]

    guardrail = OPEALLMGuardOutputGuardrail({})

    guardrail.scan_llm_output(mock_output_doc)

    mock_output_scanners_config.return_value.create_enabled_output_scanners.call_count == 2
    assert guardrail._scanners == ["BanSubstrings"]