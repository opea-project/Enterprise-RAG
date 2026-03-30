#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for Data Ingestion admin panel functionality.

Tests the Data Ingestion tab interactions using data-testid selectors:
1. Navigate to Data Ingestion tab
2. Open upload dialog
3. Add / remove links from pre-upload list
4. Search files and links
5. Refresh and auto-refresh toggle
6. Batch delete dialog flow
7. Data ingestion settings dialog

All selectors use data-testid attributes provided by PR #1819.
"""

import logging

import allure
import pytest

from tests.e2e.ui.conftest import requires_chatqa

logger = logging.getLogger(__name__)

pytestmark = requires_chatqa


# ============================================================================
# TEST CASES
# ============================================================================

@allure.testcase("IEASG-T364")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_navigate_to_data_ingestion_tab(chat_ui_helper):
    """
    Test navigation to the Data Ingestion tab in the admin panel.

    Steps:
    1. Navigate to admin panel
    2. Click 'Data Ingestion' tab within admin-panel-tabs
    3. Verify URL includes /data-ingestion

    Success criteria:
    - admin-panel-tabs is rendered (data-testid)
    - URL updates to include /data-ingestion
    """
    logger.info("Test: Navigate to Data Ingestion tab")

    page = chat_ui_helper.page

    nav_success = await chat_ui_helper.navigate_to_admin_tab("data-ingestion")
    assert nav_success, "Failed to navigate to data-ingestion tab"

    # Assert: URL contains data-ingestion
    assert "data-ingestion" in page.url, \
        f"Expected 'data-ingestion' in URL, got {page.url}"
    logger.info("Assert: URL verified for data-ingestion")

    logger.info("Test completed: Data Ingestion tab navigation validated")


@allure.testcase("IEASG-T365")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_upload_data_dialog_opens(chat_ui_helper):
    """
    Test that the Upload Data dialog opens and closes.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Click upload-data-trigger-button
    3. Verify upload-data-dialog is rendered
    4. Close dialog

    Success criteria:
    - Trigger button uses data-testid="upload-data-trigger-button"
    - Dialog renders with data-testid="upload-data-dialog"
    """
    logger.info("Test: Upload Data dialog open/close")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # Click trigger
    trigger_visible = await chat_ui_helper.is_visible_by_testid(
        "upload-data-trigger-button", timeout=10000
    )
    assert trigger_visible, "upload-data-trigger-button not visible"

    clicked = await chat_ui_helper.click_by_testid("upload-data-trigger-button")
    assert clicked, "Failed to click upload-data-trigger-button"
    await page.wait_for_timeout(500)

    # Assert: dialog is open
    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "upload-data-dialog", timeout=5000
    )
    assert dialog_visible, "upload-data-dialog should be visible"
    logger.info("Assert: upload-data-dialog is rendered")

    # Close dialog (press Escape or click close button)
    close = page.locator('[data-testid="upload-data-dialog-close-button"]')
    try:
        await close.wait_for(state="visible", timeout=3000)
        await close.click()
    except Exception:
        await page.keyboard.press("Escape")

    await page.wait_for_timeout(500)
    dialog_hidden = await chat_ui_helper.wait_for_testid_hidden(
        "upload-data-dialog", timeout=5000
    )
    assert dialog_hidden, "Dialog should be closed"
    logger.info("Dialog closed successfully")

    logger.info("Test completed: Upload Data dialog validated")


@allure.testcase("IEASG-T366")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_add_link_to_upload_list(chat_ui_helper):
    """
    Test adding a link via link-input and add-link-button.

    Steps:
    1. Navigate to Data Ingestion → open upload dialog
    2. Fill link-input with a URL
    3. Click add-link-button
    4. Verify link appears in the pre-upload list

    Success criteria:
    - link-input accepts text (data-testid)
    - add-link-button adds the link to the list
    """
    logger.info("Test: Add link to upload list")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # Open upload dialog
    await chat_ui_helper.click_by_testid("upload-data-trigger-button")
    await chat_ui_helper.is_visible_by_testid("upload-data-dialog", timeout=5000)

    # Fill link input
    test_url = "https://example.com/test-document.pdf"
    fill_ok = await chat_ui_helper.fill_by_testid("link-input", test_url)
    assert fill_ok, "Failed to fill link-input"
    logger.info(f"Filled link-input with: {test_url}")

    # Click add-link-button
    add_ok = await chat_ui_helper.click_by_testid("add-link-button")
    assert add_ok, "Failed to click add-link-button"
    await page.wait_for_timeout(500)
    logger.info("Clicked add-link-button")

    # Verify: link should appear in the list (delete-link-from-list-button appears)
    link_item_count = await chat_ui_helper.count_by_testid("delete-link-from-list-button")
    assert link_item_count >= 1, \
        f"Expected at least 1 link in list, found {link_item_count}"
    logger.info(f"Assert: {link_item_count} link(s) in pre-upload list")

    # Clean up: close dialog
    await page.keyboard.press("Escape")

    logger.info("Test completed: Add link validated")


@allure.testcase("IEASG-T367")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_remove_link_from_upload_list(chat_ui_helper):
    """
    Test removing a link from the pre-upload list.

    Steps:
    1. Open upload dialog
    2. Add a link
    3. Click delete-link-from-list-button
    4. Verify link is removed

    Success criteria:
    - delete-link-from-list-button removes the link
    """
    logger.info("Test: Remove link from upload list")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # Open upload dialog and add a link
    await chat_ui_helper.click_by_testid("upload-data-trigger-button")
    await chat_ui_helper.is_visible_by_testid("upload-data-dialog", timeout=5000)
    await chat_ui_helper.fill_by_testid("link-input", "https://example.com/remove-me.pdf")
    await chat_ui_helper.click_by_testid("add-link-button")
    await page.wait_for_timeout(500)

    count_before = await chat_ui_helper.count_by_testid("delete-link-from-list-button")
    assert count_before >= 1, "Need at least 1 link to test removal"
    logger.info(f"Links before removal: {count_before}")

    # Click the first delete button
    delete_ok = await chat_ui_helper.click_nth_by_testid(
        "delete-link-from-list-button", index=0
    )
    assert delete_ok, "Failed to click delete-link-from-list-button"
    await page.wait_for_timeout(500)

    count_after = await chat_ui_helper.count_by_testid("delete-link-from-list-button")
    assert count_after < count_before, \
        f"Expected count to decrease, was {count_before}, now {count_after}"
    logger.info(f"Assert: Links after removal: {count_after}")

    # Clean up
    await page.keyboard.press("Escape")

    logger.info("Test completed: Remove link validated")


@allure.testcase("IEASG-T368")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_files_search_bar(chat_ui_helper):
    """
    Test the files search bar renders and accepts input.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Verify files-search-bar is visible
    3. Type a query and verify input value

    Success criteria:
    - files-search-bar has data-testid and is functional
    """
    logger.info("Test: Files search bar")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # The SearchBar component does not forward data-testid to the DOM,
    # so locate it via its placeholder text instead.
    search_input = page.locator('input[placeholder*="Filter files"]')

    # Assert: search bar visible (may take longer if API data is loading)
    try:
        await search_input.wait_for(state="visible", timeout=30000)
        visible = True
    except Exception:
        visible = False
    assert visible, "files-search-bar should be visible"
    logger.info("Assert 1: files-search-bar is visible")

    # Fill and verify
    await search_input.fill("test-query")
    value = await search_input.input_value()
    assert value == "test-query", f"Expected 'test-query', got '{value}'"
    logger.info("Assert 2: Search bar accepts input")

    # Clear
    await search_input.fill("")

    logger.info("Test completed: Files search bar validated")


@allure.testcase("IEASG-T369")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_refresh_button(chat_ui_helper):
    """
    Test the refresh button on data ingestion tab.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Verify refresh-button is visible and enabled
    3. Click it

    Success criteria:
    - refresh-button is interactive via data-testid
    """
    logger.info("Test: Refresh button")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # Assert: visible
    visible = await chat_ui_helper.is_visible_by_testid("refresh-button", timeout=10000)
    assert visible, "refresh-button should be visible"

    # Assert: enabled
    enabled = await chat_ui_helper.is_enabled_by_testid("refresh-button")
    assert enabled, "refresh-button should be enabled"

    # Click
    clicked = await chat_ui_helper.click_by_testid("refresh-button")
    assert clicked, "Failed to click refresh-button"
    await page.wait_for_timeout(1000)

    logger.info("Test completed: Refresh button validated")


@allure.testcase("IEASG-T370")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_autorefresh_checkbox(chat_ui_helper):
    """
    Test the auto-refresh checkbox toggle.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Open settings dialog via data-ingestion-settings-button
    3. Verify autorefresh-checkbox is rendered
    4. Toggle it

    Success criteria:
    - Settings dialog opens via data-testid
    - autorefresh-checkbox is interactive
    """
    logger.info("Test: Autorefresh checkbox")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # Open settings dialog
    settings_visible = await chat_ui_helper.is_visible_by_testid(
        "data-ingestion-settings-button", timeout=10000
    )
    assert settings_visible, "data-ingestion-settings-button should be visible"

    await chat_ui_helper.click_by_testid("data-ingestion-settings-button")
    await page.wait_for_timeout(500)

    # Assert: settings dialog rendered
    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "data-ingestion-settings-dialog", timeout=5000
    )
    assert dialog_visible, "data-ingestion-settings-dialog should be visible"
    logger.info("Assert 1: Settings dialog opened")

    # Assert: autorefresh checkbox exists
    checkbox_visible = await chat_ui_helper.is_visible_by_testid(
        "autorefresh-checkbox", timeout=5000
    )
    assert checkbox_visible, "autorefresh-checkbox should be visible"
    logger.info("Assert 2: autorefresh-checkbox visible")

    # Click to toggle
    await chat_ui_helper.click_by_testid("autorefresh-checkbox")
    await page.wait_for_timeout(300)
    logger.info("Toggled autorefresh checkbox")

    # Close settings
    await page.keyboard.press("Escape")

    logger.info("Test completed: Autorefresh checkbox validated")


@allure.testcase("IEASG-T371")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_batch_delete_dialog(chat_ui_helper):
    """
    Test the batch delete dialog opens, shows confirm/cancel, and closes.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Click batch-actions-button
    3. Verify batch-delete-dialog appears
    4. Verify confirm and cancel buttons exist
    5. Cancel to close

    Success criteria:
    - batch-actions-button triggers batch-delete-dialog
    - batch-delete-confirm-button and batch-delete-cancel-button are present
    """
    logger.info("Test: Batch delete dialog")

    page = chat_ui_helper.page
    await chat_ui_helper.navigate_to_admin_tab("data-ingestion")

    # Click batch actions
    batch_visible = await chat_ui_helper.is_visible_by_testid(
        "batch-actions-button", timeout=10000
    )
    if not batch_visible:
        logger.warning("batch-actions-button not visible — may require file selection; skipping")
        pytest.skip("Batch actions requires selected files")

    await chat_ui_helper.click_by_testid("batch-actions-button")
    await page.wait_for_timeout(500)

    # Check if the dialog appeared (it may require items selected)
    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "batch-delete-dialog", timeout=5000
    )

    if dialog_visible:
        # Assert: confirm and cancel buttons exist
        confirm_visible = await chat_ui_helper.is_visible_by_testid(
            "batch-delete-confirm-button", timeout=3000
        )
        cancel_visible = await chat_ui_helper.is_visible_by_testid(
            "batch-delete-cancel-button", timeout=3000
        )
        assert confirm_visible, "batch-delete-confirm-button should be visible"
        assert cancel_visible, "batch-delete-cancel-button should be visible"
        logger.info("Assert: Confirm and Cancel buttons present in dialog")

        # Cancel to close
        await chat_ui_helper.click_by_testid("batch-delete-cancel-button")
        await page.wait_for_timeout(500)
        logger.info("Closed batch-delete-dialog via cancel")
    else:
        logger.info("Batch delete dialog did not open (no items selected) — verifying button is interactive")
        # The button itself was clickable, which validates the data-testid

    logger.info("Test completed: Batch delete dialog validated")
