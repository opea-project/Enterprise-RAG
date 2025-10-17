#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest
import time
import os

from constants import TEST_FILES_DIR

logger = logging.getLogger(__name__)

UNRELATED_RESPONSE_MSG = "Chatbot should return answer that is strictly related to the previously uploaded file"

# The following test cases are meant to check if chatbot learns from uploaded files.
# In each test case, a file is uploaded and a question related to the file content is asked.


@pytest.mark.smoke
@allure.testcase("IEASG-T50")
def test_txt(edp_helper, chatqa_api_helper):
    """*.txt file learning capabilities"""
    question = "How many cars commonly called MALUCH are registered in Gdansk?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.txt", question)
    assert "851" in response, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T56")
def test_docx_text_only(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (pure text inside the file)"""
    question = "What was the name of the girl who decided to visit the old tree at the edge of the village?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.docx", question)
    assert "Asfehehehe" in response, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T54")
def test_pdf_text_only(edp_helper, chatqa_api_helper):
    """*.pdf file learning capabilities (pure text inside the file)"""
    question = "In the story about Intel's headquarters in Gdansk, what was found by Krystianooo?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.pdf", question)
    assert chatqa_api_helper.words_in_response(["door", "dimension"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T55")
def test_pptx_text_only(edp_helper, chatqa_api_helper):
    """*.pptx file learning capabilities (pure text inside the file)"""
    question = "In the story about validation team at Impelooo, what surprising things has AI started to write?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.pptx", question)
    assert "poetry" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T104")
def test_json_text_only(edp_helper, chatqa_api_helper):
    """*.json file learning capabilities (pure text inside the file)"""
    question = "What is RagRag?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.json", question)
    assert "whale" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T105")
def test_doc_text_only(edp_helper, chatqa_api_helper):
    """*.doc file learning capabilities (pure text inside the file)"""
    question = "What rare ingredient did Zephyrglint add to his potion during the lunar eclipse?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.doc", question)
    assert chatqa_api_helper.words_in_response(["marshfire", "dew"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T106")
def test_ppt_text_only(edp_helper, chatqa_api_helper):
    """*.ppt file learning capabilities (pure text inside the file)"""
    question = "How did Snizzleflap arrive in Fluffington?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.ppt", question)
    assert chatqa_api_helper.words_in_response(["sky", "cloud"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T107")
def test_md_text_only(edp_helper, chatqa_api_helper):
    """*.md file learning capabilities (pure text inside the file)"""
    question = "What was Crinklebonk made of?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.md", question)
    assert "paper" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T108")
def test_html_text_only(edp_helper, chatqa_api_helper):
    """*.html file learning capabilities (pure text inside the file)"""
    question = ("What are some of the things that people in the town of Glimphtoodle began to forget "
                "as the strange phenomenon progressed?")
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.html", question)
    assert chatqa_api_helper.words_in_response(["pie", "song", "conversations", "friend", "plan"], response),(
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T109")
def test_tiff_text_only(edp_helper, chatqa_api_helper):
    """*.tiff file learning capabilities (pure text inside the file)"""
    question = "What was the name of Zanthroglid's famous creation?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.tiff", question)
    assert chatqa_api_helper.words_in_response(["clockwork", "duck"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T110")
def test_jpg_text_only(edp_helper, chatqa_api_helper):
    """*.jpg file learning capabilities (pure text inside the file)"""
    question = "What was Zorvultrix's rare ability?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jpg", question)
    assert chatqa_api_helper.words_in_response(["heal", "wound"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T111")
def test_jpeg_text_only(edp_helper, chatqa_api_helper):
    """*.jpeg file learning capabilities (pure text inside the file)"""
    question = "What was Frellor Tindrack's goal?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jpeg", question)
    assert chatqa_api_helper.words_in_response(["island", "find", "ilverden"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T112")
def test_png_text_only(edp_helper, chatqa_api_helper):
    """*.png file learning capabilities (pure text inside the file)"""
    question = "What did Squeeferplonk discover in the hidden cave?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.png", question)
    assert chatqa_api_helper.words_in_response(["crystal", "power"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T113")
def test_svg_text_only(edp_helper, chatqa_api_helper):
    """*.svg file learning capabilities (pure text inside the file)"""
    question = "What was Klythar Pindlebaum's profession?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.svg", question)
    assert chatqa_api_helper.words_in_response(["architect", "designer"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T114")
def test_xlsx_text_only(edp_helper, chatqa_api_helper):
    """*.xlsx file learning capabilities (pure text inside the file)"""
    question = "What was Zerlith Quarble's profession or passion?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xlsx", question)
    assert "alchemist" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T115")
def test_xls_text_only(edp_helper, chatqa_api_helper):
    """*.xls file learning capabilities (pure text inside the file)"""
    question = "What did Brindle Sprocketwick create that was extraordinary?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xls", question)
    assert "clock" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T116")
def test_csv_text_only(edp_helper, chatqa_api_helper):
    """*.csv file learning capabilities (pure text inside the file)"""
    question = "What did the Sandweaver create when it malfunctioned?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.csv", question)
    assert chatqa_api_helper.words_in_response(["golden ", "dust", "strange", "sand", "cloth"], response), (
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T117")
def test_jsonl_text_only(edp_helper, chatqa_api_helper):
    """*.jsonl file learning capabilities (pure text inside the file)"""
    question = "What was Yulvar Dimspark's secret talent?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jsonl", question)
    assert chatqa_api_helper.words_in_response(["manipulate ", "time", "rewind", "moments"], response), (
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T118")
def test_xml_text_only(edp_helper, chatqa_api_helper):
    """*.xml file learning capabilities (pure text inside the file)"""
    question = "What was Tressivorn Quindle known for in Bravenreach?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xml", question)
    assert chatqa_api_helper.words_in_response(["brewed", "potion", "wound"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T162")
def test_docx_multi_paragraph(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (multiple paragraphs inside the file)"""
    question = ("How many people work in the team that the Cloud Solutions Developer Intern for AI RAG Application "
                "candidate joins?")
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "Front-end Intern_example.docx", question)
    assert chatqa_api_helper.words_in_response(["12", "13"], response), UNRELATED_RESPONSE_MSG
    question = "What is the name of the group offering the Cloud Solutions Developer Intern for AI RAG position?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["dcai", "ecosystem"], response), UNRELATED_RESPONSE_MSG
    question = ("What technologies do I need to know when applying for the position of "
                "Cloud Solutions Developer Intern for AI RAG Application?")
    response = ask_question(chatqa_api_helper, question)
    technologies = ["react", "javascript", "css", "git", "jenkins", "ansible", "terraform", "kubernetes", "docker", "cicd", 
                    "github", "typescript", "react redux", "react router", "tailwind", "linux", "aws"]
    assert chatqa_api_helper.words_in_response(technologies, response), (
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T163")
def test_docx_with_images(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (with images and text surrounding the images)"""
    question = "What was Vellimer doing when the storm occurred?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story_docx_pictures.docx", question)
    assert chatqa_api_helper.words_in_response(["roof", "rod", "waiting"], response), UNRELATED_RESPONSE_MSG
    question = ("How does the village of Fernloft remember Vellimer today?"
                "What signs make them think he might still be around? ")
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["broom", "weather"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.xfail(reason="Feature not implemented yet")
@allure.testcase("IEASG-T164")
def test_get_context_from_filename(edp_helper, chatqa_api_helper):
    """Upload a file with a unique name. Ask a question related to the file name to verify if it has been ingested"""
    question = "Which company does Zerilwyn Nactroske currently work for?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "Zerilwyn Nactroske - CV.docx", question)
    assert chatqa_api_helper.words_in_response(["deepmind"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T166")
def test_docx_tables(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (with tables inside the file)"""
    # 1. Table with a single cell
    question = "What was the proffession of the person who whispered the name Trenvahir?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_table_single_cell.docx", question)
    assert chatqa_api_helper.words_in_response(["clockmaker"], response), UNRELATED_RESPONSE_MSG
    # 2. Table with many cells
    question = "Who discovered a plant called Whisperfern Lucida?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_table.docx", question)
    assert chatqa_api_helper.words_in_response(["kren", "talweir"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T165")
def test_docx_formatted_text(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (with formatted text inside the file)"""
    # 1. Check if heading is recognized
    question = "What is the full name of girl called Lucifelle?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_formatted_text.docx", question)
    assert chatqa_api_helper.words_in_response(["lunibelle", "sound"], response), UNRELATED_RESPONSE_MSG
    # 2. Test italic text
    question = "In the story about Lunibelle Lucifelle, what did the girl loved to collect?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["sound"], response), UNRELATED_RESPONSE_MSG
    # 3. Test bold text
    question = "How did the villagers perceive Lunibelle Lucifelle?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["strange", "kind"], response), UNRELATED_RESPONSE_MSG
    # 4. Test underline text
    question = "What did people call Lunibelle Lucifelle before they learned her name?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["sound girl"], response), UNRELATED_RESPONSE_MSG
    # 5. Test color text
    question = "What did Lunibelle Lucifelle do when she reached the center of the square?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["box", "whisper", "sky"], response), UNRELATED_RESPONSE_MSG
    # 6. Test text highlighted in yellow
    question = "What sound did the rain make in the story about Lunibelle Lucifelle?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["clapped", "hands"], response), UNRELATED_RESPONSE_MSG
    # 7. Test big text
    question = "How do people react when they hear the wind play a soft tune in the story about Lunibelle Lucifelle?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["smile"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T167")
def test_docx_with_hyperlink(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (with hyperlinks inside the file)"""
    question = "Give me a link to a website called AAAFFFGGGKKK"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_with_hyperlink.docx", question)
    assert "aaafffgggkkk-top-secret.com" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T168")
def test_docx_numbered_and_bulleted_lists(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (with numbered and bulleted lists inside the file)"""
    # 1. Test bulleted list
    question = "When was the document 'YYTTRREEWWQQ' created at?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_numbered_and_bulleted_lists.docx", question)
    assert "17" in response.lower(), UNRELATED_RESPONSE_MSG
    # 2. Test numbered list
    question = "What happens when the 'vanishing algorithm' is executed in a closed environment?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["0.43", "0,43"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T169")
def test_content_is_forgotten_after_file_deletion(edp_helper, chatqa_api_helper):
    """Verify if the content is actually forgotten after file deletion"""
    question = "What did the note say that Zenvorlith Marnqueeble left when he disappeared?"
    file_name = "story_to_be_deleted.txt"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, file_name, question)
    assert chatqa_api_helper.words_in_response(["nice", "forget", "remember"], response), UNRELATED_RESPONSE_MSG
    response = delete_file(edp_helper, os.path.join(TEST_FILES_DIR, file_name))
    assert response.status_code == 204, f"Failed to delete file. Response: {response.text}"
    logger.debug("Sleeping to make sure the file is deleted")
    time.sleep(10)
    logger.debug("Asking question once again after file deletion")
    response = ask_question(chatqa_api_helper, question)
    assert not chatqa_api_helper.words_in_response(["nice", "forget", "remember"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T176")
def test_adoc_basic(edp_helper, chatqa_api_helper):
    """Validate basic *.adoc files support and learning capabilities"""
    # 1. Test lists
    question = "What did Grendal Nuvrick see when he woke up?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.adoc", question)
    assert "squirrel" in response.lower(), UNRELATED_RESPONSE_MSG

    # 2. Test titles
    question = "What are the titles in the story about Grendal Nuvrick?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["strange", "end"], response), UNRELATED_RESPONSE_MSG

    # 3. Text formatting
    question = "What did Grendal Nuvrick say when he saw the squirrel?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["not", "normal"], response), UNRELATED_RESPONSE_MSG
    question = "What did Grendal Nuvrick say when he opened the door and smiled?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["think", "stay"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T177")
def test_adoc_recognized_as_troff_mime_type(edp_helper, chatqa_api_helper):
    """
    Upload a file with 'text/troff' mime type.
    Check if the file is recognized as adoc.
    Ask a question related to the content of the file.
    """
    question = " What category does Flornax Quibit belong to?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_troff_mime_type.adoc", question)
    assert "homeware" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T178")
def test_adoc_links(edp_helper, chatqa_api_helper):
    """Check if links are properly extracted from the adoc file"""
    question = "Give me a link to the website that describes the story of a man named Snorflina Quibbledew"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_links.adoc", question)
    assert "https://pppoooiiiuuu.org" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T179")
def test_adoc_tables(edp_helper, chatqa_api_helper):
    """Validate if tables are recognized in the adoc file"""
    # 1. Test tables in a standard format
    question = " What category does Flornax Quibit belong to?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_tables.adoc", question)
    assert "homeware" in response.lower(), UNRELATED_RESPONSE_MSG
    # 2. Test tables in csv format
    question = "What is the price for Myzterna Flux?"
    response = ask_question(chatqa_api_helper, question)
    assert "42" in response, UNRELATED_RESPONSE_MSG
    # 3. Test tables with merged cells
    question = "Give me a description of the product called 'Luminoid Krux'"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["compact", "light", "cube"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T180")
def test_adoc_source_code(edp_helper, chatqa_api_helper):
    """Put a code block in the adoc file and check if it is recognized"""
    question = ("What does the dockerfile set up? I refer to "
                "'Example Dockerfile with Explanations' document created by LipTanBuTan")
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_source_code.adoc", question)
    assert chatqa_api_helper.words_in_response(["flask", "python", "web"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T181")
def test_adoc_substitutions(edp_helper, chatqa_api_helper):
    """Check if substitutions are recognized in the text (*.adoc file)"""
    question = "What village did Plonka Nibbertwist live in?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_substitutions.adoc", question)
    assert "zumbleflick" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T262")
def test_logs_parsing_capability(edp_helper, chatqa_api_helper):
    """Check if chatbot can extract information from log files"""
    file = "system_logs.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

    question = ("How many WARNING logs came from the MonitoringService? "
                "These logs have the following string inside: '[MonitoringService] WARNING'")
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["3", "three"], response), UNRELATED_RESPONSE_MSG

    question = "At what time did the ERROR from InventoryService occur?"
    response = ask_question(chatqa_api_helper, question)
    assert "10:01:47" in response.lower(), UNRELATED_RESPONSE_MSG

    question = ("What was the last WARNING that comes from PaymentService? Provide the full log line. "
                "It should contain [PaymentService] string inside.")
    response = ask_question(chatqa_api_helper, question)
    assert "transaction tx1005 delayed due to network latency" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T264")
def test_reupload(edp_helper, chatqa_api_helper):
    """Check if re-uploading the same file and updated file works as expected"""
    file = "test_reupload_1.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

    question = "How many vinyl records does Frankooo have as of September 17, 2025?"
    response = ask_question(chatqa_api_helper, question)
    assert "187" in response, UNRELATED_RESPONSE_MSG

    # Re-upload the same file
    file = "test_reupload_1.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
    question = "How many vinyl records does Frankooo have as of September 17, 2025?"
    response = ask_question(chatqa_api_helper, question)
    assert "187" in response, UNRELATED_RESPONSE_MSG

    # Upload updated file
    file = "test_reupload_2.txt"  # updated file with different number of vinyl records
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
    question = "How many vinyl records does Frankooo have as of September 17, 2025?"
    response = ask_question(chatqa_api_helper, question)
    assert "212" in response, UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T249")
def test_similarity_search_with_siblings(edp_helper, chatqa_api_helper, fingerprint_api_helper):
    """
    Upload a file with a list of 20 elements.
    Ask a question that requires the entire list to be included in the answer.
    With retriever's search type set to 'similarity', expect the answer to be incomplete.
    Change the retriever's search type to 'similarity_with_siblings' and expect the answer to be complete.
    """

    current_parameters = fingerprint_api_helper.append_arguments("").json().get("parameters", {})
    original_k = current_parameters.get("k")
    original_search_type = current_parameters.get("search_type")
    if not original_k or not original_search_type:
        pytest.skip("Failed to get current retriever's parameters")

    file = "test_similarity_search_with_siblings.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
    question = "List 20 Principles for a Meaningful Life by Giorgiooo"

    try:
        if original_search_type != "similarity":
            fingerprint_api_helper.set_component_parameters("retriever", search_type="similarity", k=original_k)

        response = ask_question(chatqa_api_helper, question)
        assert "Stay humble" not in response, ("'Stay humble' is the last principle in the list. It should not be "
                                               "included in the answer when search_type='similarity'")

        # Change search type to similarity_with_siblings. Expect the response to be longer
        fingerprint_api_helper.set_component_parameters("retriever", search_type="similarity_search_with_siblings",
                                                        k=original_k)
        response = ask_question(chatqa_api_helper, question)
        assert "Stay humble" in response, "With similarity_with_siblings search type, the answer should be longer"
    finally:
        # Restore default parameters
        fingerprint_api_helper.set_component_parameters("retriever", search_type=original_search_type, k=original_k)


@allure.testcase("IEASG-T196")
def test_long_agenda_simple_questions(edp_helper, chatqa_api_helper):
    """
    This tests checks if chatbot can connect large pieces of information (events) to another one (events' days)
    This lightway part of the tests ask simple questions about event or time to see if information
    was identified and classified correctly.
    """
    file = "long-agenda.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

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


@allure.testcase("IEASG-T200")
def test_long_agenda_summary_questions(edp_helper, chatqa_api_helper):
    """
        This tests checks if chatbot can connect large pieces of information (events) to another one (events' days)
        This test verifies if chatbot can summarize all information related to a given day.
        """
    file = "long-agenda.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
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
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

    response_1_before = ask_question(chatqa_api_helper, question_1)
    assert chatqa_api_helper.words_in_response(expected_1_before, response_1_before), UNRELATED_RESPONSE_MSG

    response_2_before = ask_question(chatqa_api_helper, question_2)
    assert chatqa_api_helper.words_in_response(expected_2_before, response_2_before), UNRELATED_RESPONSE_MSG

    response_3_before = ask_question(chatqa_api_helper, question_3)
    assert chatqa_api_helper.words_in_response(expected_3_before, response_3_before), UNRELATED_RESPONSE_MSG

    with edp_helper.substitute_file("test_updated_document.txt", "test_updated_document-updated.txt"):
        edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

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
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
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
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file1))
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file2))

    question = "What is the total value of all Marianooo's balls for the game called Marianoball?"
    response = ask_question(chatqa_api_helper, question)
    assert "300" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T247")
def test_top_n(edp_helper, chatqa_api_helper, fingerprint_api_helper):
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

    file1 = "test_top_n_1.txt"
    file2 = "test_top_n_2.txt"
    question = "How many RC cars do Emanueleee and Raffaeleee have in total?"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file1))
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file2))

    try:
        fingerprint_api_helper.set_component_parameters("reranker", top_n=1)
        response = ask_question(chatqa_api_helper, question)
        assert "31" not in response.lower(), "only a single document should be used to answer the question"
        fingerprint_api_helper.set_component_parameters("reranker", top_n=3)
        response = ask_question(chatqa_api_helper, question)
        assert "31" in response.lower(), "3 documents should be used to answer the question"
    finally:
        # revert top_n back to original value
        fingerprint_api_helper.set_component_parameters("reranker", top_n=original_n)


def upload_and_ask_question(edp_helper, chatqa_api_helper, file, question=""):
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
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