#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import os
import pytest

from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)

_oidc = cfg.get("keycloak", {}).get("oidc", {})
if not all(_oidc.get(k) for k in ("endpoint", "alias", "client_id", "tenant_id", "client_secret")):
    pytestmark = pytest.mark.skip(reason="SharePoint OIDC configuration is not fully set (keycloak.oidc.*)")

DEFAULT_SP_SITE = "erag-test-site-all"

SHAREPOINT_TEST_SITES = [
    DEFAULT_SP_SITE,
    "erag-test-site-user",
    "erag-test-site-admin",
]

_rbac_enabled = cfg.get("edp", {}).get("rbac", {}).get("enabled", False)


def _cleanup_sharepoint_sites(sharepoint_helper, edp_helper):
    """Delete all files from all SharePoint test sites and sync changes."""
    for site in SHAREPOINT_TEST_SITES:
        try:
            files = sharepoint_helper.list_site_files(site_name=site)
            for file in files:
                file_name = file.get("name")
                if not file_name:
                    continue
                try:
                    sharepoint_helper.delete_file_from_site(site_name=site, file_name=file_name)
                    logger.info(f"Cleanup: deleted '{file_name}' from site '{site}'")
                except Exception as e:
                    logger.warning(f"Cleanup: failed to delete '{file_name}' from site '{site}': {e}")
        except Exception as e:
            logger.warning(f"Cleanup: failed to list files for site '{site}': {e}")

    try:
        sync_response = edp_helper.sync_sharepoint()
        logger.info(f"Cleanup: SharePoint sync triggered. Status: {sync_response.status_code}")
    except Exception as e:
        logger.warning(f"Cleanup: failed to trigger SharePoint sync: {e}")


@pytest.fixture(scope="session", autouse=True)
def cleanup_sharepoint_files(sharepoint_helper, edp_helper):
    """Delete all files from all SharePoint test sites before and after the entire test suite."""
    _cleanup_sharepoint_sites(sharepoint_helper, edp_helper)
    yield
    _cleanup_sharepoint_sites(sharepoint_helper, edp_helper)


@pytest.fixture(scope="session", autouse=True)
def restore_connected_sites(edp_helper):
    """Save connected sites before the test suite and restore them after."""
    response = edp_helper.list_sites()
    original_sites = {site["name"] for site in response.json().get("sites", [])}
    logger.info(f"Connected sites before test suite: {original_sites}")

    yield

    response = edp_helper.list_sites()
    current_sites = {site["name"] for site in response.json().get("sites", [])}
    logger.info(f"Connected sites after test suite: {current_sites}")

    # Disconnect sites that were added during tests
    sites_to_disconnect = current_sites - original_sites
    for site_name in sites_to_disconnect:
        try:
            edp_helper.disconnect_site(site_name)
            logger.info(f"Restore: disconnected '{site_name}'")
        except Exception as e:
            logger.warning(f"Restore: failed to disconnect '{site_name}': {e}")

    # Reconnect sites that were removed during tests
    sites_to_reconnect = original_sites - current_sites
    for site_name in sites_to_reconnect:
        try:
            edp_helper.connect_site(site_name)
            logger.info(f"Restore: reconnected '{site_name}'")
        except Exception as e:
            logger.warning(f"Restore: failed to reconnect '{site_name}': {e}")


@allure.testcase("IEASG-T523")
def test_sp_connect_site(edp_helper):
    """Verify connecting a new site and connecting the same site again"""
    # Ensure site not connected
    edp_helper.disconnect_site(DEFAULT_SP_SITE)

    # Positive scenario - connect new site
    response = edp_helper.connect_site(DEFAULT_SP_SITE)
    assert response.status_code == 201, f"Failed to connect site. Response: {response.text}"
    logger.info(f"Site connected: {response.json()}")
    sites = edp_helper.list_sites()
    assert any(site.get("name") == DEFAULT_SP_SITE for site in sites.json().get("sites", [])), "Connected site not found in the list of sites"

    # Connect the same site again
    response = edp_helper.connect_site(DEFAULT_SP_SITE)
    assert response.status_code == 409


