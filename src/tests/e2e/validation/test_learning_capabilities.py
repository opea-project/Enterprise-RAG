#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import os
import pytest
import time
from types import SimpleNamespace
import yaml

from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR, TEST_FILES_DIR
from tests.e2e.validation.buildcfg import cfg

# Skip all tests if chatqa pipeline is not deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        break
else:
    pytestmark = pytest.mark.skip(reason="ChatQA pipeline is not deployed")


logger = logging.getLogger(__name__)
UNRELATED_RESPONSE_MSG = "Chatbot should return answer that is strictly related to the previously uploaded file"

# The following test cases are meant to check if chatbot learns from uploaded files.
# In each test case, a file is uploaded and a question related to the file content is asked.


@pytest.fixture
def test_data(request, test_language):
    """Load scenarios and package them with language info"""
    data_path = os.path.join(TEST_FILES_DIR, "localized_dataset.yaml")

    with open(data_path, "r", encoding="utf-8") as f:
        scenarios = yaml.load(f, Loader=yaml.SafeLoader)

    current_scenario = scenarios.get(request.node.name, [])
    stages = [step[test_language] for step in current_scenario if test_language in step]

    return SimpleNamespace(stages=stages, language=test_language)


@pytest.mark.smoke
@allure.testcase("IEASG-T50")
def test_txt(edp_helper, chatqa_api_helper, test_data):
    """*.txt file learning capabilities"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@pytest.mark.smoke
@allure.testcase("IEASG-T56")
def test_docx_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@pytest.mark.smoke
@allure.testcase("IEASG-T54")
def test_pdf_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.pdf file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@pytest.mark.smoke
@allure.testcase("IEASG-T55")
def test_pptx_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.pptx file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T230")
def test_pptx_complex(edp_helper, chatqa_api_helper, test_data):
    """*.pptx file learning capabilities (tables, charts, and SmartArt)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T104")
def test_json_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.json file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T105")
def test_doc_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.doc file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T106")
def test_ppt_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.ppt file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


