# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.dataprep.utils.file_loaders.load_csv import LoadCsv
from comps.dataprep.utils.file_loaders.load_doc import LoadDoc
from comps.dataprep.utils.file_loaders.load_html import LoadHtml
from comps.dataprep.utils.file_loaders.load_json import LoadJson
from comps.dataprep.utils.file_loaders.load_pdf import LoadPdf
from comps.dataprep.utils.file_loaders.load_ppt import LoadPpt
from comps.dataprep.utils.file_loaders.load_txt import LoadTxt
from comps.dataprep.utils.file_loaders.load_md import LoadMd
from comps.dataprep.utils.file_loaders.load_xls import LoadXls
from comps.dataprep.utils.file_loaders.load_xml import LoadXml
from comps.dataprep.utils.file_loaders.load_yaml import LoadYaml
import os

def abs_file_path(file_name):
    file_path = '../../files/dataprep_upload/'
    return os.path.join(os.path.dirname(__file__), file_path, file_name)

def test_csv_loader():
    file_name = 'test_dataprep.csv'
    loader = LoadCsv(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_doc_loader():
    file_name = 'test_dataprep.doc'
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
    file_name = 'test_dataprep.ppt'
    loader = LoadPpt(abs_file_path(file_name))
    text = loader.extract_text()
    assert text is not None
    assert len(text) > 0

def test_pptx_loader():
    file_name = 'test_dataprep.pptx'
    loader = LoadPpt(abs_file_path(file_name))
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
