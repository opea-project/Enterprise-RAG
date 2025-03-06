#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import constants
import inspect
import logging
import pytest
import requests
import os
import time
import uuid

logger = logging.getLogger(__name__)
IN_PROGRESS_STATUSES = ["uploaded", "processing", "dataprep", "embedding"]


@pytest.fixture(autouse=True)
def cleanup(edp_helper):
    yield
    logger.info("\nAttempting to clean up all items created during the test")
    files = edp_helper.list_files()
    for file in files.json():
        file_name = file["object_name"]
        if file_name.startswith("test_edp_"):
            if file["status"] in IN_PROGRESS_STATUSES:
                logger.info(f"Canceling in progress task: {file_name}")
                edp_helper.cancel_processing_task(file["id"])
            elif file["status"] == "ingested":
                logger.info(f"Removing file: {file_name}")
                response = edp_helper.generate_presigned_url(file["object_name"], "DELETE")
                edp_helper.delete_from_minio(response.json().get("url"))

    links = edp_helper.list_links()
    for link in links.json():
        if "test_edp_" in link["uri"]:
            logger.info(f"Removing link: {link['uri']}")
            edp_helper.delete_link(link["id"])


@allure.testcase("IEASG-T120")
def test_edp_list_files(edp_helper):
    """Check whether the list of files is returned correctly"""
    response = edp_helper.list_files()
    assert response.status_code == 200, f"Failed to list files. Response: {response.text}"
    logger.info(f"Files: {response.json()}")


@allure.testcase("IEASG-T121")
def test_edp_upload_to_minio(edp_helper):
    """Upload a file using presigned URL. Wait for the file to be in ingested state"""
    with edp_helper.temp_txt_file(size=0.001, prefix=method_name()) as temp_file:
        file_basename = os.path.basename(temp_file.name)
        response = edp_helper.generate_presigned_url(file_basename)
        assert response.status_code == 200, f"Failed to generate presigned URL. Response: {response.text}"
        response = edp_helper.upload_to_minio(temp_file.name, response.json().get("url"))
        assert response.status_code == 200, f"Failed to upload file to MinIO. Response: {response.text}"
        edp_helper.wait_for_file_upload(file_basename, "ingested", timeout=60)


@allure.testcase("IEASG-T122")
def test_edp_delete_from_minio(edp_helper):
    """Delete a file using presigned URL. Wait for the file to be removed from the list"""
    file = edp_helper.upload_test_file(size=0.001, prefix=method_name(), status="ingested", timeout=60)
    file_basename = file["object_name"]
    response = edp_helper.generate_presigned_url(file_basename, "DELETE")
    response = edp_helper.delete_from_minio(response.json().get("url"))
    assert response.status_code == 204, f"Failed to delete file from MinIO. Response: {response.text}"
    files = edp_helper.list_files()
    assert file_basename not in [item['object_name'] for item in files.json()], \
        f"File {file} is still in the list of files"


@allure.testcase("IEASG-T123")
def test_edp_huge_file_upload(edp_helper):
    """
    Create a temporary file of size 63MB (maximum allowed file size is 64MB)
    Upload and wait for the file to be ingested.
    """
    edp_helper.upload_test_file(size=63, prefix=method_name(), status="ingested", timeout=10800)


@allure.testcase("IEASG-T124")
def test_edp_cancel_task(edp_helper):
    """Upload a large file and cancel the processing task"""
    file = edp_helper.upload_test_file(size=10, prefix=method_name(), status="processing", timeout=180)
    response = edp_helper.cancel_processing_task(file["id"])
    assert response.status_code == 200, f"Failed to cancel processing task. Response: {response.text}"
    files = edp_helper.list_files()
    for file in files.json():
        if file["object_name"] == file:
            assert file["status"] == "canceled"
            assert file["job_message"] == "Processing task canceled"


@allure.testcase("IEASG-T125")
def test_edp_delete_file_during_ingestion(edp_helper):
    """Upload a file and delete it while it is being ingested. Expect status code 204"""
    file = edp_helper.upload_test_file(size=2, prefix=method_name(), status="processing", timeout=180)
    response = edp_helper.generate_presigned_url(file["object_name"], "DELETE")
    response = edp_helper.delete_from_minio(response.json().get("url"))
    assert response.status_code == 204, f"Failed to delete file from MinIO. Response: {response.text}"


@allure.testcase("IEASG-T126")
def test_edp_upload_unsupported_file(edp_helper):
    """Upload a file with an unsupported file type and check that it is in error state"""
    file = "unsupported_filetype.adoc"
    file_path = os.path.join(constants.TEST_FILES_DIR, file)
    response = edp_helper.generate_presigned_url(file)
    response = edp_helper.upload_to_minio(file_path, response.json().get("url"))
    assert response.status_code == 200, f"Failed to upload file to MinIO. Response: {response.text}"
    edp_helper.wait_for_file_upload(file, "error", timeout=60)


