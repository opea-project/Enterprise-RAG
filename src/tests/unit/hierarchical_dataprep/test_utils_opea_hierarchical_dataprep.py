# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from comps.hierarchical_dataprep.utils.opea_hierarchical_dataprep import OPEAHierarchicalDataPrep
from comps import TextDoc

@pytest.fixture
def reset_singleton():
    OPEAHierarchicalDataPrep._instance = None
    yield
    OPEAHierarchicalDataPrep._instance = None

def test_singleton_behavior(reset_singleton):
    instance1 = OPEAHierarchicalDataPrep(chunk_size=100, chunk_overlap=10, vllm_endpoint="http://localhost:8008", summary_model="summary-model", max_new_tokens=50)
    instance2 = OPEAHierarchicalDataPrep(chunk_size=100, chunk_overlap=10, vllm_endpoint="http://localhost:8008", summary_model="summary-model", max_new_tokens=50)
    assert instance1 is instance2

def test_initialize_method(reset_singleton):
    dataprep = OPEAHierarchicalDataPrep(chunk_size=100, chunk_overlap=10, vllm_endpoint="http://localhost:8008", summary_model="summary-model", max_new_tokens=50)
    assert dataprep.chunk_size == 100
    assert dataprep.chunk_overlap == 10
    assert dataprep.vllm_endpoint == "http://localhost:8008"
    assert dataprep.summary_model == "summary-model"
    assert dataprep.max_new_tokens == 50

def test_dataprep_no_files(reset_singleton):
    hierarchical_dataprep = OPEAHierarchicalDataPrep(chunk_size=100, chunk_overlap=10, vllm_endpoint="http://localhost:8008", summary_model="summary-model", max_new_tokens=50)
    input_data = []

    with pytest.raises(ValueError) as context:
        hierarchical_dataprep.hierarchical_dataprep(files=input_data)

    assert str(context.value) == "No files passed for hierarchical data preparation."

def test_dataprep_with_files(reset_singleton):
    hierarchical_dataprep = OPEAHierarchicalDataPrep(chunk_size=100, chunk_overlap=10, vllm_endpoint="http://localhost:8008", summary_model="summary-model", max_new_tokens=50)

    mock_file = MagicMock(spec=UploadFile)
    mock_summary_doc = MagicMock(TextDoc)
    mock_chunk_doc = MagicMock(TextDoc)
    summary_list = [mock_summary_doc]
    chunk_list = [mock_chunk_doc]
    
    with patch("comps.hierarchical_dataprep.utils.opea_hierarchical_dataprep.HierarchicalIndexer.parse_files", return_value=(summary_list, chunk_list)):
        result = hierarchical_dataprep.hierarchical_dataprep(files=[mock_file])

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], TextDoc)
    assert isinstance(result[1], TextDoc)

@patch("comps.hierarchical_dataprep.utils.opea_hierarchical_dataprep.HierarchicalIndexer.parse_files")
def test_dataprep_with_files_exception(mock_parse_files, reset_singleton):
    hierarchical_dataprep = OPEAHierarchicalDataPrep(chunk_size=100, chunk_overlap=10, vllm_endpoint="http://localhost:8008", summary_model="summary-model", max_new_tokens=50)

    mock_file = MagicMock(spec=UploadFile)
    mock_parse_files.side_effect = Exception("Parsing Error")

    with pytest.raises(ValueError) as context:
        hierarchical_dataprep.hierarchical_dataprep(files=[mock_file])
    
    assert str(context.value) == "Failed to parse file: Exception Parsing Error"