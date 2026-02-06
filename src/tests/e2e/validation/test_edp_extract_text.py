#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest
import os

from tests.e2e.validation.buildcfg import cfg

# Skip all tests if edp is not deployed
if not cfg.get("edp", {}).get("enabled"):
    pytestmark = pytest.mark.skip(reason="EDP is not deployed")

logger = logging.getLogger(__name__)
FILES_DIR = "e2e/files/extract_text"
FILES_PREFIX = "extract_text_test_"
IN_PROGRESS_STATUSES = ["uploaded", "processing", "text_extracting", "text_compression", "text_splitting", "late_chunking", "embedding"]


@pytest.fixture(autouse=True)
def cleanup(edp_helper):
    yield
    logger.info("\nAttempting to clean up all items created during the test")
    files = edp_helper.list_files()
    for file in files.json():
        file_name = file["object_name"]
        if FILES_PREFIX in file_name:
            if file["status"] in IN_PROGRESS_STATUSES:
                logger.info(f"Canceling in progress task: {file_name}")
                edp_helper.cancel_processing_task(file["id"])
            elif file["status"] in ["ingested", "error"]:
                logger.info(f"Removing file: {file_name}")
                response = edp_helper.generate_presigned_url(file["object_name"], "DELETE", file["bucket_name"])
                edp_helper.delete_file(response.json().get("url"))

    links = edp_helper.list_links()
    for link in links.json():
        if FILES_PREFIX in link["uri"]:
            logger.info(f"Removing link: {link['uri']}")
            edp_helper.delete_link(link["id"])


@allure.testcase("IEASG-T218")
def test_edp_extract_text_adoc(edp_helper):
    """Test case containing all adoc extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "adoc"

    """Upload adoc file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "adoc")

    """Upload adoc file with some basic features and check that they are extracted correctly"""
    file = FILES_PREFIX + "basics.adoc"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    file_phrases = ["Text title",
                    "Bulleted list", "Bullet list element 1", "Bullet list element 2",
                    "Numbered list", "Number list element 1", "Number list element 2",
                    "Formatted text", "Bolded text", "Cursive text", "Underscored text"] 
    for phrase in file_phrases:
        assert phrase in extracted_text, f"Phrase '{phrase}' missing from the extracted text, extracted text: {extracted_text}"

    """Upload adoc file with links and check that they are extracted correctly"""
    file = FILES_PREFIX + "links.adoc"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    file_phrases = ["Custom link:", "http://samplelinkforadoc.org",
                    "Link to Google:", "https://google.com"] 
    for phrase in file_phrases:
        assert phrase in extracted_text, f"Phrase '{phrase}' missing from the extracted text, extracted text: {extracted_text}"

    """Upload adoc file with tables and check that they are extracted correctly"""
    file = FILES_PREFIX + "tables.adoc"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    standard_table_phrases = ["Table 1: Standard AsciiDoc Table",
                    "ID", "Name",
                    "1", "Number One",
                    "2", "Number Two" ]
    csv_table_phrases = ["Table 2: CSV Format Table",
                    "R0C0", "R0C1",
                    "R1C0", "R1C1"]
    multi_table_phrases = ["Table 3: Merged and Multiline Table",
                    "Row number", "Column 1", "Column 2",
                    "00", "Multi-column text",
                    "01", "Multi-row text", "Multi-line", "value",
                    "02", "Sample text"]
    for table_phrases in [standard_table_phrases, csv_table_phrases, multi_table_phrases]:
        for phrase in table_phrases:
            assert phrase in extracted_text, f"Phrase '{phrase}' missing from the extracted text, extracted text: {extracted_text}"

    """Upload adoc file with substituted words and check that they are extracted correctly"""
    file = FILES_PREFIX + "substitutions.adoc"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    sentence_in_file = "Simple sentence with substituted words."
    assert sentence_in_file in extracted_text, f"Sentence '{sentence_in_file}' missing from the extracted text, extracted text: {extracted_text}"

    """Upload adoc file with source code and check that it is extracted correctly"""
    file = FILES_PREFIX + "source_code.adoc"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    file_phrases = ["Example python source code:", "print(\"Hello, world!\")"] 
    for phrase in file_phrases:
        assert phrase in extracted_text, f"Phrase '{phrase}' missing from the extracted text, extracted text: {extracted_text}"

    """Upload adoc file recognized as text/troff mime type and check that its contents are extracted correctly"""
    file = FILES_PREFIX + "troff_mime_type.adoc"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    file_phrases = ["File header", "File content", "An example table", "Not important", "cell content"] 
    for phrase in file_phrases:
        assert phrase in extracted_text, f"Phrase '{phrase}' missing from the extracted text, extracted text: {extracted_text}"


