#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import os
import shutil
import tempfile
import uuid

import pytest

from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)

_oidc = cfg.get("keycloak", {}).get("oidc", {})
if not all(_oidc.get(k) for k in ("endpoint", "alias", "client_id", "tenant_id", "client_secret")):
    _msg = ("SharePoint OIDC configuration is not fully set (keycloak.oidc.*). "
            "Ensure endpoint, alias, client_id, tenant_id, and client_secret are configured.")
    logger.debug(_msg)
    pytest.skip(_msg, allow_module_level=True)

_SP_ENV_VARS = ("SP_SITE_URL_ALL", "SP_SITE_URL_ADMIN", "SP_SITE_URL_USER")
_missing_sp_vars = [v for v in _SP_ENV_VARS if not os.environ.get(v)]
if _missing_sp_vars:
    _msg = (f"SharePoint site URL environment variable(s) not set: {', '.join(_missing_sp_vars)}. "
            f"Export them before running SharePoint tests, e.g.:\n"
            f"  export SP_SITE_URL_ALL='https://intel.sharepoint.com/sites/my-site'\n"
            f"  export SP_SITE_URL_ADMIN='https://intel.sharepoint.com/sites/my-admin-site'\n"
            f"  export SP_SITE_URL_USER='https://intel.sharepoint.com/sites/my-user-site'")
    logger.debug(_msg)
    pytest.skip(_msg, allow_module_level=True)

SP_SITE_ALL = os.environ.get("SP_SITE_URL_ALL", "")
SP_SITE_ADMIN = os.environ.get("SP_SITE_URL_ADMIN", "")
SP_SITE_USER = os.environ.get("SP_SITE_URL_USER", "")

DEFAULT_SP_SITE = SP_SITE_ALL


def _site_short_name(site_url):
    """Extract the short site name from a full SharePoint URL.
    E.g. 'https://intel.sharepoint.com/sites/test-site' -> 'test-site'
    """
    if "/" in site_url:
        return site_url.rstrip("/").rsplit("/", 1)[-1]
    return site_url

SHAREPOINT_TEST_SITES = [
    SP_SITE_ALL,
    SP_SITE_USER,
    SP_SITE_ADMIN,
]

_rbac_enabled = cfg.get("edp", {}).get("rbac", {}).get("enabled", False)

_SSO_ENV_VARS = (
    "KEYCLOAK_ERAG_SSO_ADMIN_USERNAME", "KEYCLOAK_ERAG_SSO_ADMIN_PASSWORD",
    "KEYCLOAK_ERAG_SSO_USER_USERNAME", "KEYCLOAK_ERAG_SSO_USER_PASSWORD",
)
_missing_sso_vars = [v for v in _SSO_ENV_VARS if not os.environ.get(v)]
_sso_credentials_missing = len(_missing_sso_vars) > 0
_sso_skip_reason = (
    f"SSO credential environment variable(s) not set: {', '.join(_missing_sso_vars)}. "
    f"Export them before running RBAC SharePoint tests, e.g.:\n"
    f"  export KEYCLOAK_ERAG_SSO_ADMIN_USERNAME='admin@example.com'\n"
    f"  export KEYCLOAK_ERAG_SSO_ADMIN_PASSWORD='secret'\n"
    f"  export KEYCLOAK_ERAG_SSO_USER_USERNAME='user@example.com'\n"
    f"  export KEYCLOAK_ERAG_SSO_USER_PASSWORD='secret'"
) if _sso_credentials_missing else ""


def _snapshot_sharepoint_sites(sharepoint_helper):
    """Snapshot file names on all SharePoint test sites. Returns {site_url: set of names}.
    Sites that fail to list (e.g. timeout) are excluded from the dict."""
    snapshot = {}
    for site in SHAREPOINT_TEST_SITES:
        try:
            files = sharepoint_helper.list_site_files(site_name=site)
            snapshot[site] = {file.get("name") for file in files if file.get("name")}
            logger.info(f"Snapshot: site '{site}' has {len(snapshot[site])} file(s): {snapshot[site]}")
        except Exception as e:
            logger.warning(f"Snapshot: failed to list files for site '{site}': {e}")
    return snapshot