@allure.testcase("IEASG-T525")
def test_sp_connect_nonexistent_site(edp_helper):
    """Verify that connecting a nonexistent SharePoint site returns 404"""
    response = edp_helper.connect_site("this-site-does-not-exist-at-all")
    assert response.status_code == 404, \
        f"Expected 404 for nonexistent site, but got {response.status_code}: {response.text}"


@allure.testcase("IEASG-T524")
def test_sp_disconnect_site(edp_helper):
    """Verify disconnecting an existing site and disconnecting the same site again"""
    # Ensure site is connected before disconnecting
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Retrieve site ID
    site_id = edp_helper.get_site_id_by_name(DEFAULT_SP_SITE)

    # Positive scenario - disconnect existing site
    response = edp_helper.disconnect_site(DEFAULT_SP_SITE)

    assert response.status_code == 200, f"Failed to disconnect site. Response: {response.text}"
    sites = edp_helper.list_sites()
    assert not any(site.get("name") == DEFAULT_SP_SITE for site in sites.json().get("sites", [])), "Disconnected site still found in the list of sites"

    # Disconnect the same site again - should return 404 as it's already disconnected
    response = edp_helper.disconnect_site(DEFAULT_SP_SITE, site_id)
    assert response.status_code == 404


@allure.testcase("IEASG-T526")
def test_sp_disconnect_nonexistent_site(edp_helper):
    """Verify that disconnecting a nonexistent SharePoint site returns 404"""
    response = edp_helper.disconnect_site("this-site-does-not-exist-at-all")
    assert response.status_code == 404, \
        f"Expected 404 for nonexistent site, but got {response.status_code}: {response.text}"


@allure.testcase("IEASG-T528")
def test_sp_list_sites(edp_helper):
    """Ensure list_sites API call completes without failure"""
    response = edp_helper.list_sites()
    assert response.status_code == 200, f"Failed to list Sharepoint sites. Response: {response.text}"
    logger.info(f"Sites: {response.json()}")


@allure.testcase("IEASG-T527")
@pytest.mark.skipif(_rbac_enabled, reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test")
def test_sp_add_file_via_edp(edp_helper, sharepoint_helper, chatqa_api_helper):
    """Verify adding a file to the connected site using EDP API and checking its presence using Microsoft Graph APII"""
    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload file using EDP API
    file = "test_sp_add_file_via_edp.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file)
    response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, file_path)
    assert response.status_code in (200, 201), f"Failed to upload file via EDP SharePoint API. Response: {response.text}"

    # Sync changes
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"

    # Wait for the file to be ingested into EDP
    file = edp_helper.wait_for_file_upload(file, "ingested", timeout=120)

    # Verify the file is present in SharePoint using Microsoft Graph API
    file_basename = os.path.basename(file["object_name"])
    files = sharepoint_helper.list_site_files(site_name=DEFAULT_SP_SITE)
    assert any(file.get("name") == file_basename for file in files), f"Uploaded file not found in the list of site files. List: {files}"

    # Ask a related question to the file to verify it's properly ingested and indexed
    question = "How many Soviet watches sets does Migueloooo have?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "362" in response_text, f"Unexpected ChatQA response: {response_text}"