def test_msg_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.msg file learning capabilities (Outlook email - pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T107")
def test_md_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.md file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T108")
def test_html_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.html file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T109")
def test_tiff_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.tiff file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T110")
def test_jpg_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.jpg file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T111")
def test_jpeg_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.jpeg file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T112")
def test_png_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.png file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T113")
def test_svg_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.svg file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T114")
def test_xlsx_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.xlsx file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T115")
def test_xls_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.xls file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T116")
def test_csv_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.csv file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T117")
def test_jsonl_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.jsonl file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T118")
def test_xml_text_only(edp_helper, chatqa_api_helper, test_data):
    """*.xml file learning capabilities (pure text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T162")
def test_docx_multi_paragraph(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (multiple paragraphs inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T163")
def test_docx_with_images(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (with images and text surrounding the images)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@pytest.mark.xfail(reason="Feature not implemented yet")
@allure.testcase("IEASG-T164")
def test_get_context_from_filename(edp_helper, chatqa_api_helper):
    """Upload a file with a unique name. Ask a question related to the file name to verify if it has been ingested"""
    question = "Which company does Zerilwyn Nactroske currently work for?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "Zerilwyn Nactroske - CV.docx", question)
    assert chatqa_api_helper.words_in_response(["deepmind"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T166")
def test_docx_tables(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (with tables inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T165")
def test_docx_formatted_text(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (with formatted text inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T167")
def test_docx_with_hyperlink(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (with hyperlinks inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T168")
def test_docx_numbered_and_bulleted_lists(edp_helper, chatqa_api_helper, test_data):
    """*.docx file learning capabilities (with numbered and bulleted lists inside the file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@pytest.mark.smoke
@allure.testcase("IEASG-T169")
def test_content_is_forgotten_after_file_deletion(edp_helper, chatqa_api_helper, test_data):
    """Verify if the content is actually forgotten after file deletion"""
    stage = test_data.stages[0]
    file_name = stage["files"][0]
    question = stage["questions"][0]["question"]
    expected = stage["questions"][0]["expected_any"]

    file_path = os.path.join(TEST_FILES_DIR, f"dataset_{test_data.language}", file_name)
    logger.info(f"Ingesting file: {file_name}")
    edp_helper.upload_file_and_wait_for_ingestion(file_path)
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(expected, response), UNRELATED_RESPONSE_MSG

    response = delete_file(edp_helper, file_path)
    assert response.status_code == 204, f"Failed to delete file. Response: {response.text}"
    logger.debug("Sleeping to make sure the file is deleted")
    time.sleep(10)
    logger.debug("Asking question once again after file deletion")
    response = ask_question(chatqa_api_helper, question)
    assert not chatqa_api_helper.words_in_response(expected, response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T176")
def test_adoc_basic(edp_helper, chatqa_api_helper, test_data):
    """Validate basic *.adoc files support and learning capabilities"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T177")
def test_adoc_recognized_as_troff_mime_type(edp_helper, chatqa_api_helper, test_data):
    """
    Upload a file with 'text/troff' mime type.
    Check if the file is recognized as adoc.
    Ask a question related to the content of the file.
    """
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T178")
def test_adoc_links(edp_helper, chatqa_api_helper, test_data):
    """Check if links are properly extracted from the adoc file"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T179")
def test_adoc_tables(edp_helper, chatqa_api_helper, test_data):
    """Validate if tables are recognized in the adoc file"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T180")
def test_adoc_source_code(edp_helper, chatqa_api_helper, test_data):
    """Put a code block in the adoc file and check if it is recognized"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T181")
def test_adoc_substitutions(edp_helper, chatqa_api_helper, test_data):
    """Check if substitutions are recognized in the text (*.adoc file)"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T262")
def test_logs_parsing_capability(edp_helper, chatqa_api_helper, test_data):
    """Check if chatbot can extract information from log files"""
    run_standard_validation(edp_helper, chatqa_api_helper, test_data)


@allure.testcase("IEASG-T264")
def test_reupload(edp_helper, chatqa_api_helper, test_data):
    """Check if re-uploading the same file and updated file works as expected"""

    def modify_file(file__to_modify, old_value, new_value):
        with open(file__to_modify, "r+") as f:
            content = f.read().replace(old_value, new_value)
            f.seek(0)
            f.write(content)
            f.truncate()

    stage = test_data.stages[0]
    file_name = stage["files"][0]
    question = stage["questions"][0]["question"]
    expected_initial = stage["questions"][0]["expected_any"][0]
    expected_modified = stage["questions"][0]["expected_modified"]
    modify_old = stage["questions"][0]["modify_old"]
    modify_new = stage["questions"][0]["modify_new"]

    file_path = os.path.join(TEST_FILES_DIR, f"dataset_{test_data.language}", file_name)

    # Upload initial file
    edp_helper.upload_file_and_wait_for_ingestion(file_path)
    response = ask_question(chatqa_api_helper, question)
    assert expected_initial in response, UNRELATED_RESPONSE_MSG

    # Re-upload the same file
    edp_helper.upload_file_and_wait_for_ingestion(file_path)
    response = ask_question(chatqa_api_helper, question)
    assert expected_initial in response, UNRELATED_RESPONSE_MSG

    # Upload updated file
    try:
        modify_file(file_path, modify_old, modify_new)
        edp_helper.upload_file_and_wait_for_ingestion(file_path)
        response = ask_question(chatqa_api_helper, question)
        assert expected_modified in response, UNRELATED_RESPONSE_MSG
    finally:
        modify_file(file_path, modify_new, modify_old)  # restore original file content


@allure.testcase("IEASG-T249")
def test_similarity_search_with_siblings(edp_helper, chatqa_api_helper, fingerprint_api_helper, test_data):
    """
    Upload a file with a list of 20 elements.
    Ask a question that requires the entire list to be included in the answer.
    With retriever's search type set to 'similarity', expect the answer to be incomplete.
    Change the retriever's search type to 'similarity_with_siblings' and expect the answer to be complete.
    """
    # Skip the test if late chunking is enabled
    if cfg.get("edp", {}).get("late_chunking", {}).get("enabled", False):
        pytest.skip("Test is not applicable when late chunking is enabled")

    current_parameters = fingerprint_api_helper.append_arguments("").json().get("parameters", {})
    original_k = current_parameters.get("k")
    original_search_type = current_parameters.get("search_type")
    if not original_k or not original_search_type:
        pytest.skip("Failed to get current retriever's parameters")

    stage = test_data.stages[0]
    file_name = stage["files"][0]
    question = stage["questions"][0]["question"]
    expected_absent = stage["questions"][0]["expected_absent"]
    expected_present = stage["questions"][0]["expected_present"]

    file_path = os.path.join(TEST_FILES_DIR, f"dataset_{test_data.language}", file_name)
    edp_helper.upload_file_and_wait_for_ingestion(file_path)

    try:
        if original_search_type != "similarity":
            fingerprint_api_helper.set_component_parameters("retriever", search_type="similarity", k=original_k)

        response = ask_question(chatqa_api_helper, question)
        assert expected_absent not in response, (f"'{expected_absent}' is the last principle in the list. It should not be "
                                               "included in the answer when search_type='similarity'")

        # Change search type to similarity_with_siblings. Expect the response to be longer
        fingerprint_api_helper.set_component_parameters("retriever", search_type="similarity_search_with_siblings",
                                                        k=original_k)
        response = ask_question(chatqa_api_helper, question)
        assert expected_present in response, "With similarity_with_siblings search type, the answer should be longer"
    finally:
        # Restore default parameters
        fingerprint_api_helper.set_component_parameters("retriever", search_type=original_search_type, k=original_k)


@allure.testcase("IEASG-T308")
def test_late_chunking(edp_helper, chatqa_api_helper, fingerprint_api_helper, test_data):
    """
    Upload a file with a list of 35 elements.
    Ask a question that requires the entire list to be included in the answer.
    With late chunking enabled, expect the full answer. Otherwise, just save the response for comparison.
    """
    stage = test_data.stages[0]
    file = stage["files"][0]
    q = stage["questions"][0]

    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, f"dataset_{test_data.language}", file))

    response = ask_question(chatqa_api_helper, q["question"])
    if cfg.get("edp", {}).get("late_chunking", {}).get("enabled", False):
        # With late chunking enabled, expect the full answer
        assert chatqa_api_helper.words_in_response(q["expected_all"], response)


@pytest.mark.xfail(reason="Feature not implemented yet - requires graph structures support")
@allure.testcase("IEASG-T196")
def test_long_agenda_simple_questions(edp_helper, chatqa_api_helper):
    """
    This tests checks if chatbot can connect large pieces of information (events) to another one (events' days)
    This lightway part of the tests ask simple questions about event or time to see if information
    was identified and classified correctly.
    """
    file = "long-agenda.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))

    with (allure.step("Ask about time of event")):
        question = "When is the lunch break on Day 2?"
        response = ask_question(chatqa_api_helper, question)
        assert chatqa_api_helper.words_in_response(
            [
                "12:00 PM - 01:00 PM",
                "from 12:00 PM to 01:00 PM",
            ],
            response), UNRELATED_RESPONSE_MSG

    with allure.step("Ask about event happening once"):
        question = "When are awards ceremony"
        response = ask_question(chatqa_api_helper, question)
        assert chatqa_api_helper.all_words_in_response(["day 2", "07:00 PM", "08:30 PM"], response), UNRELATED_RESPONSE_MSG

    with allure.step("Ask about event happening both days"):
        question = "When are Scrimmage Games?"
        response = ask_question(chatqa_api_helper, question)
        assert chatqa_api_helper.all_words_in_response(["day 1", "day 2"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.xfail(reason="Feature not implemented yet - requires graph structures support")
@allure.testcase("IEASG-T200")
def test_long_agenda_summary_questions(edp_helper, chatqa_api_helper):
    """
        This tests checks if chatbot can connect large pieces of information (events) to another one (events' days)
        This test verifies if chatbot can summarize all information related to a given day.
        """
    file = "long-agenda.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))
    with allure.step("Summarize question about a day"):
        required_mentions = ["registration", "welcome", "warm-up", "stretching", "skill development",
                             "lunch", "team building", "scrimmage", "cool down", "dinner", "entertainment", "wind down",
                             "bedtime"]
        question = "What happens on day 1?"
        response = ask_question(chatqa_api_helper, question)
        assert chatqa_api_helper.all_words_in_response(required_mentions, response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T199")
def test_updated_file(edp_helper, chatqa_api_helper):
    question_1 = "Who is Alex?"
    expected_1_before = ["sloth"]
    expected_1_after = ["fox"]

    question_2 = "Where does Alex live?"
    expected_2_before = ["rainforest", "Amazon", "america", "south"]
    expected_2_after = ["cold", "tundra", "arctic", "north"]

    question_3 = "What does Alex eat?"
    expected_3_before = ["leaves", "shoots", "fruits"]
    expected_3_after = ["carnivor", "fish", "birds"]

    file = "test_updated_document.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))

    response_1_before = ask_question(chatqa_api_helper, question_1)
    assert chatqa_api_helper.words_in_response(expected_1_before, response_1_before), UNRELATED_RESPONSE_MSG

    response_2_before = ask_question(chatqa_api_helper, question_2)
    assert chatqa_api_helper.words_in_response(expected_2_before, response_2_before), UNRELATED_RESPONSE_MSG

    response_3_before = ask_question(chatqa_api_helper, question_3)
    assert chatqa_api_helper.words_in_response(expected_3_before, response_3_before), UNRELATED_RESPONSE_MSG

    with edp_helper.substitute_file("test_updated_document.txt", "test_updated_document-updated.txt"):
        edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))

        response_1_after = ask_question(chatqa_api_helper, question_1)
        assert chatqa_api_helper.words_in_response(expected_1_after, response_1_after), UNRELATED_RESPONSE_MSG

        response_2_after = ask_question(chatqa_api_helper, question_2)
        assert chatqa_api_helper.words_in_response(expected_2_after, response_2_after), UNRELATED_RESPONSE_MSG

        response_3_after = ask_question(chatqa_api_helper, question_3)
        assert chatqa_api_helper.words_in_response(expected_3_after, response_3_after), UNRELATED_RESPONSE_MSG


@pytest.mark.xfail(reason="Feature not implemented yet - requires graph structures support")
@allure.testcase("IEASG-T246")
def test_json_config_file_insights(edp_helper, chatqa_api_helper):
    """
    Upload a JSON config file and ask questions related to the content of the file.
    Force the chatbot to extract information from across the entire file, not just from a single line.
    """
    file = "sample_config.json"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))
    question = "What is the database type used by the user-service?"
    response = ask_question(chatqa_api_helper, question)
    assert "mysql" in response.lower(), UNRELATED_RESPONSE_MSG

    question = "What services are enabled in ExampleMicroservicesSystem under 'services' section?"
    enabled_services = ["auth-service", "user-service", "order-service", "reporting-service"]
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.all_words_in_response(enabled_services, response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T248")
def test_multi_doc_reasoning(edp_helper, chatqa_api_helper):
    """
    Upload 2 documents:
    A: Marianooo has 20 balls for a game called Marianoball.
    B: One ball for the game called Marianoball costs 15$.
    Check if chatbot can combine information from both documents to answer the question:
    "What is the total value of all Marianooo's balls for the game called Marianoball?"
    """
    file1 = "multi_doc_retrieval_1.txt"
    file2 = "multi_doc_retrieval_2.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file1))
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file2))

    question = "What is the total value of all Marianooo's balls for the game called Marianoball?"
    response = ask_question(chatqa_api_helper, question)
    assert "300" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T247")
def test_top_n(edp_helper, chatqa_api_helper, fingerprint_api_helper, test_data):
    """
    Upload 2 documents:
    A: Emanueleee has got 4 RC cars.
    B: Raffaeleee has got 27 RC cars.
    Ask a question that requires information from both documents to be answered:
    "How many RC cars do Emanueleee and Raffaeleee have in total?"
    Change top_n parameter to 1 and check if the answer is wrong (only one document should be used to answer the question).
    Change top_n parameter to 3 and check if the answer is correct (both documents should be used to answer the question).
    """
    current_parameters = fingerprint_api_helper.append_arguments("").json().get("parameters", {})
    original_n = current_parameters.get("top_n")

    # Get the first (and only) stage for this test from the unified test_data object
    stage = test_data.stages[0]
    question_item = stage["questions"][0]
    question = question_item["question"]
    expected_value = question_item["expected_any"][0]

    # 1. Ingest files using the language defined in test_data
    for file_name in stage.get("files", []):
        path = os.path.join(TEST_FILES_DIR, f"dataset_{test_data.language}", file_name)
        edp_helper.upload_file_and_wait_for_ingestion(path)

    try:
        fingerprint_api_helper.set_component_parameters("reranker", top_n=1)
        response = ask_question(chatqa_api_helper, question)
        assert expected_value not in response.lower(), "only a single document should be used to answer the question"

        fingerprint_api_helper.set_component_parameters("reranker", top_n=3)
        response = ask_question(chatqa_api_helper, question)
        assert expected_value in response.lower(), "3 documents should be used to answer the question"
    finally:
        # revert top_n back to original value
        fingerprint_api_helper.set_component_parameters("reranker", top_n=original_n)


def upload_and_ask_question(edp_helper, chatqa_api_helper, file, question=""):
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(DATAPREP_UPLOAD_DIR, file))
    return ask_question(chatqa_api_helper, question)


def ask_question(chatqa_api_helper, question=""):
    """Ask a question to the chatbot and return the response"""
    response = chatqa_api_helper.call_chatqa(question)
    assert response.status_code == 200, "Unexpected status code returned"
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}")
    return response_text


def delete_file(edp_helper, file):
    response = edp_helper.generate_presigned_url(file, "DELETE")
    return edp_helper.delete_file(response.json().get("url"))


def run_standard_validation(edp_helper, chatqa_api_helper, test_data):
    """
    For each stage in the test data:
    1. Ingest files specified in the stage.
    2. For each question in the stage, ask the question and validate the response against expected answers.
    3. Support both 'expected_any' and 'expected_all' validation methods.
    """
    for stage in test_data.stages:
        # 1. File ingestion
        for file_name in stage.get("files", []):
            path = os.path.join(TEST_FILES_DIR, f"dataset_{test_data.language}", file_name)
            logger.info(f"Ingesting file: {file_name}")
            edp_helper.upload_file_and_wait_for_ingestion(path)

        # 2. Question validation
        for item in stage.get("questions", []):
            question = item.get("question")
            response = ask_question(chatqa_api_helper, question)

            # expected_any: success if at least one string is found
            if "expected_any" in item:
                expected_list = item["expected_any"]
                assert chatqa_api_helper.words_in_response(expected_list, response), \
                    f"Assertion failed! None of {expected_list} found in response: {response}"

            # expected_all: success only if all strings are found
            if "expected_all" in item:
                expected_list = item["expected_all"]
                missing_words = [word for word in expected_list if word.lower() not in response.lower()]
                assert not missing_words, \
                    f"Assertion failed! Missing words: {missing_words} in response: {response}"