@allure.testcase("IEASG-T127")
def test_edp_upload_file_of_size_0(edp_helper):
    """Upload a file of size 0 and check that it is in error state"""
    edp_helper.upload_test_file(size=0, prefix=method_name(), status="error", timeout=60)


@allure.testcase("IEASG-T128")
def test_edp_reupload_file(edp_helper):
    """Upload a file, re-upload the same file (with additional content), and check that the file size has increased"""
    with edp_helper.temp_txt_file(size=0.01, prefix=method_name()) as temp_file:
        file_basename = os.path.basename(temp_file.name)
        response = edp_helper.generate_presigned_url(file_basename)
        edp_helper.upload_to_minio(temp_file.name, response.json().get("url"))
        first_upload = edp_helper.wait_for_file_upload(file_basename, "ingested")
        temp_file.write("additional data")
        temp_file.flush()
        response = edp_helper.generate_presigned_url(file_basename)
        edp_helper.upload_to_minio(temp_file.name, response.json().get("url"))
        second_upload = edp_helper.wait_for_file_upload(file_basename, "ingested")
        assert first_upload["size"] < second_upload["size"]


@allure.testcase("IEASG-T129")
def test_edp_reupload_file_after_deletion(edp_helper):
    """
    Upload a file, delete it, re-upload the same file (with additional content)
    and check that the file size has increased
    """
    with edp_helper.temp_txt_file(size=0.01, prefix=method_name()) as temp_file:
        file_basename = os.path.basename(temp_file.name)
        response = edp_helper.generate_presigned_url(file_basename)
        edp_helper.upload_to_minio(temp_file.name, response.json().get("url"))
        first_upload = edp_helper.wait_for_file_upload(file_basename, "ingested")

        response = edp_helper.generate_presigned_url(file_basename, "DELETE")
        edp_helper.delete_from_minio(response.json().get("url"))
        time.sleep(5)

        temp_file.write("additional data")
        temp_file.flush()
        response = edp_helper.generate_presigned_url(file_basename)
        edp_helper.upload_to_minio(temp_file.name, response.json().get("url"))
        second_upload = edp_helper.wait_for_file_upload(file_basename, "ingested")
        assert first_upload["size"] < second_upload["size"]


@allure.testcase("IEASG-T130")
def test_edp_cancel_nonexistent_task(edp_helper):
    """Cancel a task that does not exist. Expect status code 404"""
    response = edp_helper.cancel_processing_task(str(uuid.uuid4()))
    assert response.status_code == 404, f"Unexpected status code. Response: {response.text}"


@allure.testcase("IEASG-T131")
def test_edp_cancel_already_ingested_task(edp_helper):
    """Cancel a task that is already ingested. Expect status code 404"""
    file = edp_helper.upload_test_file(size=0.01, prefix=method_name(), status="ingested", timeout=60)
    response = edp_helper.cancel_processing_task(file["id"])
    assert response.status_code == 404, f"Unexpected status code. Response: {response.text}"


@allure.testcase("IEASG-T132")
def test_edp_list_links(edp_helper):
    """Check whether the list of links is returned correctly"""
    response = edp_helper.list_links()
    assert response.status_code == 200, f"Failed to list links. Response: {response.text}"
    try:
        logger.info(f"Links: {response.json()}")
    except requests.exceptions.JSONDecodeError:
        pytest.fail(f"Failed to decode JSON response. Response: {response.text}")


@allure.testcase("IEASG-T133")
def test_edp_upload_links(edp_helper):
    """Upload a couple of valid links and verify that they appear in the list of links"""
    links = [f"https://www.example.org/?test_edp_upload_links={uuid.uuid4()}",
             f"https://www.example.org/?test_edp_upload_links={uuid.uuid4()}"]
    response = edp_helper.upload_links({"links": links})
    assert response.status_code == 200

    try:
        links_response = edp_helper.list_links().json()
    except requests.exceptions.JSONDecodeError:
        pytest.fail(f"Failed to decode JSON response. Response: {response.text}")

    uploaded_uris = [item["uri"] for item in links_response]
    assert set(links).issubset(set(uploaded_uris)), \
        f"Not all links were uploaded successfully. Current links list: {response}"

    for link in links:
        edp_helper.wait_for_link_upload(link, "ingested", timeout=300)