@allure.testcase("IEASG-T529")
@pytest.mark.skipif(_rbac_enabled, reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test")
def test_sp_add_file_via_sharepoint(edp_helper, sharepoint_helper, chatqa_api_helper):
    """Verify adding a file directly to SharePoint site and checking it gets ingested into EDP"""
    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload file to Sharepoint
    file = "test_sp_add_file_via_sharepoint.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file)
    result = sharepoint_helper.upload_file_to_site(site_name=DEFAULT_SP_SITE, file_path=file_path)
    logger.info(f"File uploaded to SharePoint: {result}")

    # Sync changes
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"

    # Verify the file gets ingested into EDP
    file_name = os.path.basename(file_path)
    file = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file, f"File '{file_name}' was not ingested into EDP"
    assert file_name in file.get("object_name", ""), \
        f"Unexpected object name in EDP: {file.get('object_name')}"

    # Ask a related question to the file to verify it's properly ingested and indexed
    question = "How many LEGO sets does Marcelinoooo have?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "7592" in response_text, f"Unexpected ChatQA response: {response_text}"


@allure.testcase("IEASG-T530")
@pytest.mark.skipif(_rbac_enabled, reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test")
def test_sp_delete_file_via_edp(edp_helper, sharepoint_helper, chatqa_api_helper):
    """Verify deleting a file via EDP API removes it from SharePoint and the chatbot forgets its content"""
    file_name = "test_sp_delete_file_via_edp.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file_name)

    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload file via EDP SharePoint API
    response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, file_path)
    assert response.status_code in (200, 201), f"Failed to upload file via EDP SharePoint API. Response: {response.text}"

    # Sync and wait for ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file_info, f"File '{file_name}' was not ingested into EDP"
    object_name = file_info.get("object_name")

    # Delete the file via EDP SharePoint API
    response = edp_helper.remove_from_sharepoint(DEFAULT_SP_SITE, object_name)
    assert response.status_code in (200, 204), f"Failed to delete file via EDP SharePoint API. Response: {response.text}"

    # Sync and wait until the file is no longer present in EDP
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    edp_helper.wait_for_file_deletion(object_name)

    # Verify the file is no longer present in SharePoint
    files = sharepoint_helper.list_site_files(site_name=DEFAULT_SP_SITE)
    assert not any(f.get("name") == file_name for f in files), \
        f"Deleted file '{file_name}' still found in SharePoint. Files: {files}"

    # Ask a related question - chatbot should not mention "910"
    question = "How many Ekstraklasa match tickets does Sofiaaaa have?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "910" not in response_text, f"Chatbot still mentions '910' after file deletion: {response_text}"


@allure.testcase("IEASG-T531")
@pytest.mark.skipif(_rbac_enabled, reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test")
def test_sp_delete_file_via_sharepoint(edp_helper, sharepoint_helper, chatqa_api_helper):
    """Verify deleting a file via SharePoint API removes it from EDP and chatbot forgets its content"""
    file_name = "test_sp_delete_file_via_sharepoint.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file_name)

    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload file via EDP SharePoint API
    response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, file_path)
    assert response.status_code in (200, 201), f"Failed to upload file via EDP SharePoint API. Response: {response.text}"

    # Sync and wait for ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file_info, f"File '{file_name}' was not ingested into EDP"
    object_name = file_info.get("object_name")

    # Delete the file via SharePoint API
    sharepoint_helper.delete_file_from_site(site_name=DEFAULT_SP_SITE, file_name=file_name)

    # Ask a related question - chatbot should mention "539" because synchronization has not happened yet
    question = "How many refrigerator magnets does Giuliaaaa own?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (before deletion): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "539" in response_text, f"Chatbot did not mention '539' before file deletion: {response_text}"

    # Synchronize SharePoint changes into EDP
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"

    # Wait until file is no longer present in EDP
    edp_helper.wait_for_file_deletion(object_name)

    # Ask a related question - chatbot should no longer mention "539"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (after deletion): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "539" not in response_text, f"Chatbot still mentions '539' after file deletion: {response_text}"


@allure.testcase("IEASG-T532")
def test_sp_add_file_to_disconnected_site(edp_helper):
    """Verify that uploading a file to a SharePoint bucket is rejected when the site is disconnected"""

    # Connect to site to get site ID, then disconnect it to simulate the scenario of uploading to a disconnected site
    edp_helper.connect_site(DEFAULT_SP_SITE)
    site_id = edp_helper.get_site_id_by_name(DEFAULT_SP_SITE)
    edp_helper.disconnect_site(DEFAULT_SP_SITE)

    # Attempt to upload a file to the disconnected site
    with edp_helper.temp_txt_file(size=1, prefix="test_sp_add_file_to_disconnected_site") as temp_file:
        response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, temp_file.name, site_id)
        logger.info(f"Upload response: {response.status_code} - {response.text}")
        assert response.status_code == 404, \
            f"Expected upload to be rejected for disconnected site, but got status {response.status_code}: {response.text}"


