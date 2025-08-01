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


@pytest.fixture
def access_token(keycloak_helper):
    return keycloak_helper.get_access_token()


@pytest.mark.smoke
@allure.testcase("IEASG-T50")
def test_txt(edp_helper, chatqa_api_helper, access_token):
    """*.txt file learning capabilities"""
    question = "How many cars commonly called MALUCH are registered in Gdansk?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.txt", access_token, question)
    assert "851" in response, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T56")
def test_docx_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (pure text inside the file)"""
    question = "What was the name of the girl who decided to visit the old tree at the edge of the village?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.docx", access_token, question)
    assert "Asfehehehe" in response, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T54")
def test_pdf_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.pdf file learning capabilities (pure text inside the file)"""
    question = "In the story about Intel's headquarters in Gdansk, what was found by Krystianooo?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.pdf", access_token, question)
    assert chatqa_api_helper.words_in_response(["door", "dimension"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T55")
def test_pptx_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.pptx file learning capabilities (pure text inside the file)"""
    question = "In the story about validation team at Impelooo, what surprising things has AI started to write?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.pptx", access_token, question)
    assert "poetry" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T104")
def test_json_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.json file learning capabilities (pure text inside the file)"""
    question = "What is RagRag?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.json", access_token, question)
    assert "whale" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T105")
def test_doc_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.doc file learning capabilities (pure text inside the file)"""
    question = "What rare ingredient did Zephyrglint add to his potion during the lunar eclipse?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.doc", access_token, question)
    assert chatqa_api_helper.words_in_response(["marshfire", "dew"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T106")
def test_ppt_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.ppt file learning capabilities (pure text inside the file)"""
    question = "How did Snizzleflap arrive in Fluffington?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.ppt", access_token, question)
    assert chatqa_api_helper.words_in_response(["sky", "cloud"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T107")
def test_md_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.md file learning capabilities (pure text inside the file)"""
    question = "What was Crinklebonk made of?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.md", access_token, question)
    assert "paper" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T108")
def test_html_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.html file learning capabilities (pure text inside the file)"""
    question = ("What are some of the things that people in the town of Glimphtoodle began to forget "
                "as the strange phenomenon progressed?")
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.html", access_token, question)
    assert chatqa_api_helper.words_in_response(["pie", "song", "conversations", "friend", "plan"], response),(
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T109")
def test_tiff_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.tiff file learning capabilities (pure text inside the file)"""
    question = "What was the name of Zanthroglid's famous creation?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.tiff", access_token, question)
    assert chatqa_api_helper.words_in_response(["clockwork", "duck"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T110")
def test_jpg_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.jpg file learning capabilities (pure text inside the file)"""
    question = "What was Zorvultrix's rare ability?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jpg", access_token, question)
    assert chatqa_api_helper.words_in_response(["heal", "wound"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T111")
def test_jpeg_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.jpeg file learning capabilities (pure text inside the file)"""
    question = "What was Frellor Tindrack's goal?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jpeg", access_token, question)
    assert chatqa_api_helper.words_in_response(["island", "find", "ilverden"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T112")
def test_png_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.png file learning capabilities (pure text inside the file)"""
    question = "What did Squeeferplonk discover in the hidden cave?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.png", access_token, question)
    assert chatqa_api_helper.words_in_response(["crystal", "power"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T113")
def test_svg_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.svg file learning capabilities (pure text inside the file)"""
    question = "What was Klythar Pindlebaum's profession?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.svg", access_token, question)
    assert chatqa_api_helper.words_in_response(["architect", "designer"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T114")
def test_xlsx_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.xlsx file learning capabilities (pure text inside the file)"""
    question = "What was Zerlith Quarble's profession or passion?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xlsx", access_token, question)
    assert "alchemist" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T115")
def test_xls_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.xls file learning capabilities (pure text inside the file)"""
    question = "What did Brindle Sprocketwick create that was extraordinary?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xls", access_token, question)
    assert "clock" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T116")
def test_csv_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.csv file learning capabilities (pure text inside the file)"""
    question = "What did the Sandweaver create when it malfunctioned?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.csv", access_token, question)
    assert chatqa_api_helper.words_in_response(["golden ", "dust", "strange", "sand", "cloth"], response), (
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T117")
def test_jsonl_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.jsonl file learning capabilities (pure text inside the file)"""
    question = "What was Yulvar Dimspark's secret talent?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jsonl", access_token, question)
    assert chatqa_api_helper.words_in_response(["manipulate ", "time", "rewind", "moments"], response), (
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T118")
def test_xml_text_only(edp_helper, chatqa_api_helper, access_token):
    """*.xml file learning capabilities (pure text inside the file)"""
    question = "What was Tressivorn Quindle known for in Bravenreach?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xml", access_token, question)
    assert chatqa_api_helper.words_in_response(["brewed", "potion", "wound"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T162")
def test_docx_multi_paragraph(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (multiple paragraphs inside the file)"""
    question = ("How many people work in the team that the Cloud Solutions Developer Intern for AI RAG Application "
                "candidate joins?")
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "Front-end Intern_example.docx", access_token, question)
    assert chatqa_api_helper.words_in_response(["12", "13"], response), UNRELATED_RESPONSE_MSG
    question = "What is the name of the group offering the Cloud Solutions Developer Intern for AI RAG position?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["dcai", "ecosystem"], response), UNRELATED_RESPONSE_MSG
    question = ("What qualifications do I need to meet when applying for the position of "
                "Cloud Solutions Developer Intern for AI RAG Application?")
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["jenkins", "terraform", "typescript"], response), (
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T163")
def test_docx_with_images(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (with images and text surrounding the images)"""
    question = "What was Vellimer doing when the storm occurred?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story_docx_pictures.docx", access_token, question)
    assert chatqa_api_helper.words_in_response(["roof", "rod", "waiting"], response), UNRELATED_RESPONSE_MSG
    question = ("How does the village of Fernloft remember Vellimer today?"
                "What signs make them think he might still be around? ")
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["broom", "weather"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.skip(reason="Feature not implemented yet")
@allure.testcase("IEASG-T164")
def test_get_context_from_filename(edp_helper, chatqa_api_helper, access_token):
    """Upload a file with a unique name. Ask a question related to the file name to verify if it has been ingested"""
    question = "Which company does Zerilwyn Nactroske currently work for?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "Zerilwyn Nactroske - CV.docx", access_token, question)
    assert chatqa_api_helper.words_in_response(["deepmind"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T166")
def test_docx_tables(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (with tables inside the file)"""
    # 1. Table with a single cell
    question = "What is Trenvahir's profession?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_table_single_cell.docx", access_token, question)
    assert chatqa_api_helper.words_in_response(["clockmaker"], response), UNRELATED_RESPONSE_MSG
    # 2. Table with many cells
    question = "Who discovered a plant called Whisperfern Lucida?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_table.docx", access_token, question)
    assert chatqa_api_helper.words_in_response(["kren", "talweir"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T165")
def test_docx_formatted_text(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (with formatted text inside the file)"""
    # 1. Check if heading is recognized
    question = "Who is the girl called Lucifelle?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_formatted_text.docx", access_token, question)
    assert chatqa_api_helper.words_in_response(["lunibelle", "sound"], response), UNRELATED_RESPONSE_MSG
    # 2. Test italic text
    question = "In the story about Lunibelle Lucifelle, what did the girl loved to collect?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["sound"], response), UNRELATED_RESPONSE_MSG
    # 3. Test bold text
    question = "How did the villagers perceive Lunibelle Lucifelle?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["strange", "kind"], response), UNRELATED_RESPONSE_MSG
    # 4. Test underline text
    question = "What did people call Lunibelle Lucifelle, and why?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["sound girl"], response), UNRELATED_RESPONSE_MSG
    # 5. Test color text
    question = "What did Lunibelle Lucifelle do when she reached the center of the square?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["box", "whisper", "sky"], response), UNRELATED_RESPONSE_MSG
    # 6. Test text highlighted in yellow
    question = "What sound did the rain make in the story about Lunibelle Lucifelle?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["clapped", "hands"], response), UNRELATED_RESPONSE_MSG
    # 7. Test big text
    question = "How do people react when they hear the wind play a soft tune in the story about Lunibelle Lucifelle?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["smile"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T167")
def test_docx_with_hyperlink(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (with hyperlinks inside the file)"""
    question = "Give me a link to a website called AAAFFFGGGKKK"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_with_hyperlink.docx", access_token, question)
    assert "aaafffgggkkk-top-secret.com" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T168")
def test_docx_numbered_and_bulleted_lists(edp_helper, chatqa_api_helper, access_token):
    """*.docx file learning capabilities (with numbered and bulleted lists inside the file)"""
    # 1. Test bulleted list
    question = "When was the document 'YYTTRREEWWQQ' created at?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_numbered_and_bulleted_lists.docx", access_token, question)
    assert "17" in response.lower(), UNRELATED_RESPONSE_MSG
    # 2. Test numbered list
    question = "What happens when the 'vanishing algorithm' is executed in a closed environment?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["0.43", "0,43"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T169")
def test_content_is_forgotten_after_file_deletion(edp_helper, chatqa_api_helper, access_token):
    """Verify if the content is actually forgotten after file deletion"""
    question = "What did the note say that Zenvorlith Marnqueeble left when he disappeared?"
    file_name = "story_to_be_deleted.txt"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, file_name, access_token, question)
    assert chatqa_api_helper.words_in_response(["nice", "forget", "remember"], response), UNRELATED_RESPONSE_MSG
    response = delete_file(edp_helper, os.path.join(TEST_FILES_DIR, file_name))
    assert response.status_code == 204, f"Failed to delete file. Response: {response.text}"
    logger.debug("Sleeping to make sure the file is deleted")
    time.sleep(10)
    logger.debug("Asking question once again after file deletion")
    response = ask_question(chatqa_api_helper, access_token, question)
    assert not chatqa_api_helper.words_in_response(["nice", "forget", "remember"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T176")
def test_adoc_basic(edp_helper, chatqa_api_helper, access_token):
    """Validate basic *.adoc files support and learning capabilities"""
    # 1. Test lists
    question = "What did Grendal Nuvrick see when he woke up?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.adoc", access_token, question)
    assert "squirrel" in response.lower(), UNRELATED_RESPONSE_MSG

    # 2. Test titles
    question = "What are the titles in the story about Grendal Nuvrick?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["strange", "end"], response), UNRELATED_RESPONSE_MSG

    # 3. Text formatting
    question = "What did Grendal Nuvrick say when he saw the squirrel?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["not", "normal"], response), UNRELATED_RESPONSE_MSG
    question = "What did Grendal Nuvrick say when he opened the door and smiled?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["think", "stay"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T177")
def test_adoc_recognized_as_troff_mime_type(edp_helper, chatqa_api_helper, access_token):
    """
    Upload a file with 'text/troff' mime type.
    Check if the file is recognized as adoc.
    Ask a question related to the content of the file.
    """
    question = " What category does Flornax Quibit belong to?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_troff_mime_type.adoc", access_token, question)
    assert "homeware" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T178")
def test_adoc_links(edp_helper, chatqa_api_helper, access_token):
    """Check if links are properly extracted from the adoc file"""
    question = "Give me a link to the website that describes the story of a man named Snorflina Quibbledew"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_links.adoc", access_token, question)
    assert "https://pppoooiiiuuu.org" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T179")
def test_adoc_tables(edp_helper, chatqa_api_helper, access_token):
    """Validate if tables are recognized in the adoc file"""
    # 1. Test tables in a standard format
    question = " What category does Flornax Quibit belong to?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_tables.adoc", access_token, question)
    assert "homeware" in response.lower(), UNRELATED_RESPONSE_MSG
    # 2. Test tables in csv format
    question = "What is the price for Myzterna Flux?"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert "42" in response, UNRELATED_RESPONSE_MSG
    # 3. Test tables with merged cells
    question = "Give me a description of the product called 'Luminoid Krux'"
    response = ask_question(chatqa_api_helper, access_token, question)
    assert chatqa_api_helper.words_in_response(["compact", "light", "cube"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T180")
def test_adoc_source_code(edp_helper, chatqa_api_helper, access_token):
    """Put a code block in the adoc file and check if it is recognized"""
    question = ("What does the dockerfile set up? I refer to "
                "'Example Dockerfile with Explanations' document created by LipTanBuTan")
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_source_code.adoc", access_token, question)
    assert chatqa_api_helper.words_in_response(["flask", "python", "web"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T181")
def test_adoc_substitutions(edp_helper, chatqa_api_helper, access_token):
    """Check if substitutions are recognized in the text (*.adoc file)"""
    question = "What village did Plonka Nibbertwist live in?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_adoc_substitutions.adoc", access_token, question)
    assert "zumbleflick" in response.lower(), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T196")
def test_long_agenda_simple_questions(edp_helper, chatqa_api_helper, access_token):
    """
    This tests checks if chatbot can connect large pieces of information (events) to another one (events' days)
    This lightway part of the tests ask simple questions about event or time to see if information
    was identified and classified correctly.
    """
    file = "long-agenda.txt"
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

    with (allure.step("Ask about time of event")):
        question = "When is the lunch break on Day 2?"
        response = ask_question(chatqa_api_helper, access_token, question)
        assert chatqa_api_helper.words_in_response(
            [
                "12:00 PM - 01:00 PM",
                "from 12:00 PM to 01:00 PM",
            ],
            response), UNRELATED_RESPONSE_MSG

    with allure.step("Ask about event happening once"):
        question = "When are awards ceremony"
        response = ask_question(chatqa_api_helper, access_token, question)
        assert chatqa_api_helper.all_words_in_response(["day 2", "07:00 PM", "08:30 PM"], response), UNRELATED_RESPONSE_MSG

    with allure.step("Ask about event happening both days"):
        question = "When are Scrimmage Games?"
        response = ask_question(chatqa_api_helper, access_token, question)
        assert chatqa_api_helper.all_words_in_response(["day 1", "day 2"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T200")
def test_long_agenda_summary_questions(edp_helper, chatqa_api_helper, access_token):
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
        response = ask_question(chatqa_api_helper, access_token, question)
        assert chatqa_api_helper.all_words_in_response(required_mentions, response), UNRELATED_RESPONSE_MSG

@allure.testcase("IEASG-T199")
def test_updated_file(edp_helper, chatqa_api_helper, access_token):
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

    response_1_before = ask_question(chatqa_api_helper, access_token, question_1)
    assert chatqa_api_helper.words_in_response(expected_1_before, response_1_before), UNRELATED_RESPONSE_MSG

    response_2_before = ask_question(chatqa_api_helper, access_token, question_2)
    assert chatqa_api_helper.words_in_response(expected_2_before, response_2_before), UNRELATED_RESPONSE_MSG

    response_3_before = ask_question(chatqa_api_helper, access_token, question_3)
    assert chatqa_api_helper.words_in_response(expected_3_before, response_3_before), UNRELATED_RESPONSE_MSG

    with edp_helper.substitute_file("test_updated_document.txt", "test_updated_document-updated.txt"):
        edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))

        response_1_after = ask_question(chatqa_api_helper, access_token, question_1)
        assert chatqa_api_helper.words_in_response(expected_1_after, response_1_after), UNRELATED_RESPONSE_MSG

        response_2_after = ask_question(chatqa_api_helper, access_token, question_2)
        assert chatqa_api_helper.words_in_response(expected_2_after, response_2_after), UNRELATED_RESPONSE_MSG

        response_3_after = ask_question(chatqa_api_helper, access_token, question_3)
        assert chatqa_api_helper.words_in_response(expected_3_after, response_3_after), UNRELATED_RESPONSE_MSG


def upload_and_ask_question(edp_helper, chatqa_api_helper, file, token="", question=""):
    edp_helper.upload_file_and_wait_for_ingestion(os.path.join(TEST_FILES_DIR, file))
    return ask_question(chatqa_api_helper, token, question)


def ask_question(chatqa_api_helper, token="", question=""):
    """Ask a question to the chatbot and return the response"""
    response = chatqa_api_helper.call_chatqa_through_apisix(token, question)
    assert response.status_code == 200, "Unexpected status code returned"
    response_text = chatqa_api_helper.format_response(response)
    logger.info(f"ChatQA response: {response_text}")
    return response_text


def delete_file(edp_helper, file):
    response = edp_helper.generate_presigned_url(file, "DELETE")
    return edp_helper.delete_file(response.json().get("url"))