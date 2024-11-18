#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import concurrent.futures
import os
import pytest
import requests
import time
from tempfile import NamedTemporaryFile

CHUNK_SIZE = 512
CHUNK_OVERLAPPING = 64
TEST_FILES_DIR = "files/dataprep_upload"


@allure.testcase("IEASG-T43")
def test_dataprep_link_pass_many_websites(dataprep_api_helper):
    """
    Check if uploading many websites works correctly
    """
    links = ["https://google.com", "https://intel.com"]
    response = dataprep_api_helper.call_dataprep_upload_links(links)
    assert response.status_code == 200, "Invalid HTTP status code returned"


@allure.testcase("IEASG-T41")
def test_dataprep_link_nonexistent_website(dataprep_api_helper):
    """
    Expect status code 400 when uploading a link to a nonexistent website
    """
    website_link = ["https://some-nonexisting-webpage-12345.com"]
    response = dataprep_api_helper.call_dataprep_upload_links(website_link)
    assert response.status_code == 400, "Invalid HTTP status code returned"


@allure.testcase("IEASG-T40")
def test_dataprep_link_check_status_code_and_headers(dataprep_api_helper):
    """
    Check status code and headers in a simple, positive test case
    when passing a valid website link
    """
    website_link = "https://intel.com"
    response = dataprep_api_helper.call_dataprep_upload_links(website_link)
    content_type_header = response.headers.get("Content-Type")
    assert response.status_code == 200, "Invalid HTTP status code returned"
    assert content_type_header == "application/json", "Unexpected Content-Type header in response"


@allure.testcase("IEASG-T39")
def test_dataprep_huge_file_upload(dataprep_api_helper):
    """
    Create a temporary file of size 63MB (maximum allowed file size is 64MB)
    Upload and check status code
    """
    size_in_bytes = 63 * 1024 * 1024  # 63 MB file

    print("Creating a temporary file")
    with NamedTemporaryFile(delete=True, mode='w+') as temp_file:
        _fill_in_file(temp_file, size_in_bytes)
        response = dataprep_api_helper.call_dataprep_upload_file(temp_file.name)
        assert response.status_code == 200, \
            "Unexpected status code returned when invalid request is made to dataprep pipeline"


@allure.testcase("IEASG-T38")
def test_dataprep_responsiveness_while_uploading_file(dataprep_api_helper, generic_api_helper):
    """
    Upload a large file to dataprep. Check if it responds to other API calls in the meantime
    """
    size_in_bytes = 63 * 1024 * 1024 # 63 MB file
    with NamedTemporaryFile(delete=True, mode='w+') as temp_file:
        _fill_in_file(temp_file, size_in_bytes)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Execute file upload in the background
            exec_handler = executor.submit(dataprep_api_helper.call_dataprep_upload_file,
                                           temp_file.name)
            print("Starting to periodically call /v1/health_check API of dataprep service")
            counter = 0
            start_time = time.time()
            while counter < 60:
                try:
                    response = generic_api_helper.call_health_check_api("dataprep", "dataprep-svc", 9399)
                except requests.exceptions.ReadTimeout:
                    pytest.fail("Dataprep API is not responsive while the file is being uploaded")

                print(f"Response #{counter} after: {time.time() - start_time} seconds")
                assert response.status_code == 200, "Got unexpected status code"
                time.sleep(1)
                counter += 1
                if exec_handler.done():
                    print("Uploading file finished")
                    break

            # Wait for the upload to finish and get the result
            result = exec_handler.result()
            print(f"Upload finished with response: {result}")

        assert result.status_code == 200, "Unexpected status code returned"


@allure.testcase("IEASG-T37")
def test_dataprep_pass_invalid_request_body(dataprep_api_helper):
    """
    Pass invalid request when uploading a file. Expect status code 400
    """
    custom_body = {"unknonwn_field": ""}
    response = dataprep_api_helper.call_dataprep_upload_custom_body(custom_body)
    assert response.status_code == 400, \
        "Unexpected status code returned when invalid request was made to dataprep pipeline"


@allure.testcase("IEASG-T36")
def test_dataprep_pass_empty_fields_in_request_body(dataprep_api_helper):
    """
    Pass empty fields for the required parameters values. Expect status code 400
    """
    custom_body = {
        "files": [{
                "filename": "",
                "data64": ""
            }
        ]
    }
    response = dataprep_api_helper.call_dataprep_upload_custom_body(custom_body)
    assert response.status_code == 400, \
        "Invalid status code returned when empty parameters are passed to dataprep pipeline"


@allure.testcase("IEASG-T35")
def test_dataprep_all_supported_file_types(dataprep_api_helper):
    """
    Check if all the supported file types are uploaded successfully
    """
    failed_files = []
    for filename in os.listdir(TEST_FILES_DIR):
        file_path = os.path.join(TEST_FILES_DIR, filename)
        resp = dataprep_api_helper.call_dataprep_upload_file(file_path)
        if resp.status_code != 200:
            failed_files.append(filename)
    assert failed_files == [], f"Some of the files were not uploaded successfully: {failed_files}"


@allure.testcase("IEASG-T34")
def test_dataprep_response_status_code_and_header(dataprep_api_helper):
    """
    Check status code and headers in a simple, positive test case
    for uploading a file to dataprep pipeline
    """
    txt_file = "files/dataprep_upload/test_dataprep.txt"
    response = dataprep_api_helper.call_dataprep_upload_file(txt_file)
    content_type_header = response.headers.get("Content-Type")
    assert response.status_code == 200, "Invalid HTTP status code returned"
    assert content_type_header == "application/json", "Unexpected Content-Type header in response"


@allure.testcase("IEASG-T33")
def test_dataprep_chunk_overlapping(dataprep_api_helper):
    """
    Check if the uploaded text is properly split into chunks
    Check of the text inside the chunks overlap with each other
    """
    txt_file = "files/dataprep_upload/test_dataprep_long_text.txt"
    response = dataprep_api_helper.call_dataprep_upload_file(txt_file)
    response = response.json()
    docs = response.get("docs")

    # Check if the text was split into 4 chunks as expected
    # File has 1593 characters and CHUNK_SIZE=512
    assert len(docs) == 4, "Unexpected number of chunks"
    for doc in docs:
        assert len(doc.get("text")) <= CHUNK_SIZE

    # Check chunk overlapping
    for doc_number, doc in enumerate(docs):
        if doc_number == 0:
            continue
        beginning = doc.get("text")[0:CHUNK_OVERLAPPING]
        previous_doc_ending = docs[doc_number - 1].get("text")[-CHUNK_OVERLAPPING:]
        assert beginning == previous_doc_ending


def _fill_in_file(temp_file, size):
    """
    Write data to the temp file until we reach the desired size
    """
    chunk_size = 1024 * 1024
    current_size = 0 # Write in chunks of 1 MB
    while current_size < size:
        chunk = 'A' * chunk_size
        temp_file.write(chunk)
        current_size += chunk_size
        temp_file.flush()
    # Flush the file to ensure all data is written
    temp_file.flush()
    print(f"Temporary file created at: {temp_file.name}")