@allure.testcase("IEASG-T533")
def test_sp_add_file_to_nonexistent_site(edp_helper):
    """Verify that uploading a file to a completely unknown/invented site is rejected"""
    nonexistent_site = "this-site-does-not-exist-at-all"
    site_id = "00000000-0000-0000-0000-000000000000"

    with edp_helper.temp_txt_file(size=1, prefix="test_sp_add_file_to_nonexistent_site") as temp_file:
        response = edp_helper.upload_to_sharepoint(nonexistent_site, temp_file.name, site_id)
        logger.info(f"Upload response: {response.status_code} - {response.text}")
        assert response.status_code not in (200, 201), \
            f"Expected upload to be rejected for nonexistent site, but got status {response.status_code}: {response.text}"


@allure.testcase("IEASG-T541")
def test_sp_get_file_url(edp_helper):
    """Verify that a file uploaded to SharePoint can be retrieved via the file-url API and returns a valid URL"""
    file_name = "test_sp_add_file_via_edp.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file_name)

    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload file via EDP SharePoint API
    response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, file_path)
    assert response.status_code in (200, 201), f"Failed to upload file via EDP SharePoint API. Response: {response.text}"

    # Sync and wait for ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file_info, f"File '{file_name}' was not ingested into EDP"
    object_name = file_info.get("object_name")

    # Get file URL via EDP API
    response = edp_helper.get_file_url(DEFAULT_SP_SITE, object_name)
    assert response.status_code == 200, f"Failed to get file URL. Response: {response.text}"
    file_url = response.json().get("url")
    assert file_url, f"File URL not found in response: {response.json()}"
    logger.info(f"File URL: {file_url}")

    # Verify that it is a valid URL
    assert file_url.startswith("https://"), f"Invalid file URL: {file_url}"
    assert "sharepoint.com" in file_url, f"File URL does not point to SharePoint: {file_url}"


@allure.testcase("IEASG-T542")
def test_sp_get_file_url_negative(edp_helper):
    """Verify that get_file_url returns error responses for invalid inputs"""

    # Ensure site is connected for some of the scenarios
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Scenario 1: Nonexistent site name
    response = edp_helper.get_file_url("this-site-does-not-exist-at-all", "Documents/some_file.txt")
    logger.info(f"Nonexistent site response: {response.status_code} - {response.text}")
    assert response.status_code == 404, \
        f"Expected error for nonexistent site, but got {response.status_code}: {response.text}"

    # Scenario 2: Valid site, nonexistent object name
    response = edp_helper.get_file_url(DEFAULT_SP_SITE, "Documents/nonexistent_file_abc123.txt")
    logger.info(f"Nonexistent object response: {response.status_code} - {response.text}")
    assert response.status_code == 404, \
        f"Expected error for nonexistent object, but got {response.status_code}: {response.text}"

    # Scenario 3: Empty site name
    response = edp_helper.get_file_url("", "Documents/some_file.txt")
    logger.info(f"Empty site name response: {response.status_code} - {response.text}")
    assert response.status_code == 400, \
        f"Expected error for empty site name, but got {response.status_code}: {response.text}"

    # Scenario 4: Empty object name
    response = edp_helper.get_file_url(DEFAULT_SP_SITE, "")
    logger.info(f"Empty object name response: {response.status_code} - {response.text}")
    assert response.status_code == 400, \
        f"Expected error for empty object name, but got {response.status_code}: {response.text}"

    # Scenario 5: Both empty
    response = edp_helper.get_file_url("", "")
    logger.info(f"Both empty response: {response.status_code} - {response.text}")
    assert response.status_code == 400, \
        f"Expected error for both empty params, but got {response.status_code}: {response.text}"