def _cleanup_sharepoint_sites(sharepoint_helper, edp_helper, files_to_keep):
    """Delete only files that were added during the test session."""
    for site in SHAREPOINT_TEST_SITES:
        if site not in files_to_keep:
            logger.warning(f"Cleanup: skipping site '{site}' — no snapshot available")
            continue
        try:
            files = sharepoint_helper.list_site_files(site_name=site)
            for file in files:
                file_name = file.get("name")
                if not file_name:
                    continue
                if file_name in files_to_keep[site]:
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
    """Snapshot files before tests, then delete only files added during the session."""
    files_before = _snapshot_sharepoint_sites(sharepoint_helper)
    yield
    _cleanup_sharepoint_sites(sharepoint_helper, edp_helper, files_to_keep=files_before)


@pytest.fixture(scope="session", autouse=True)
def restore_connected_sites(edp_helper):
    """Save connected sites before the test suite and restore them after."""
    response = edp_helper.list_sites()
    original_sites = {site["name"]: site.get("web_url", "") for site in response.json().get("sites", [])}
    logger.info(f"Connected sites before test suite: {set(original_sites.keys())}")

    yield

    response = edp_helper.list_sites()
    current_sites = {site["name"]: site.get("web_url", "") for site in response.json().get("sites", [])}
    logger.info(f"Connected sites after test suite: {set(current_sites.keys())}")

    # Disconnect sites that were added during tests
    sites_to_disconnect = set(current_sites.keys()) - set(original_sites.keys())
    for site_name in sites_to_disconnect:
        try:
            edp_helper.disconnect_site(site_name)
            logger.info(f"Restore: disconnected '{site_name}'")
        except Exception as e:
            logger.warning(f"Restore: failed to disconnect '{site_name}': {e}")

    # Reconnect sites that were removed during tests
    sites_to_reconnect = set(original_sites.keys()) - set(current_sites.keys())
    for site_name in sites_to_reconnect:
        try:
            site_url = original_sites[site_name]
            edp_helper.connect_site(site_url)
            logger.info(f"Restore: reconnected '{site_name}' ({site_url})")
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
    assert any(site.get("name") == _site_short_name(DEFAULT_SP_SITE) for site in sites.json().get("sites", [])), "Connected site not found in the list of sites"

    # Connect the same site again
    response = edp_helper.connect_site(DEFAULT_SP_SITE)
    assert response.status_code == 409


@allure.testcase("IEASG-T525")
def test_sp_connect_nonexistent_site(edp_helper):
    """Verify that connecting a nonexistent SharePoint site returns 404"""
    response = edp_helper.connect_site("https://intel.sharepoint.com/sites/this-site-does-not-exist-at-all")
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
    assert not any(site.get("name") == _site_short_name(DEFAULT_SP_SITE) for site in sites.json().get("sites", [])), "Disconnected site still found in the list of sites"

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


