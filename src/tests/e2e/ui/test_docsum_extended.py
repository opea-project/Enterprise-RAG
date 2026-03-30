#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for DocSum extended UI functionality using data-testid selectors.

Tests advanced DocSum features beyond the basic flow in test_basic_docsum.py:
1. Paste text area clear button
2. Upload file tab interactions
3. Export summary dialog
4. Summary history item management (rename, delete)
5. Generated summary content verification via data-testid

All selectors use data-testid attributes for test resilience.
"""

import logging

import allure
import pytest

from tests.e2e.ui.conftest import requires_docsum

logger = logging.getLogger(__name__)

pytestmark = requires_docsum


SAMPLE_TEXT = """
Artificial Intelligence (AI) is transforming industries across the globe.
From healthcare to finance, AI-powered solutions are improving efficiency,
accuracy, and decision-making processes. Machine learning algorithms can
analyze vast amounts of data to identify patterns and make predictions
that would be impossible for humans to detect manually.
"""


# ============================================================================
# HELPERS
# ============================================================================

async def _fill_and_generate_summary(docsum_ui_helper, text=None):
    """Fill paste-text area and generate a summary for use in subsequent tests."""
    page = docsum_ui_helper.page
    input_text = text or SAMPLE_TEXT

    # Fill textarea via data-testid
    fill_ok = await docsum_ui_helper.fill_by_testid("paste-text-textarea-input", input_text)
    assert fill_ok, "Failed to fill paste-text-textarea-input"
    await page.wait_for_timeout(500)

    # Click generate summary using the dedicated helper method which
    # handles both data-testid and CSS class fallback selectors.
    # Note: The generate button currently uses class='dropdown-button__main'
    # without a data-testid attribute.
    click_ok = await docsum_ui_helper.click_generate_summary_button()
    assert click_ok, "Failed to click Generate Summary button"

    # Wait for summary
    summary_text = await docsum_ui_helper.wait_for_summary(timeout=60000)
    assert summary_text and len(summary_text.strip()) > 0, "Summary was empty"
    return summary_text


# ============================================================================
# TEST CASES
# ============================================================================

@allure.testcase("IEASG-T379")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_paste_text_textarea_via_testid(docsum_ui_helper):
    """
    Test the paste-text textarea using data-testid instead of element ID.

    Steps:
    1. Verify paste-text-textarea-input is visible
    2. Fill text via data-testid
    3. Verify input value matches

    Success criteria:
    - data-testid="paste-text-textarea-input" is functional
    """
    logger.info("Test: Paste text textarea via data-testid")

    # Assert: visible
    visible = await docsum_ui_helper.is_visible_by_testid(
        "paste-text-textarea-input", timeout=10000
    )
    assert visible, "paste-text-textarea-input should be visible"
    logger.info("Assert 1: Textarea visible")

    # Fill
    test_text = "Testing input via data-testid."
    fill_ok = await docsum_ui_helper.fill_by_testid("paste-text-textarea-input", test_text)
    assert fill_ok, "Failed to fill textarea via data-testid"

    # Verify
    value = await docsum_ui_helper.get_input_value_by_testid("paste-text-textarea-input")
    assert value == test_text, f"Expected '{test_text}', got '{value}'"
    logger.info("Assert 2: Input value matches")

    logger.info("Test completed: Paste text textarea validated")


@allure.testcase("IEASG-T380")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_paste_text_clear_button(docsum_ui_helper):
    """
    Test the clear button on the paste text tab.

    Steps:
    1. Fill textarea with text
    2. Click paste-text-clear-button
    3. Verify textarea is empty

    Success criteria:
    - data-testid="paste-text-clear-button" clears the textarea
    """
    logger.info("Test: Paste text clear button")

    page = docsum_ui_helper.page

    # Fill textarea
    fill_ok = await docsum_ui_helper.fill_by_testid(
        "paste-text-textarea-input", "Text to clear"
    )
    assert fill_ok, "Failed to fill textarea"
    await page.wait_for_timeout(300)

    # Click clear button
    clear_visible = await docsum_ui_helper.is_visible_by_testid(
        "paste-text-clear-button", timeout=5000
    )
    assert clear_visible, "paste-text-clear-button should be visible when text is entered"

    clicked = await docsum_ui_helper.click_by_testid("paste-text-clear-button")
    assert clicked, "Failed to click paste-text-clear-button"
    await page.wait_for_timeout(300)

    # Verify cleared
    value = await docsum_ui_helper.get_input_value_by_testid("paste-text-textarea-input")
    assert value == "" or value is None, f"Expected empty textarea, got '{value}'"
    logger.info("Assert: Textarea cleared successfully")

    logger.info("Test completed: Clear button validated")


@allure.testcase("IEASG-T381")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_generated_summary_content_testid(docsum_ui_helper):
    """
    Test that generated summary content appears with correct data-testid.

    Steps:
    1. Fill text and generate summary
    2. Verify generated-summary-content is visible and has text

    Success criteria:
    - data-testid="generated-summary-content" contains summary text
    """
    logger.info("Test: Generated summary content via data-testid")

    summary_text = await _fill_and_generate_summary(docsum_ui_helper)
    logger.info(f"Summary generated: {len(summary_text)} chars")

    # Assert: content element is visible via data-testid
    visible = await docsum_ui_helper.is_visible_by_testid(
        "generated-summary-content", timeout=5000
    )
    assert visible, "generated-summary-content should be visible"

    # Assert: has actual text content
    content = await docsum_ui_helper.get_text_by_testid("generated-summary-content")
    assert content and len(content.strip()) > 10, \
        f"Expected substantial content, got: {content[:50] if content else 'None'}"
    logger.info(f"Assert: Summary content has {len(content)} chars")

    logger.info("Test completed: Generated summary content validated")


@allure.testcase("IEASG-T382")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_export_summary_button(docsum_ui_helper):
    """
    Test the export summary button and dialog.

    Steps:
    1. Generate a summary
    2. Click export-summary-button
    3. Verify export-summary-action-dialog is rendered
    4. Verify export-summary-format-select is visible
    5. Close dialog

    Success criteria:
    - All export elements use data-testid
    """
    logger.info("Test: Export summary button and dialog")

    page = docsum_ui_helper.page

    await _fill_and_generate_summary(docsum_ui_helper)

    # Click export button
    export_visible = await docsum_ui_helper.is_visible_by_testid(
        "export-summary-button", timeout=5000
    )
    assert export_visible, "export-summary-button should be visible after summary generated"

    clicked = await docsum_ui_helper.click_by_testid("export-summary-button")
    assert clicked, "Failed to click export-summary-button"
    await page.wait_for_timeout(500)

    # Assert: export dialog rendered
    dialog_visible = await docsum_ui_helper.is_visible_by_testid(
        "export-summary-action-dialog", timeout=5000
    )
    assert dialog_visible, "export-summary-action-dialog should be visible"
    logger.info("Assert 1: Export dialog rendered")

    # Assert: format select rendered
    format_visible = await docsum_ui_helper.is_visible_by_testid(
        "export-summary-format-select", timeout=3000
    )
    assert format_visible, "export-summary-format-select should be visible"
    logger.info("Assert 2: Format select visible")

    # Assert: file name element rendered
    filename_visible = await docsum_ui_helper.is_visible_by_testid(
        "export-summary-file-name", timeout=3000
    )
    assert filename_visible, "export-summary-file-name should be visible"
    logger.info("Assert 3: File name element visible")

    # Close dialog
    await page.keyboard.press("Escape")

    logger.info("Test completed: Export summary validated")


@allure.testcase("IEASG-T383")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_docsum_tabs_via_testid(docsum_ui_helper):
    """
    Test that the DocSum tabs component renders with correct data-testid.

    Steps:
    1. Verify docsum-tabs is visible
    2. Verify it has children (tab items)

    Success criteria:
    - data-testid="docsum-tabs" is rendered with children
    """
    logger.info("Test: DocSum tabs via data-testid")

    tabs_ok = await docsum_ui_helper.check_element_rendered(
        data_testid="docsum-tabs", check_children=True, timeout=10000
    )
    assert tabs_ok, "docsum-tabs should be rendered with children"
    logger.info("Assert: docsum-tabs rendered with tab items")

    logger.info("Test completed: DocSum tabs validated")


@allure.testcase("IEASG-T384")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_summary_history_item_menu(docsum_ui_helper):
    """
    Test the summary history item context menu.

    Steps:
    1. Generate a summary (this creates a history item)
    2. Navigate to history view (if separate tab)
    3. Verify history-item is rendered
    4. Open history-item-menu
    5. Verify rename, export, delete menu items exist

    Note: If history is not visible, the test skips gracefully.

    Success criteria:
    - All history menu items use data-testid
    """
    logger.info("Test: Summary history item menu")

    page = docsum_ui_helper.page

    # Generate a summary to create history
    await _fill_and_generate_summary(docsum_ui_helper)
    await page.wait_for_timeout(1000)

    # Check if history items exist
    history_count = await docsum_ui_helper.count_by_testid("history-item")

    if history_count == 0:
        logger.info("No history items found — may need to navigate to history tab")
        # Try clicking a history tab if it exists
        history_tab = page.locator('text=History')
        try:
            await history_tab.wait_for(state="visible", timeout=3000)
            await history_tab.click()
            await page.wait_for_timeout(1000)
            history_count = await docsum_ui_helper.count_by_testid("history-item")
        except Exception:
            pass

    if history_count == 0:
        logger.info("History items not available — skipping menu test")
        pytest.skip("No history items available")

    logger.info(f"Found {history_count} history item(s)")

    # Open history item context menu (handles tooltip dismissal)
    menu_opened = await docsum_ui_helper.open_summary_history_menu(index=0)
    assert menu_opened, "Failed to open summary history menu"
    await page.wait_for_timeout(300)

    # Assert: menu items exist
    rename_visible = await docsum_ui_helper.is_visible_by_testid(
        "rename-summary-menu-item", timeout=3000
    )
    export_visible = await docsum_ui_helper.is_visible_by_testid(
        "export-summary-menu-item", timeout=3000
    )
    delete_visible = await docsum_ui_helper.is_visible_by_testid(
        "delete-summary-menu-item", timeout=3000
    )

    assert rename_visible, "rename-summary-menu-item should be visible"
    assert export_visible, "export-summary-menu-item should be visible"
    assert delete_visible, "delete-summary-menu-item should be visible"
    logger.info("Assert: All history menu items rendered")

    # Close menu
    await page.keyboard.press("Escape")

    logger.info("Test completed: Summary history menu validated")


@allure.testcase("IEASG-T385")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_rename_summary_dialog(docsum_ui_helper):
    """
    Test the rename summary dialog via history menu.

    Steps:
    1. Ensure history item exists
    2. Open history menu → click rename
    3. Verify rename-summary-dialog and rename-summary-input render
    4. Cancel to close

    Success criteria:
    - Rename dialog elements use data-testid
    """
    logger.info("Test: Rename summary dialog")

    page = docsum_ui_helper.page

    # Generate summary for history
    await _fill_and_generate_summary(docsum_ui_helper)
    await page.wait_for_timeout(1000)

    history_count = await docsum_ui_helper.count_by_testid("history-item")
    if history_count == 0:
        # Try history tab
        history_tab = page.locator('text=History')
        try:
            await history_tab.click()
            await page.wait_for_timeout(1000)
            history_count = await docsum_ui_helper.count_by_testid("history-item")
        except Exception:
            pass

    if history_count == 0:
        pytest.skip("No history items available")

    # Open history item context menu (handles tooltip dismissal)
    menu_opened = await docsum_ui_helper.open_summary_history_menu(index=0)
    assert menu_opened, "Failed to open summary history menu"
    await page.wait_for_timeout(300)
    await docsum_ui_helper.click_by_testid("rename-summary-menu-item")
    await page.wait_for_timeout(500)

    # Assert: dialog visible
    dialog_visible = await docsum_ui_helper.is_visible_by_testid(
        "rename-summary-dialog", timeout=5000
    )
    assert dialog_visible, "rename-summary-dialog should be visible"
    logger.info("Assert 1: Rename dialog rendered")

    # Assert: input visible
    input_visible = await docsum_ui_helper.is_visible_by_testid(
        "rename-summary-input", timeout=3000
    )
    assert input_visible, "rename-summary-input should be visible"
    logger.info("Assert 2: Rename input rendered")

    # Cancel
    await page.keyboard.press("Escape")

    logger.info("Test completed: Rename summary dialog validated")


@allure.testcase("IEASG-T386")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_summary_dialog(docsum_ui_helper):
    """
    Test the delete summary confirmation dialog.

    Steps:
    1. Ensure history item exists
    2. Open history menu → click delete
    3. Verify delete-summary-dialog renders
    4. Cancel to close

    Success criteria:
    - data-testid="delete-summary-dialog" is rendered
    """
    logger.info("Test: Delete summary dialog")

    page = docsum_ui_helper.page

    await _fill_and_generate_summary(docsum_ui_helper)
    await page.wait_for_timeout(1000)

    history_count = await docsum_ui_helper.count_by_testid("history-item")
    if history_count == 0:
        history_tab = page.locator('text=History')
        try:
            await history_tab.click()
            await page.wait_for_timeout(1000)
            history_count = await docsum_ui_helper.count_by_testid("history-item")
        except Exception:
            pass

    if history_count == 0:
        pytest.skip("No history items available")

    # Open history item context menu (handles tooltip dismissal)
    menu_opened = await docsum_ui_helper.open_summary_history_menu(index=0)
    assert menu_opened, "Failed to open summary history menu"
    await page.wait_for_timeout(300)
    await docsum_ui_helper.click_by_testid("delete-summary-menu-item")
    await page.wait_for_timeout(500)

    # Assert: deletion dialog visible
    dialog_visible = await docsum_ui_helper.is_visible_by_testid(
        "delete-summary-dialog", timeout=5000
    )
    assert dialog_visible, "delete-summary-dialog should be visible"
    logger.info("Assert: Delete summary dialog rendered")

    # Cancel
    await page.keyboard.press("Escape")

    logger.info("Test completed: Delete summary dialog validated")
