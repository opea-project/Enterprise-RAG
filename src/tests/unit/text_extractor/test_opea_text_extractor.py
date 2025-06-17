# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import patch, MagicMock, Mock, mock_open
from fastapi import UploadFile

from comps.text_extractor.utils.opea_text_extractor import OPEATextExtractor
from comps.cores.proto.docarray import DataPrepInput, TextDoc

@pytest.fixture
def reset_singleton():
    OPEATextExtractor._instance = None
    yield
    OPEATextExtractor._instance = None

@pytest.fixture
def mock_uploadfile():
    mock_file = MagicMock()
    mock_file.filename = "test_document.txt"
    mock_content = b"This is test content"
    mock_file.file.read.return_value = mock_content
    return mock_file

def test_singleton_behavior(reset_singleton):
    instance1 = OPEATextExtractor()
    instance2 = OPEATextExtractor()
    assert instance1 is instance2

# Tests for load_data method

@patch('comps.text_extractor.utils.opea_text_extractor.logger')
def test_load_data_with_no_input(mock_logging, reset_singleton):
    """Test that load_data raises ValueError when no files or links are provided."""
    text_extractor = OPEATextExtractor()
    input_data = DataPrepInput(files=[], links=[])

    with pytest.raises(ValueError) as exc_info:
        text_extractor.load_data(files=input_data.files, link_list=input_data.links)
        assert str(exc_info.value) == "No links and/or files passed for data preparation."

@patch.object(OPEATextExtractor, '_load_files')
@patch.object(OPEATextExtractor, '_load_links')
def test_load_data_with_files_only(mock_load_links, mock_load_files, reset_singleton):
    """Test load_data with only files provided."""
    text_extractor = OPEATextExtractor()
    mock_files = [Mock(spec=UploadFile)]
    mock_docs = [TextDoc(text="test content", metadata={"filename": "test.txt"})]
    mock_load_files.return_value = mock_docs

    result = text_extractor.load_data(files=mock_files, link_list=None)

    mock_load_files.assert_called_once_with(files=mock_files)
    mock_load_links.assert_not_called()
    assert result == mock_docs

@patch.object(OPEATextExtractor, '_load_files')
@patch.object(OPEATextExtractor, '_load_links')
def test_load_data_with_links_only(mock_load_links, mock_load_files, reset_singleton):
    """Test load_data with only links provided."""
    text_extractor = OPEATextExtractor()
    mock_links = ["https://example.com"]
    mock_docs = [TextDoc(text="test content", metadata={"url": "https://example.com"})]
    mock_load_links.return_value = mock_docs

    result = text_extractor.load_data(files=None, link_list=mock_links)

    mock_load_links.assert_called_once_with(links=mock_links)
    mock_load_files.assert_not_called()
    assert result == mock_docs

@patch.object(OPEATextExtractor, '_load_files')
@patch.object(OPEATextExtractor, '_load_links')
def test_load_data_with_both_files_and_links(mock_load_links, mock_load_files, reset_singleton):
    """Test load_data with both files and links provided."""
    text_extractor = OPEATextExtractor()
    mock_files = [Mock(spec=UploadFile)]
    mock_links = ["https://example.com"]
    file_docs = [TextDoc(text="file content", metadata={"filename": "test.txt"})]
    link_docs = [TextDoc(text="link content", metadata={"url": "https://example.com"})]

    mock_load_files.return_value = file_docs
    mock_load_links.return_value = link_docs

    result = text_extractor.load_data(files=mock_files, link_list=mock_links)

    mock_load_files.assert_called_once_with(files=mock_files)
    mock_load_links.assert_called_once_with(links=mock_links)
    assert result == file_docs + link_docs

@patch.object(OPEATextExtractor, '_load_files')
def test_load_data_file_exception(mock_load_files, reset_singleton):
    """Test that load_data properly handles exceptions from _load_files."""
    text_extractor = OPEATextExtractor()
    mock_files = [Mock(spec=UploadFile)]
    mock_load_files.side_effect = Exception("Test error")

    with pytest.raises(ValueError, match="Failed to load file"):
        text_extractor.load_data(files=mock_files, link_list=None)

# Tests for _load_files method

