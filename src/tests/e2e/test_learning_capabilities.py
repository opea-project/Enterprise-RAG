#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import constants
import logging
import os
import pytest
import time

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
    question = ("What qualifications do I need to meet when applying for the position of "
                "Cloud Solutions Developer Intern for AI RAG Application?")
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["jenkins", "terraform", "typescript"], response), (
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
    assert chatqa_api_helper.words_in_response(["broom", "waeather"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.skip(reason="Feature not implemented yet")
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
    question = "What is Trenvahir's profession?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_table_single_cell.docx", question)
    assert chatqa_api_helper.words_in_response(["clockmaker"], response), UNRELATED_RESPONSE_MSG
    # 2. Table with many cells
    question = "Who discovered a plant called Whisperfern Lucida?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "test_docx_table.docx", question)
    assert chatqa_api_helper.words_in_response(["kren", "talweir"], response), UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T165")
def test_docx_formatted_text(edp_helper, chatqa_api_helper):
    """*.docx file learning capabilities (with formatted text inside the file)"""
    # 1. Check if heading is recognized
    question = "Who is the girl called Lucifelle?"
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
    question = "What did people call Lunibelle Lucifelle, and why?"
    response = ask_question(chatqa_api_helper, question)
    assert chatqa_api_helper.words_in_response(["sound", "girl"], response), UNRELATED_RESPONSE_MSG
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
    question = "Give me a link to a top secret webstite called AAAFFFGGGKKK"
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
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story_to_be_deleted.txt", question)
    assert chatqa_api_helper.words_in_response(["nice", "forget", "remember"], response), UNRELATED_RESPONSE_MSG
    logger.debug("Sleeping to make sure the file is deleted")
    time.sleep(10)
    logger.debug("Asking question once again after file deletion")
    response = delete_and_ask_question(edp_helper, chatqa_api_helper, "story_to_be_deleted.txt", question)
    assert not chatqa_api_helper.words_in_response(["nice", "forget", "remember"], response), UNRELATED_RESPONSE_MSG


def delete_and_ask_question(edp_helper, chatqa_api_helper, file, question):
    response = edp_helper.generate_presigned_url(file, "DELETE")
    edp_helper.delete_file(response.json().get("url"))
    return ask_question(chatqa_api_helper, question)


def upload_and_ask_question(edp_helper, chatqa_api_helper, file, question):
    # Upload file and wait for it to be ingested
    file_path = os.path.join(constants.TEST_FILES_DIR, file)
    response = edp_helper.generate_presigned_url(file)
    response = edp_helper.upload_file(file_path, response.json().get("url"))
    assert response.status_code == 200
    edp_helper.wait_for_file_upload(file, "ingested", timeout=180)
    return ask_question(chatqa_api_helper, question)


def ask_question(chatqa_api_helper, question):
    """Ask a question to the chatbot and return the response"""
    response = chatqa_api_helper.call_chatqa(question)
    assert response.status_code == 200, "Unexpected status code returned"
    response_text = chatqa_api_helper.format_response(response)
    logger.info(f"ChatQA response: {response_text}")
    return response_text