@allure.testcase("IEASG-T219")
def test_edp_extract_text_txt(edp_helper):
    """Test case containing all txt extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "txt"

    """Upload txt file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "txt")


@allure.testcase("IEASG-T220")
def test_edp_extract_text_doc(edp_helper):
    """Test case containing all doc extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "doc"

    """Upload doc file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "doc")


@allure.testcase("IEASG-T221")
def test_edp_extract_text_pdf(edp_helper):
    """Test case containing all pdf extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "pdf"

    """Upload pdf file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "pdf")

    """Upload PDF file with links and check that the links are extracted correctly"""
    file = FILES_PREFIX + "links.pdf"
    links = ["www.SomeMadeUpSiteOne.com", "https://SomeMadeUpSiteTwo.org", "http://SomeMadeUpSiteThree.net",
             "https://SomeMadeUpSiteFour.pl", "http://bamboozlingwebsite.pl"]
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    for link in links:
        assert link in extracted_text, f"Link '{link}' missing from the extracted text, extracted text: {extracted_text}"

    """Upload PDF file with table and check that the text inside is extracted correctly"""
    file = FILES_PREFIX + "schedule.pdf"
    column_tags = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    time_stamps = ["6:00", "8:00", "8:30", "10:00", "11:05", "13:00", "14:00", "15:00", "15:05", "16:30"]
    subjects = {
        "Math" : 9,
        "Philosophy" : 1,
        "Swimming" : 1,
        "Theology" : 1,
        "Physics" : 4,
        "PE" : 1,
        "Computer" : 1,
        "Science" : 1,
        "Art" : 1,
        "Biology" : 1,
        "Chemistry" : 1
    }
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    assert all(day in extracted_text for day in column_tags)
    assert all(hours in extracted_text for hours in time_stamps)
    for subject in subjects:
        subject_number = extracted_text.count(subject)
        assert subject_number == subjects[subject]


@allure.testcase("IEASG-T318")
def test_edp_extract_text_pdf_complex(edp_helper):
    """Test case for complex pdf extract text scenario"""
    files_dir = FILES_DIR + "/" + "pdf"
    file = FILES_PREFIX + "complex.pdf"
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    extracted_text = extracted_text.lower()

    # Expect footer data to be excluded from extracted text
    assert "pppaaagggeee" not in extracted_text, "Extracted text contains data from a footer"

    # Expect document title to be present before data from the table
    document_title_str = "the description of the"
    table_string = "document author"
    assert extracted_text.index(document_title_str) < extracted_text.index(table_string), "Extracted text has unexpected order of contents"

    # Retrieve text from image
    image_text = "Lumic-Pelt: UV-Reflective Double Coat"
    assert image_text.lower() in extracted_text, "Extracted text does not contain text from an image"

    # Check made up words are present and not changed by OCR
    made_up_words = ["wwwooorrrdddsss", "cccaaattt", "dddoooggg"]
    for word in made_up_words:
        assert word in extracted_text, f"Extracted text does not contain made up word: {word}"

    # Check for space between the chunks of texts divided by image
    expected_text = "visitors. early"
    assert expected_text in extracted_text, f"Extracted text does not contain expected phrase with space: {expected_text}"

    # Check is these chunks (extracted from various parts of the document) are present in the extracted text
    expected_phrases = [
        "early inhabitants",
        "typically dark amber or hazel",
        "profound loyalty",
        "responsible breeding practices",
        "remarkable companion for active individuals"
    ]
    for phrase in expected_phrases:
        assert phrase in extracted_text, f"Extracted text does not contain expected phrase: {phrase}"


