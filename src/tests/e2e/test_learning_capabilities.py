#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
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
def test_txt(dataprep_api_helper, chatqa_api_helper):
    """*.txt file learning capabilities"""
    question = "How many cars commonly called MALUCH are registered in Gdansk?"
    response = upload_and_ask_question(dataprep_api_helper, chatqa_api_helper, "story.txt", question)
    assert "851" in response, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T56")
def test_docx_text_only(dataprep_api_helper, chatqa_api_helper):
    """*.docx file learning capabilities (pure text inside the file)"""
    question = "What was the name of the girl who decided to visit the old tree at the edge of the village?"
    response = upload_and_ask_question(dataprep_api_helper, chatqa_api_helper, "story.docx", question)
    assert "Asfehehehe" in response, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T54")
def test_pdf_text_only(dataprep_api_helper, chatqa_api_helper):
    """*.pdf file learning capabilities (pure text inside the file)"""
    question = "In the story about Intel's headquarters in Gdansk, what was found by Krystianooo?"
    response = upload_and_ask_question(dataprep_api_helper, chatqa_api_helper, "story.pdf", question)
    response_lower = response.lower()
    assert "door" in response_lower or "dimension" in response_lower, UNRELATED_RESPONSE_MSG


@pytest.mark.smoke
@allure.testcase("IEASG-T55")
def test_pptx_text_only(dataprep_api_helper, chatqa_api_helper):
    """*.pptx file learning capabilities (pure text inside the file)"""
    question = "In the story about validation team at Impelooo, what surprising things has AI started to write?"
    response = upload_and_ask_question(dataprep_api_helper, chatqa_api_helper, "story.pptx", question)
    assert "poetry" in response.lower(), UNRELATED_RESPONSE_MSG


def upload_and_ask_question(dataprep_api_helper, chatqa_api_helper, file, question):
    file_path = os.path.join(constants.TEST_FILES_DIR, file)
    upload_response = dataprep_api_helper.call_dataprep_upload_file(file_path)
    assert upload_response.status_code == 200, "Unexpected status code returned"

    response = chatqa_api_helper.call_chatqa(question)
    assert response.status_code == 200, "Unexpected status code returned"
    response_text = chatqa_api_helper.format_response(response)
    print(f"ChatQA response: {response_text}")
    return response_text