@allure.testcase("IEASG-T612")
@pytest.mark.skipif(_rbac_enabled, reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test")
def test_sp_reupload_file_content_changes(edp_helper, chatqa_api_helper):
    """Verify that re-uploading a file with the same name but different content updates the chatbot's knowledge"""
    file_name = "test_sp_reupload_file.txt"
    file_path_v1 = os.path.join(DATAPREP_UPLOAD_DIR, file_name)
    file_path_v2 = os.path.join(DATAPREP_UPLOAD_DIR, "test_sp_reupload_file_v2.txt")

    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload v1 of the file
    response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, file_path_v1)
    assert response.status_code in (200, 201), f"Failed to upload v1 file. Response: {response.text}"

    # Sync and wait for ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file_info, f"File '{file_name}' was not ingested into EDP"

    # Verify chatbot knows v1 content ("4817 vintage postcards")
    question = "How many vintage postcards does Rodrigoooo have?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (v1): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "4817" in response_text, f"Chatbot should mention '4817' for v1 content but got: {response_text}"

    # Re-upload with different content using the same file name
    tmp_dir = tempfile.mkdtemp()
    try:
        reupload_path = os.path.join(tmp_dir, file_name)
        shutil.copy2(file_path_v2, reupload_path)

        response = edp_helper.upload_to_sharepoint(DEFAULT_SP_SITE, reupload_path)
        assert response.status_code in (200, 201), f"Failed to re-upload file. Response: {response.text}"
    finally:
        shutil.rmtree(tmp_dir)

    # Sync and wait for re-ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file_info, f"File '{file_name}' was not re-ingested into EDP"

    # Verify chatbot now knows v2 content ("2163 antique chess sets") and no longer returns v1 content
    question = "What does Rodrigoooo own?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (v2): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "2163" in response_text, f"Chatbot should mention '2163' for v2 content but got: {response_text}"
    assert "4817" not in response_text, f"Chatbot still mentions '4817' from v1 after re-upload: {response_text}"