@allure.testcase("IEASG-T222")
def test_edp_extract_text_pptx(edp_helper):
    """Test case containing all pptx extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "pptx"

    """Upload pptx file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "pptx")

    """Upload PPTX file with text in image and check that the text is extracted correctly"""
    file = FILES_PREFIX + "text_in_image.pptx"
    text_in_image = "My name is John, and I am a human. Call me “John the Human”."
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    assert text_in_image in extracted_text, f"Extracted text '{extracted_text}' does not contain expected text '{text_in_image}'"


@allure.testcase("IEASG-T223")
def test_edp_extract_text_json(edp_helper):
    """Test case containing all json extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "json"

    """Upload json file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "json")


@allure.testcase("IEASG-T224")
def test_edp_extract_text_ppt(edp_helper):
    """Test case containing all ppt extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "ppt"

    """Upload ppt file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "ppt")


@allure.testcase("IEASG-T225")
def test_edp_extract_text_md(edp_helper):
    """Test case containing all md extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "md"

    """Upload md file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "md")


@allure.testcase("IEASG-T226")
def test_edp_extract_text_html(edp_helper):
    """Test case containing all html extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "html"

    """Upload html file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "html")


@allure.testcase("IEASG-T227")
def test_edp_extract_text_tiff(edp_helper):
    """Test case containing all tiff extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "tiff"

    """Upload tiff file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "tiff")


@allure.testcase("IEASG-T228")
def test_edp_extract_text_jpg(edp_helper):
    """Test case containing all jpg extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "jpg"

    """Upload jpg file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "jpg")


@allure.testcase("IEASG-T229")
def test_edp_extract_text_jpeg(edp_helper):
    """Test case containing all jpeg extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "jpeg"

    """Upload jpeg file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "jpeg")


@allure.testcase("IEASG-T230")
def test_edp_extract_text_png(edp_helper):
    """Test case containing all png extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "png"

    """Upload png file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "png")


@allure.testcase("IEASG-T231")
def test_edp_extract_text_svg(edp_helper):
    """Test case containing all svg extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "svg"

    """Upload svg file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "svg")


@allure.testcase("IEASG-T232")
def test_edp_extract_text_xlsx(edp_helper):
    """Test case containing all xlsx extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "xlsx"

    """Upload xlsx file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "xlsx")


@allure.testcase("IEASG-T233")
def test_edp_extract_text_xls(edp_helper):
    """Test case containing all xls extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "xls"

    """Upload xls file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "xls")


@allure.testcase("IEASG-T234")
def test_edp_extract_text_csv(edp_helper):
    """Test case containing all csv extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "csv"

    """Upload csv file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "csv")


@allure.testcase("IEASG-T235")
def test_edp_extract_text_jsonl(edp_helper):
    """Test case containing all jsonl extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "jsonl"

    """Upload jsonl file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "jsonl")


@allure.testcase("IEASG-T236")
def test_edp_extract_text_xml(edp_helper):
    """Test case containing all xml extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "xml"

    """Upload xml file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "xml")


