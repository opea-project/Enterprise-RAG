# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.text_extractor.utils.file_loaders.load_csv import LoadCsv
from comps.text_extractor.utils.file_loaders.load_adoc import LoadAsciiDoc
from comps.text_extractor.utils.file_loaders.load_doc import LoadDoc
from comps.text_extractor.utils.file_loaders.load_html import LoadHtml
from comps.text_extractor.utils.file_loaders.load_json import LoadJson
from comps.text_extractor.utils.file_loaders.load_pdf import LoadPdf
from comps.text_extractor.utils.file_loaders.load_ppt import LoadPpt
from comps.text_extractor.utils.file_loaders.load_txt import LoadTxt
from comps.text_extractor.utils.file_loaders.load_md import LoadMd
from comps.text_extractor.utils.file_loaders.load_xls import LoadXls
from comps.text_extractor.utils.file_loaders.load_xml import LoadXml
from comps.text_extractor.utils.file_loaders.load_yaml import LoadYaml
from comps.text_extractor.utils.file_loaders.load_with_markitdown import LoadWithMarkitdown
import os

def abs_file_path(file_name):
    file_path = '../../e2e/files/dataprep_upload/'
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path, file_name)

def test_adoc_loader():
    file_name = 'test_dataprep.adoc'
    loader = LoadAsciiDoc(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_csv_loader():
    file_name = 'test_dataprep.csv'
    loader = LoadCsv(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_doc_loader():
    file_name = 'test_dataprep_convert.doc'
    loader = LoadDoc(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_docx_loader():
    file_name = 'test_dataprep.docx'
    loader = LoadDoc(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_html_loader():
    file_name = 'test_dataprep.html'
    loader = LoadHtml(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_json_loader():
    file_name = 'test_dataprep.json'
    loader = LoadJson(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_jsonl_loader():
    file_name = 'test_dataprep.jsonl'
    loader = LoadJson(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_md_loader():
    file_name = 'test_dataprep.md'
    loader = LoadMd(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_pdf_loader():
    file_name = 'test_dataprep.pdf'
    loader = LoadPdf(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_ppt_loader():
    file_name = 'test_dataprep_convert.ppt'
    loader = LoadPpt(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_pptx_loader():
    file_name = 'story.pptx'
    file_path = '../../e2e/files/dataset_en/'

    loader = LoadPpt(os.path.join(os.path.dirname(__file__), file_path, file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_txt_loader():
    file_name = 'test_dataprep.txt'
    loader = LoadTxt(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_xls_loader():
    file_name = 'test_dataprep.xls'
    loader = LoadXls(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_xlsx_loader():
    file_name = 'test_dataprep.xlsx'
    loader = LoadXls(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_xml_loader():
    file_name = 'test_dataprep.xml'
    loader = LoadXml(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_yaml_loader():
    file_name = 'test_dataprep.yaml'
    loader = LoadYaml(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_load_with_markitdown():
    extensions = ['adoc', 'txt', 'json', 'jsonl', 'csv', 'xlsx', 'xls', 'html', 'md', 'xml', 'yaml']
    for extension in extensions:
        file_name = f'test_dataprep.{extension}'
        loader = LoadWithMarkitdown(abs_file_path(file_name))
        text = loader.extract_text()
        assert text is not None
        assert len(text) > 0

def test_utf8_encoding_beyond_4kb():
    """
    Test for encoding bug fix - special UTF-8 chars beyond first 4KB.

    Bug: markitdown detects charset from first 4KB only. When UTF-8 special chars
    (e.g., macramé) appear beyond 4KB in mostly-ASCII file, charset detection
    returns ASCII, then decode() throws UnicodeDecodeError.

    Without fix: UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3
    With fix: Falls back to full-file charset detection, succeeds
    """
    import tempfile

    # Create file matching bug report: mostly ASCII with UTF-8 chars late in file
    content = "hello world test " * 1000  # ~18KB of ASCII
    content += "macramé café résumé naïve"  # UTF-8 chars beyond 4KB detection window
    content += " more data" * 5000  # More content

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name

    try:
        loader = LoadWithMarkitdown(temp_path)
        text = loader.extract_text()

        # Verify file processed without UnicodeDecodeError
        assert text is not None
        assert len(text) > 0

        # Verify special UTF-8 characters preserved
        assert "macramé" in text, "UTF-8 char é not found"
        assert "café" in text, "UTF-8 char é not found"
        assert "résumé" in text, "UTF-8 char é not found"
        assert "naïve" in text, "UTF-8 char ï not found"
    finally:
        os.unlink(temp_path)
