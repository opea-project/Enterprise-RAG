# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest import mock
from comps.dataprep.utils.file_parser import FileParser
import pytest

@pytest.fixture
def mock_fileparser():
    val = [ {'file_type': 'xyz', 'loader_file_name': 'load_xyz', 'loader_class': 'LoadXYZ', 'mime_type': 'application/test'} ]
    with mock.patch('comps.dataprep.utils.file_parser.FileParser.default_mappings', return_value=val):
        yield

@pytest.fixture
def mock_mimetype():
    val = 'application/test'
    with mock.patch('comps.dataprep.utils.file_parser.FileParser.get_mime_type', return_value=val):
        yield

@pytest.fixture
def mock_mimetype_missmatch():
    val = 'application/non_existend'
    with mock.patch('comps.dataprep.utils.file_parser.FileParser.get_mime_type', return_value=val):
        yield

def test_not_supported_extension(mock_fileparser, mock_mimetype):
    file_name = 'test_dataprep.foo'
    with pytest.raises(ValueError):
        FileParser(file_name)

def test_not_supported_mime_type(mock_mimetype):
    file_name = 'test_dataprep.xyz'
    with pytest.raises(ValueError):
        FileParser(file_name)

def test_supported_mappings(mock_fileparser, mock_mimetype):
    file_name = 'test_dataprep.xyz'
    fp = FileParser(file_name)
    assert fp.supported_types() == ['xyz']

def test_supported_mime_types(mock_fileparser, mock_mimetype):
    file_name = 'test_dataprep.xyz'
    fp = FileParser(file_name)
    assert fp.supported_mime_types() == ['application/test']

def test_file_type_and_mime_type_missmatch(mock_fileparser, mock_mimetype_missmatch):
    file_name = 'test_dataprep.xyz'
    with pytest.raises(ValueError):
        FileParser(file_name)

def test_types(mock_fileparser, mock_mimetype):
    file_name = 'test_dataprep.xyz'
    fp = FileParser(file_name)
    assert fp.supported_file('application/test') == [{'file_type': 'xyz', 'loader_file_name': 'load_xyz', 'loader_class': 'LoadXYZ', 'mime_type': 'application/test'}]

def test_symlink_file(mock_fileparser, mock_mimetype):
    file_name = 'test_dataprep.xyz'
    with mock.patch('os.path.islink', return_value=True):
        with pytest.raises(ValueError, match=f"The file {file_name} is a symbolic link, which is not allowed."):
            FileParser(file_name)
