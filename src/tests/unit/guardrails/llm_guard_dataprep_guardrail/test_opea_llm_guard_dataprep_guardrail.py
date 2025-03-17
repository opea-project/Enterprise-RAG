# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail import OPEALLMGuardDataprepGuardrail
from comps import TextDoc, TextDocList

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
def mock_dataprep_doc():
    list_of_docs=[TextDoc(text="abcd"), TextDoc(text="1234")]

    return TextDocList(
        docs=list_of_docs,
    )

@patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail.DataprepScannersConfig')
def test_init(mock_dataprep_scanners_config, mock_usv_config):
    mock_dataprep_scanners_config.return_value.create_enabled_dataprep_scanners.return_value = ["BanCode", "BanCompetitors", "BanSubstrings"]
    guardrail = OPEALLMGuardDataprepGuardrail(mock_usv_config)
    mock_dataprep_scanners_config.assert_called_once_with(mock_usv_config)
    assert guardrail._scanners == ["BanCode", "BanCompetitors", "BanSubstrings"]

@patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail.DataprepScannersConfig')
@patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail.OPEALLMGuardDataprepGuardrail.scan_dataprep_docs')
def test_scan_llm_dataprep_valid(mock_scan_dataprep_docs, mock_dataprep_scanners_config, mock_dataprep_doc):
    mock_scan_dataprep_docs.return_value = TextDocList(docs=[TextDoc(text='abcd'), TextDoc(text="1234")])
    mock_dataprep_scanners_config.return_value.changed.return_value = False
    mock_dataprep_scanners_config.return_value.create_enabled_dataprep_scanners.return_value = ["BanCode"]

    guardrail = OPEALLMGuardDataprepGuardrail({})
    doc = guardrail.scan_dataprep_docs(mock_dataprep_doc)

    assert doc == mock_dataprep_doc


@patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail.scan_prompt')
@patch('comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail.DataprepScannersConfig')
def test_scan_llm_dataprep_invalid(mock_dataprep_scanners_config, mock_scan_prompt, mock_dataprep_doc):
    mock_scan_prompt.return_value = ("sanitized_doc", {"BanCode": False}, {"BanCode": 0.1})
    mock_dataprep_scanners_config.return_value.changed.return_value = False
    mock_dataprep_scanners_config.return_value.create_enabled_dataprep_scanners.return_value = ["BanCode"]

    guardrail = OPEALLMGuardDataprepGuardrail({})

    with pytest.raises(HTTPException) as excinfo:
        guardrail.scan_dataprep_docs(mock_dataprep_doc)

    assert excinfo.value.status_code == 466
    assert "cannot ingest" in excinfo.value.detail