@allure.testcase("IEASG-T619")
@pytest.mark.skipif(_rbac_enabled, reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test")
def test_sp_upload_file_in_subdirectory(edp_helper, sharepoint_helper, chatqa_api_helper):
    """Verify uploading a file to a subdirectory in SharePoint, querying its content, and deleting it"""
    file_name = "test_sp_upload_in_subdirectory.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file_name)
    folder_name = "validation_subfolder"
    remote_path = f"{folder_name}/{file_name}"

    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Upload file to a subdirectory via SharePoint Graph API
    result = sharepoint_helper.upload_file_to_site(
        site_name=DEFAULT_SP_SITE, file_path=file_path, remote_path=remote_path
    )
    logger.info(f"File uploaded to SharePoint subdirectory: {result}")

    # Sync changes
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"

    # Wait for the file to be ingested into EDP
    file_info = edp_helper.wait_for_file_upload(file_name, "ingested", timeout=120)
    assert file_info, f"File '{file_name}' was not ingested into EDP"

    # Verify the file is present in the subdirectory using Microsoft Graph API
    files = sharepoint_helper.list_site_files(site_name=DEFAULT_SP_SITE, folder_path=folder_name)
    assert any(f.get("name") == file_name for f in files), \
        f"Uploaded file not found in subdirectory '{folder_name}'. Files: {files}"

    # Ask a related question to verify the file content is indexed
    question = "How many handmade ceramic tiles does Kazimierzzzz have?"
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "8471" in response_text, f"Unexpected ChatQA response: {response_text}"

    # Delete the file from the subdirectory
    sharepoint_helper.delete_file_from_site(site_name=DEFAULT_SP_SITE, file_name=remote_path)

    # Sync and wait for deletion in EDP
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    object_name = file_info.get("object_name")
    edp_helper.wait_for_file_deletion(object_name)

    # Verify the file is no longer in the subdirectory
    files = sharepoint_helper.list_site_files(site_name=DEFAULT_SP_SITE, folder_path=folder_name)
    assert not any(f.get("name") == file_name for f in files), \
        f"Deleted file still found in subdirectory '{folder_name}'. Files: {files}"

    # Verify chatbot no longer returns the file content
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (after deletion): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "8471" not in response_text, f"Chatbot still mentions '8471' after file deletion: {response_text}"


@allure.testcase("IEASG-T552")
@pytest.mark.skipif(not _rbac_enabled, reason="EDP RBAC is not enabled. Skipping RBAC SharePoint test")
@pytest.mark.skipif(_sso_credentials_missing, reason=_sso_skip_reason)
def test_sp_rbac_sso_admin_site_not_visible_to_user(edp_helper, sharepoint_helper, chatqa_api_helper, bootstrap_sso_user):
    """Verify that an SSO admin user can upload a file to the admin-only SP site via EDP API,
    query its content, and that SSO user (who has no access to that site) cannot see it."""
    site_name = SP_SITE_ADMIN

    # Ensure site is connected (as admin)
    edp_helper.connect_site(site_name)

    # Upload file as SSO admin
    file = "test_sp_rbac_admin_site.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file)
    response = edp_helper.upload_to_sharepoint(site_name, file_path, as_user="sso_admin")
    assert response.status_code in (200, 201), f"SSO admin failed to upload file via EDP SharePoint API. Response: {response.text}"

    # Sync changes (as admin)
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"

    # Wait for the file to be ingested into EDP
    file_info = edp_helper.wait_for_file_upload(file, "ingested", timeout=120)

    # Verify the file is present in SharePoint using Microsoft Graph API
    file_basename = os.path.basename(file_info["object_name"])
    files = sharepoint_helper.list_site_files(site_name=site_name)
    assert any(f.get("name") == file_basename for f in files), \
        f"Uploaded file not found in the list of site files. List: {files}"

    # Ask a related question as SSO admin — should get the answer
    question = "How many vintage vinyl records does Fernandoooo own?"
    response = chatqa_api_helper.call_chatqa(question, as_user="sso_admin")
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (as sso_admin): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "1847" in response_text, f"SSO admin should see file content but got: {response_text}"

    # Ask the same question as SSO user — should NOT get the answer (user has no access to admin site)
    response = chatqa_api_helper.call_chatqa(question, as_user="sso_user")
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (as sso_user): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "1847" not in response_text, \
        f"SSO user should NOT see content from admin-only site but got: {response_text}"


@allure.testcase("IEASG-T553")
@pytest.mark.skipif(not _rbac_enabled, reason="EDP RBAC is not enabled. Skipping RBAC SharePoint test")
@pytest.mark.skipif(_sso_credentials_missing, reason=_sso_skip_reason)
def test_sp_rbac_sso_user_site_not_visible_to_admin(edp_helper, sharepoint_helper, chatqa_api_helper, bootstrap_sso_user):
    """Verify RBAC: SSO user uploads a file to the user-only SP site via SharePoint API,
    can query its content, but SSO admin cannot see the content because admin has no access to that site."""
    site_name = SP_SITE_USER

    # Ensure site is connected (as admin)
    edp_helper.connect_site(site_name)

    # Upload file as SSO user to the user-only site via SharePoint API
    # (SSO user cannot upload via EDP API — only via SharePoint directly)
    file = "test_sp_rbac_user_site.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file)
    result = sharepoint_helper.upload_file_to_site(site_name=site_name, file_path=file_path)
    logger.info(f"File uploaded to SharePoint by SSO user: {result}")

    # Sync and wait for ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file, "ingested", timeout=120)
    assert file_info, f"File '{file}' was not ingested into EDP"

    # Verify file is present in SharePoint
    file_basename = os.path.basename(file_info["object_name"])
    files = sharepoint_helper.list_site_files(site_name=site_name)
    assert any(f.get("name") == file_basename for f in files), \
        f"Uploaded file not found in the list of site files. List: {files}"

    # Ask a question as SSO user — should get the answer from the file
    question = "How many porcelain teacups does Isabellaaa have?"
    response = chatqa_api_helper.call_chatqa(question, as_user="sso_user")
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (as sso_user): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "2953" in response_text, f"SSO user should see file content but got: {response_text}"

    # Ask the same question as SSO admin — should NOT get the answer (admin has no access to user site)
    response = chatqa_api_helper.call_chatqa(question, as_user="sso_admin")
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (as sso_admin): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "2953" not in response_text, \
        f"SSO admin should NOT see content from user-only site but got: {response_text}"


@allure.testcase("IEASG-T554")
@pytest.mark.skipif(not _rbac_enabled, reason="EDP RBAC is not enabled. Skipping RBAC SharePoint test")
@pytest.mark.skipif(_sso_credentials_missing, reason=_sso_skip_reason)
def test_sp_rbac_shared_site_visible_to_both_users(edp_helper, sharepoint_helper, chatqa_api_helper, bootstrap_sso_user):
    """Verify RBAC: SSO admin uploads a file to the shared SP site,
    can query its content, and SSO user can also see the content (both have access)."""
    site_name = SP_SITE_ALL

    # Ensure site is connected (as admin)
    edp_helper.connect_site(site_name)

    # Upload file as SSO admin to the shared site
    file = "test_sp_rbac_shared_site.txt"
    file_path = os.path.join(DATAPREP_UPLOAD_DIR, file)
    response = edp_helper.upload_to_sharepoint(site_name, file_path, as_user="sso_admin")
    assert response.status_code in (200, 201), \
        f"SSO admin failed to upload file via EDP SharePoint API. Response: {response.text}"

    # Sync and wait for ingestion
    sync_response = edp_helper.sync_sharepoint()
    assert sync_response.status_code == 200, f"Failed to sync SharePoint. Response: {sync_response.text}"
    file_info = edp_helper.wait_for_file_upload(file, "ingested", timeout=120)
    assert file_info, f"File '{file}' was not ingested into EDP"

    # Verify file is present in SharePoint
    file_basename = os.path.basename(file_info["object_name"])
    files = sharepoint_helper.list_site_files(site_name=site_name)
    assert any(f.get("name") == file_basename for f in files), \
        f"Uploaded file not found in the list of site files. List: {files}"

    # Ask a question as SSO admin — should get the answer from the file
    question = "How many miniature ship models does Aleksanderrr have?"
    response = chatqa_api_helper.call_chatqa(question, as_user="sso_admin")
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (as sso_admin): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "4281" in response_text, f"SSO admin should see file content but got: {response_text}"

    # Ask the same question as SSO user — should also get the answer (both have access to shared site)
    response = chatqa_api_helper.call_chatqa(question, as_user="sso_user")
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response (as sso_user): {response_text}; status code: {response.status_code}")
    assert response.status_code == 200, f"ChatQA API call failed with status code {response.status_code}"
    assert "4281" in response_text, \
        f"SSO user should see content from shared site but got: {response_text}"


@allure.testcase("IEASG-T618")
@pytest.mark.skipif(
    _rbac_enabled,
    reason="EDP RBAC is enabled. Skipping non-RBAC SharePoint test"
)
def test_sp_upload_many_files(edp_helper, sharepoint_helper):
    """Upload 100 files directly to SharePoint, sync, and verify all are ingested."""
    num_files = 100

    # Ensure site is connected
    edp_helper.connect_site(DEFAULT_SP_SITE)

    # Generate files
    tmp_dir = tempfile.mkdtemp(prefix="sp_bulk_upload_")
    file_paths = []
    try:
        for i in range(num_files):
            name = f"sp_bulk_{i:04d}.txt"
            path = os.path.join(tmp_dir, name)
            content = (
                f"SharePoint bulk upload test {i}. "
                f"Content: {uuid.uuid4()}\n"
            )
            with open(path, "w") as f:
                f.write(content * 20)
            file_paths.append(path)

        # Upload all files in parallel directly to SharePoint
        sharepoint_helper.upload_files_in_parallel(
            DEFAULT_SP_SITE, file_paths
        )

        # Trigger manual sync
        sync_response = edp_helper.sync_sharepoint()
        assert sync_response.status_code == 200, (
            f"Failed to sync. Response: {sync_response.text}"
        )

        # Wait for all files to be ingested
        basenames = {os.path.basename(p) for p in file_paths}
        edp_helper.wait_for_all_files_ingestion(
            basenames, timeout=900
        )

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
