#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

import constants
import os


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
    assert words_in_response(["door", "dimension"], response), UNRELATED_RESPONSE_MSG


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
    assert words_in_response(["marshfire", "dew"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T106")
def test_ppt_text_only(edp_helper, chatqa_api_helper):
    """*.ppt file learning capabilities (pure text inside the file)"""
    question = "How did Snizzleflap arrive in Fluffington?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.ppt", question)
    assert words_in_response(["sky", "cloud"], response), UNRELATED_RESPONSE_MSG


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
    assert words_in_response(["pie", "song", "conversations", "friend", "plan"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T109")
def test_tiff_text_only(edp_helper, chatqa_api_helper):
    """*.tiff file learning capabilities (pure text inside the file)"""
    question = "What was the name of Zanthroglid's famous creation?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.tiff", question)
    assert words_in_response(["clockwork", "duck"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T110")
def test_jpg_text_only(edp_helper, chatqa_api_helper):
    """*.jpg file learning capabilities (pure text inside the file)"""
    question = "What was Zorvultrix's rare ability?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jpg", question)
    assert words_in_response(["heal", "wound"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T111")
def test_jpeg_text_only(edp_helper, chatqa_api_helper):
    """*.jpeg file learning capabilities (pure text inside the file)"""
    question = "What was Frellor Tindrack's goal?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jpeg", question)
    assert words_in_response(["island", "find", "ilverden"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T112")
def test_png_text_only(edp_helper, chatqa_api_helper):
    """*.png file learning capabilities (pure text inside the file)"""
    question = "What did Squeeferplonk discover in the hidden cave?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.png", question)
    assert words_in_response(["crystal", "power"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T113")
def test_svg_text_only(edp_helper, chatqa_api_helper):
    """*.svg file learning capabilities (pure text inside the file)"""
    question = "What was Klythar Pindlebaum's profession?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.svg", question)
    assert words_in_response(["architect", "designer"], response), UNRELATED_RESPONSE_MSG


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
    assert words_in_response(["golden ", "dust", "strange", "sand", "cloth"], response),(
        UNRELATED_RESPONSE_MSG)


@allure.testcase("IEASG-T117")
def test_jsonl_text_only(edp_helper, chatqa_api_helper):
    """*.jsonl file learning capabilities (pure text inside the file)"""
    question = "What was Yulvar Dimspark's secret talent?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.jsonl", question)
    assert words_in_response(["manipulate ", "time", "rewind", "moments"], response), UNRELATED_RESPONSE_MSG


@allure.testcase("IEASG-T118")
def test_xml_text_only(edp_helper, chatqa_api_helper):
    """*.xml file learning capabilities (pure text inside the file)"""
    question = "What was Tressivorn Quindle known for in Bravenreach?"
    response = upload_and_ask_question(edp_helper, chatqa_api_helper, "story.xml", question)
    assert words_in_response(["brewed", "potion", "wound"], response), UNRELATED_RESPONSE_MSG


def upload_and_ask_question(edp_helper, chatqa_api_helper, file, question):
    # Upload file and wait for it to be ingested
    file_path = os.path.join(constants.TEST_FILES_DIR, file)
    response = edp_helper.generate_presigned_url(file)
    response = edp_helper.upload_to_minio(file_path, response.json().get("url"))
    assert response.status_code == 200
    edp_helper.wait_for_file_upload(file, "ingested", timeout=180)

    response = chatqa_api_helper.call_chatqa(question)
    assert response.status_code == 200, "Unexpected status code returned"
    response_text = chatqa_api_helper.format_response(response)
    print(f"ChatQA response: {response_text}")
    return response_text


def words_in_response(substrings, response):
    """Returns true if any of the substrings appear in the response strings"""
    response = response.lower()
    return any(substring in response for substring in substrings)
