# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from comps.dataprep.utils.opea_dataprep import OPEADataprep
from comps.cores.proto.docarray import DataPrepInput, TextDoc
import base64

@pytest.fixture
def reset_singleton():
    OPEADataprep._instance = None
    yield
    OPEADataprep._instance = None

def test_singleton_behavior(reset_singleton):
    instance1 = OPEADataprep(chunk_size=100, chunk_overlap=10, process_table=True, table_strategy="simple")
    instance2 = OPEADataprep(chunk_size=100, chunk_overlap=10, process_table=True, table_strategy="simple")
    assert instance1 is instance2

def test_initialize_method(reset_singleton):
    dataprep = OPEADataprep(chunk_size=100, chunk_overlap=10, process_table=True, table_strategy="simple")
    assert dataprep.chunk_size == 100
    assert dataprep.chunk_overlap == 10
    assert dataprep.process_table is True
    assert dataprep.table_strategy == "simple"

@patch('opea_dataprep.logging')
async def test_dataprep_no_files_or_links(mock_logging, reset_singleton):
    dataprep = OPEADataprep(chunk_size=100, chunk_overlap=10, process_table=True, table_strategy="simple")
    input_data = DataPrepInput(files=[], links=[])

    with pytest.raises(HTTPException) as exc_info:
        await dataprep.dataprep(input=input_data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Must provide either a file or a string list."

@patch('opea_dataprep.logging')
async def test_dataprep_with_files(mock_logging, reset_singleton):
    dataprep = OPEADataprep(chunk_size=100, chunk_overlap=10, process_table=True, table_strategy="simple")
    file_content = base64.b64encode(b"test content").decode('utf-8')
    input_data = DataPrepInput(files=[MagicMock(data64=file_content)], links=[])

    with patch('opea_dataprep.base64.b64decode', return_value=b"test content") as mock_b64decode:
        result = await dataprep.dataprep(input=input_data)

    mock_logging.info.assert_any_call(f"Dataprep files: {input_data.files}")
    mock_logging.info.assert_any_call(f"Dataprep link list: {input_data.links}")
    mock_b64decode.assert_called_once_with(file_content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextDoc)

# Additional tests for other parts of the `dataprep` method can be added similarly.