@patch.object(OPEATextExtractor, '_save_file_to_local_disk')
@patch.object(OPEATextExtractor, '_load_text')
def test_load_files(mock_load_text, mock_save_file, reset_singleton, mock_uploadfile):
    """Test the _load_files method with a single file."""
    text_extractor = OPEATextExtractor()
    mock_path = MagicMock()
    mock_path.resolve.return_value = "/tmp/test_document.txt"
    mock_save_file.return_value = mock_path
    mock_load_text.return_value = "Parsed text content"

    result = text_extractor._load_files([mock_uploadfile])

    mock_save_file.assert_called_once_with(mock_uploadfile)
    mock_load_text.assert_called_once_with("/tmp/test_document.txt")
    assert len(result) == 1
    assert isinstance(result[0], TextDoc)
    assert result[0].text == "Parsed text content"
    assert result[0].metadata['filename'] == "test_document.txt"
    assert 'timestamp' in result[0].metadata

@patch.object(OPEATextExtractor, '_save_file_to_local_disk')
@patch.object(OPEATextExtractor, '_load_text')
@patch('os.path.exists')
@patch('os.remove')
def test_load_files_cleanup(mock_remove, mock_exists, mock_load_text, mock_save_file, reset_singleton, mock_uploadfile):
    """Test that _load_files cleans up the saved file."""
    text_extractor = OPEATextExtractor()
    mock_path = MagicMock()
    mock_path.resolve.return_value = "/tmp/test_document.txt"
    mock_save_file.return_value = mock_path
    mock_load_text.return_value = "Parsed text content"
    mock_exists.return_value = True

    text_extractor._load_files([mock_uploadfile])

    mock_remove.assert_called_once_with("/tmp/test_document.txt")

# Tests for _load_links method

def test_load_links_invalid_url(reset_singleton):
    """Test that _load_links validates URLs properly."""
    text_extractor = OPEATextExtractor()
    invalid_urls = [
        "not_a_url",
        "http/example.com",
        "ftp://example.com"
    ]

    for url in invalid_urls:
        with pytest.raises(ValueError, match=f"The given link/str {url} cannot be parsed"):
            text_extractor._load_links([url])

@patch.object(OPEATextExtractor, '_save_link_to_local_disk')
@patch.object(OPEATextExtractor, '_load_text')
def test_load_links_regular_file(mock_load_text, mock_save_link, reset_singleton):
    """Test _load_links with a regular (non-HTML) link."""
    text_extractor = OPEATextExtractor()
    url = "https://example.com/document.pdf"
    parsed_link = {
        'url': url,
        'filename': 'document.pdf',
        'file_path': '/tmp/document.pdf',
        'content_type': 'application/pdf'
    }
    mock_save_link.return_value = parsed_link
    mock_load_text.return_value = "Parsed PDF content"

    result = text_extractor._load_links([url])

    mock_save_link.assert_called_once_with(url)
    mock_load_text.assert_called_once_with('/tmp/document.pdf')
    assert len(result) == 1
    assert result[0].text == "Parsed PDF content"
    assert result[0].metadata['url'] == url
    assert result[0].metadata['filename'] == 'document.pdf'

@patch.object(OPEATextExtractor, '_save_link_to_local_disk')
@patch.object(OPEATextExtractor, '_load_text')
@patch.object(OPEATextExtractor, '_load_html_data')
def test_load_links_html_file(mock_load_html, mock_load_text, mock_save_link, reset_singleton):
    """Test _load_links with an HTML link."""
    text_extractor = OPEATextExtractor()
    url = "https://example.com/page.html"
    parsed_link = {
        'url': url,
        'filename': 'page.html',
        'file_path': '/tmp/page.html',
        'content_type': 'text/html'
    }
    mock_save_link.return_value = parsed_link
    mock_load_html.return_value = "Processed HTML content"
    mock_load_text.return_value = "Parsed HTML content"

    # Mock open file operations
    m = mock_open()
    with patch("builtins.open", m):
        result = text_extractor._load_links([url])

    mock_save_link.assert_called_once_with(url)
    mock_load_html.assert_called_once_with('/tmp/page.html')
    mock_load_text.assert_called_once_with('/tmp/page.html')
    m().write.assert_called_once_with("Processed HTML content")

    assert len(result) == 1
    assert result[0].text == "Parsed HTML content"