@allure.testcase("IEASG-T237")
def test_edp_extract_text_docx(edp_helper):
    """Test case containing all docx extract text test scenarios"""

    files_dir = FILES_DIR + "/" + "docx"

    """Upload docx file with text only and check that it is extracted correctly"""
    extract_text_file_with_text_only(edp_helper, files_dir, "docx")

    """Upload docx file with text in table with single cell and check that the text is extracted correctly"""
    table_single_cell_file = FILES_PREFIX + "table_single_cell.docx"
    table_single_cell_contents = "This is text in a single cell of a table inside a docx file."
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, table_single_cell_file)
    assert table_single_cell_contents in extracted_text, f"Extracted text '{extracted_text}' does not match expected text '{table_single_cell_contents}'"

    """Upload docx file with text in table and check that the text is extracted correctly"""
    table_file = FILES_PREFIX + "table.docx"
    table_contents = ["Cell00", "Cell01", "Cell10", "Cell11"]
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, table_file)
    for cell_value in table_contents:
        assert cell_value in extracted_text, f"Extracted text does not contain expected cell: {cell_value}."

    """Upload docx file with formatted text and check that the text is extracted correctly"""
    formatted_text_file = FILES_PREFIX + "formatted_text.docx"
    formatted_sentences = ["Header of the file.",
                           "This is italic text.",
                           "This is bold text.", 
                           "This is underlined text.",
                           "This is colored text.",
                           "This is highlighted text.",
                           "This is big text."]
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, formatted_text_file)
    for sentence in formatted_sentences:
        assert sentence in extracted_text, f"Extracted text does not contain formatted text: {sentence}."

    """Upload docx file with link and check that the links are extracted correctly"""
    hyperlink_file = FILES_PREFIX + "text_with_hyperlink.docx"
    link = "https://xyz.com/"
    text =  f"This is a  link ({link})  to a website named XYZ."
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, hyperlink_file)
    assert link in extracted_text
    assert text in extracted_text

    """Upload docx file with numbered and bulleted lists and check that text is extracted correctly"""
    numbered_and_bulleted_list_file = FILES_PREFIX + "text_with_numbered_and_bulleted_lists.docx"
    file_contents = ["Bulleted list:", "Bullet 1", "Bullet 2", "Numbered list:", "Number 1", "Number 2"]
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, numbered_and_bulleted_list_file)
    for sentence in file_contents:
        assert sentence in extracted_text, f"Expected phrase '{sentence}' does not appear in extracted text: '{extracted_text}'"
    
    """Upload DOCX file with text in image and check that the text is extracted correctly"""
    file = FILES_PREFIX + "text_in_image.docx"
    text_in_image = "My name is John, and I am a human. Call me “John the Human”."
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    assert extracted_text == text_in_image, f"Extracted text '{extracted_text}' does not match expected text '{text_in_image}'"

    """Upload DOCX file with text in image inside a table and check that the text is extracted correctly"""
    file = FILES_PREFIX + "table_text_in_image.docx"
    text_in_image = "My name is John, and I am a human. Call me “John the Human”."
    extracted_text = upload_file_and_extract_text(edp_helper, files_dir, file)
    assert extracted_text == text_in_image, f"Extracted text '{extracted_text}' does not match expected text '{text_in_image}'"


def extract_text_file_with_text_only(edp_helper, dir, file_extension):
    """Upload file with text only and check that the text is extracted correctly"""
    file = f"{FILES_PREFIX}text_only.{file_extension}"
    expected_text = f"This is simple text in a {file_extension} file."
    text_from_file = upload_file_and_extract_text(edp_helper, dir, file)
    assert expected_text in text_from_file, f"Extracted text '{text_from_file}' does not match expected text '{expected_text}'"


def upload_file_and_extract_text(edp_helper, dir, file):
    edp_file = edp_helper.upload_file_and_wait_for_ingestion(os.path.join(dir, file))
    response = edp_helper.extract_text(edp_file["id"])
    assert response.status_code == 200, f"Failed to extract text. Response: {response.text}"
    return _get_extracted_text(response)


def _get_extracted_text(response):
    """response is the result of edp_helper.extract_text method"""
    extracted_text = ""
    logger.info(f"Number of extracted text positions: {len(response.json()["docs"]["docs"])}")
    for doc in response.json()["docs"]["docs"]:
        extracted_text = f"{extracted_text} {doc['text']}"
    return extracted_text.strip()