@allure.testcase("IEASG-T134")
def test_edp_delete_link(edp_helper):
    """Upload a link and delete it. Verify that the link is no longer in the list of links"""
    link_to_delete = f"https://www.example.org/?test_edp_delete_links={uuid.uuid4()}"
    payload = {"links": [link_to_delete]}
    response = edp_helper.upload_links(payload)
    link_id = response.json().get("id")[0]
    edp_helper.wait_for_link_upload(link_to_delete, "ingested")
    response = edp_helper.delete_link(link_id)
    assert response.status_code == 200, f"Failed to delete link. Response: {response.text}"
    current_links_list = edp_helper.list_links()
    assert link_to_delete not in [item["uri"] for item in current_links_list.json()], \
        f"Link {link_to_delete} is still in the list of links"


@allure.testcase("IEASG-T135")
def test_edp_reupload_link_after_deletion(edp_helper):
    """Upload a link, delete it, and re-upload the same link"""
    # 1. Upload link
    link_to_reupload = f"https://www.example.org/?test_edp_reupload_link_after_deletion={uuid.uuid4()}"
    payload = {"links": [link_to_reupload]}
    response = edp_helper.upload_links(payload)
    link_id = response.json().get("id")
    edp_helper.wait_for_link_upload(link_to_reupload, "ingested")

    # 2. Delete link
    edp_helper.delete_link(link_id)

    # 3. Re-upload the same link
    response = edp_helper.upload_links(payload)
    assert response.status_code == 200, f"Failed to re-upload link. Response: {response.text}"
    edp_helper.wait_for_link_upload(link_to_reupload, "ingested")


@allure.testcase("IEASG-T136")
def test_edp_reupload_link(edp_helper):
    """Upload a link, and re-upload the same link"""
    # 1. Upload link
    link_to_reupload = f"https://www.example.org/?test_edp_reupload_link={uuid.uuid4()}"
    payload = {"links": [link_to_reupload]}
    edp_helper.upload_links(payload)
    edp_helper.wait_for_link_upload(link_to_reupload, "ingested")

    # 2. Re-upload the same link
    response = edp_helper.upload_links(payload)
    assert response.status_code == 200, f"Failed to re-upload link. Response: {response.text}"
    edp_helper.wait_for_link_upload(link_to_reupload, "ingested")


@allure.testcase("IEASG-T137")
def test_edp_upload_nonexistent_link(edp_helper):
    """Upload a link to a nonexistent website"""
    nonexistent_link = "https://some-nonexisting-webpage-12345.com"
    response = edp_helper.upload_links({"links": [nonexistent_link]})
    assert response.status_code == 200, f"Unexpected status code. Response: {response.text}"


@allure.testcase("IEASG-T138")
def test_edp_upload_invalid_body(edp_helper):
    """Upload a link with an invalid body"""
    response = edp_helper.upload_links({"invalid_body": "invalid"})
    assert response.status_code == 422, f"Unexpected status code. Response: {response.text}"
    response = edp_helper.upload_links({"link": []})
    assert response.status_code == 422, f"Unexpected status code. Response: {response.text}"
    response = edp_helper.upload_links({"link": ["not a link"]})
    assert response.status_code == 422, f"Unexpected status code. Response: {response.text}"


@allure.testcase("IEASG-T139")
def test_edp_delete_nonexistent_link(edp_helper):
    """Delete a link that does not exist"""
    response = edp_helper.delete_link("nonexistent_link_id")
    assert response.status_code == 400, f"Unexpected status code. Response: {response.text}"


@allure.testcase("IEASG-T38")
def test_edp_responsiveness_while_uploading_file(edp_helper):
    """
    Upload a file and periodically call dataprep and edp health check APIs
    Note: this test will take at least 2 minutes to complete
    """
    threshold = 120
    file = edp_helper.upload_test_file(size=10, prefix=method_name(), status="dataprep", timeout=300)

    logger.info("Starting to periodically call dataprep /v1/health_check API and edp /health API")
    counter = 0
    start_time = time.time()
    while time.time() < start_time + threshold:
        try:
            response = edp_helper.call_health_check_api("edp", {"app.kubernetes.io/name": "edp-dataprep"}, 9399)
            assert response.status_code == 200, "Got unexpected status code when calling dataprep health check API"
        except requests.exceptions.ReadTimeout:
            pytest.fail("Dataprep API is not responsive while the file is being uploaded")
        try:
            response = edp_helper.call_health_check_api("edp", {"app.kubernetes.io/name": "edp-backend"}, 5000,
                                                        "health")
            assert response.status_code == 200, "Got unexpected status code when calling edp health API"
        except requests.exceptions.ReadTimeout:
            pytest.fail("Edp API is not responsive while the file is being uploaded")

        logger.info(f"Response #{counter} after: {time.time() - start_time} seconds")
        time.sleep(1)
        counter += 1
    # Cancel task if not finished
    edp_helper.cancel_processing_task(file["id"])


def method_name():
    return f"{inspect.stack()[1].function}_"
