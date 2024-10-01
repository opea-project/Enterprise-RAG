from unittest import mock
from comps.dataprep.utils.file_parser import FileParser
import pytest

@pytest.fixture
def mock_fileparser():
    val = [ {'file_type': 'xyz', 'loader_file_name': 'load_xyz', 'loader_class': 'LoadXYZ'} ]
    with mock.patch('comps.dataprep.utils.file_parser.FileParser.default_mappings', return_value=val):
        yield

def test_not_supported_loader():
    file_name = 'test_dataprep.foo'
    with pytest.raises(ValueError):
        FileParser(file_name)

def test_supported_mappings(mock_fileparser):
    file_name = 'test_dataprep.xyz'
    fp = FileParser(file_name)
    assert fp.supported_types() == ['xyz']

def test_types(mock_fileparser):
    file_name = 'test_dataprep.xyz'
    fp = FileParser(file_name)
    assert fp.supported_file(fp.file_type) == {'file_type': 'xyz', 'loader_file_name': 'load_xyz', 'loader_class': 'LoadXYZ'}
