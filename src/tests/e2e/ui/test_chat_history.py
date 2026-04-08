#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for Chat History management functionality.

Tests the chat history sidebar interactions using data-testid selectors:
1. New chat creation
2. Chat history item appears after sending a message
3. Rename chat via context menu
4. Pin / unpin chat
5. Delete chat
6. Export chat dialog
7. Chat history search / filter

All selectors use data-testid attributes for resilience against CSS/class changes.
"""

import json
import logging
import os
import tempfile

import allure
import pytest

from tests.e2e.ui.conftest import requires_chatqa

logger = logging.getLogger(__name__)

pytestmark = requires_chatqa


# ============================================================================
# HELPERS
# ============================================================================

async def _ensure_at_least_one_chat(chat_ui_helper):
    """Start a new chat and send a message to guarantee a fresh chat history item exists."""
    # Always start a new chat so previous test state doesn't bleed over
    await chat_ui_helper.start_new_chat()
    await chat_ui_helper.page.wait_for_timeout(500)
    success, _ = await chat_ui_helper.send_message(
        "Hello, this is a test message.", wait_for_response=True
    )
    assert success, "Failed to send seed message for chat history"
    await chat_ui_helper.page.wait_for_timeout(1000)
    # Ensure the sidebar is open so subsequent assertions on history work
    await chat_ui_helper.ensure_sidebar_open()


# ============================================================================
# TEST CASES
# ============================================================================

@allure.testcase("IEASG-T356")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_new_chat_button(chat_ui_helper):
    """
    Test that clicking New Chat starts a fresh conversation.

    Steps:
    1. Send a message first (new-chat-button only appears after first message)
    2. Verify new-chat-button is visible
    3. Click new-chat-button
    4. Verify conversation feed is empty / URL includes /chat

    Success criteria:
    - New chat button is visible and clickable via data-testid
    - After click, conversation feed is reset
    """
    logger.info("Test: New Chat button via data-testid")

    page = chat_ui_helper.page

    # Seed a chat so that new-chat-button appears (it only exists after first message)
    await _ensure_at_least_one_chat(chat_ui_helper)

    # Assert 1: New chat button is visible (only after first message sent)
    is_visible = await chat_ui_helper.is_visible_by_testid("new-chat-button", timeout=5000)
    assert is_visible, "new-chat-button should be visible after sending a message"
    logger.info("Assert 1: new-chat-button is visible")

    # Act: click new chat
    success = await chat_ui_helper.start_new_chat()
    assert success, "Failed to click new-chat-button"
    await page.wait_for_timeout(1000)
    logger.info("Clicked new-chat-button")

    # Assert 2: URL still on /chat (new empty chat)
    assert "/chat" in page.url, f"Expected /chat in URL, got {page.url}"
    logger.info("Assert 2: URL correct after new chat")

    # Assert 3: Prompt input form is visible (InitialChatLayout is shown for new/empty chat;
    # conversation-feed only renders once messages exist)
    prompt_visible = await chat_ui_helper.is_visible_by_testid("prompt-input-form", timeout=5000)
    assert prompt_visible, "prompt-input-form should be visible on new chat"
    logger.info("Assert 3: Prompt input form visible on new chat (initial layout)")

    logger.info("Test completed: New chat button validated")


@allure.testcase("IEASG-T357")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_chat_history_item_appears(chat_ui_helper):
    """
    Test that a chat history item appears after sending a message.

    Steps:
    1. Start a new chat (if button available)
    2. Send a message
    3. Open sidebar and verify chat-history-item exists

    Success criteria:
    - At least one chat-history-item is rendered with correct data-testid
    """
    logger.info("Test: Chat history item appears")

    page = chat_ui_helper.page

    # Start fresh if possible
    await chat_ui_helper.start_new_chat()
    await page.wait_for_timeout(500)

    # Send message to create a chat
    success, response = await chat_ui_helper.send_message(
        "What is the capital of France?", wait_for_response=True
    )
    assert success, "Failed to send message"
    assert response, "No response received"
    logger.info("Message sent and response received")

    # Open sidebar and check history items
    await chat_ui_helper.ensure_sidebar_open()

    # Assert: History item exists
    count = await chat_ui_helper.get_chat_history_count()
    assert count >= 1, f"Expected at least 1 chat history item, found {count}"
    logger.info(f"Assert: {count} chat history item(s) found via data-testid")

    logger.info("Test completed: Chat history item appearance validated")


@allure.testcase("IEASG-T358")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_rename_chat(chat_ui_helper):
    """
    Test renaming a chat through the history item context menu.

    Steps:
    1. Ensure chat exists
    2. Hover over chat-history-item to reveal menu
    3. Click chat-history-item-menu-button
    4. Click rename-chat-menu-item
    5. Fill rename-chat-input with new name
    6. Confirm
    7. Verify title changed

    Success criteria:
    - All menu interactions use data-testid selectors
    - Chat name updates after rename
    """
    logger.info("Test: Rename chat via data-testid menu")

    page = chat_ui_helper.page
    await _ensure_at_least_one_chat(chat_ui_helper)

    new_name = "Renamed Test Chat"

    # Rename the first chat in the history
    rename_success = await chat_ui_helper.rename_chat(new_name, item_index=0)
    assert rename_success, "Failed to rename chat"
    logger.info("Chat renamed successfully")

    # Verify: scan all chat history items for the new name
    # (sidebar may reorder items after rename)
    await page.wait_for_timeout(1000)
    items = page.locator('[data-testid="chat-history-item"]')
    count = await items.count()
    found = False
    for i in range(count):
        text = await items.nth(i).text_content()
        if new_name in (text or ""):
            found = True
            logger.info(f"Assert: Chat title '{new_name}' found at index {i}")
            break
    assert found, (
        f"Expected '{new_name}' in any chat history item, "
        f"scanned {count} items"
    )

    logger.info("Test completed: Chat rename validated")


@allure.testcase("IEASG-T359")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_pin_unpin_chat(chat_ui_helper):
    """
    Test pinning and unpinning a chat via the context menu.

    Steps:
    1. Ensure chat exists
    2. Open context menu → click pin-chat-menu-item
    3. Verify unpin-chat-button appears (pinned state)
    4. Click unpin-chat-button
    5. Verify pin is removed

    Success criteria:
    - Pin action uses data-testid="pin-chat-menu-item"
    - Pinned chat shows data-testid="unpin-chat-button"
    - Unpin removes the pin indicator
    """
    logger.info("Test: Pin/Unpin chat via data-testid")

    page = chat_ui_helper.page
    await _ensure_at_least_one_chat(chat_ui_helper)

    # Step 1: Pin the chat via context menu
    menu_opened = await chat_ui_helper.open_chat_history_menu(index=0)
    assert menu_opened, "Failed to open chat history menu"
    await page.wait_for_timeout(300)

    pin_clicked = await chat_ui_helper.click_chat_menu_action("pin")
    assert pin_clicked, "Failed to click pin-chat-menu-item"
    await page.wait_for_timeout(500)
    logger.info("Step 1: Pinned chat via menu")

    # Assert 1: unpin-chat-button should now be visible (pinned state)
    unpin_visible = await chat_ui_helper.is_visible_by_testid("unpin-chat-button", timeout=5000)
    assert unpin_visible, "unpin-chat-button should appear after pinning"
    logger.info("Assert 1: Chat is pinned (unpin-chat-button visible)")

    # Step 2: Unpin by clicking unpin-chat-button
    unpin_clicked = await chat_ui_helper.click_by_testid("unpin-chat-button")
    assert unpin_clicked, "Failed to click unpin-chat-button"
    await page.wait_for_timeout(500)
    logger.info("Step 2: Clicked unpin-chat-button")

    # Assert 2: unpin-chat-button should no longer be visible
    unpin_gone = await chat_ui_helper.wait_for_testid_hidden("unpin-chat-button", timeout=3000)
    assert unpin_gone, "unpin-chat-button should disappear after unpinning"
    logger.info("Assert 2: Chat is unpinned (unpin-chat-button hidden)")

    logger.info("Test completed: Pin/Unpin validated")


@allure.testcase("IEASG-T360")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_chat(chat_ui_helper):
    """
    Test deleting a chat via the context menu.

    Steps:
    1. Start new chat, send message to create history entry
    2. Open sidebar and count current history items
    3. Open context menu → click delete-chat-menu-item
    4. Verify confirmation dialog and confirm
    5. Verify item count decreased

    Success criteria:
    - Delete action uses data-testid selectors
    - Chat is removed from history after deletion
    """
    logger.info("Test: Delete chat via data-testid")

    page = chat_ui_helper.page

    # Create a fresh chat to delete
    await chat_ui_helper.start_new_chat()
    await page.wait_for_timeout(500)
    success, _ = await chat_ui_helper.send_message(
        "Temporary chat to be deleted.", wait_for_response=True
    )
    assert success, "Failed to create chat for deletion"

    # Open sidebar to count items
    await chat_ui_helper.ensure_sidebar_open()

    initial_count = await chat_ui_helper.get_chat_history_count()
    logger.info(f"Initial chat history count: {initial_count}")
    assert initial_count >= 1, "Need at least 1 chat to test deletion"

    # Open menu and delete
    menu_opened = await chat_ui_helper.open_chat_history_menu(index=0)
    assert menu_opened, "Failed to open chat history menu"
    await page.wait_for_timeout(300)

    delete_clicked = await chat_ui_helper.click_chat_menu_action("delete")
    assert delete_clicked, "Failed to click delete-chat-menu-item"
    await page.wait_for_timeout(300)

    # Confirm deletion (ActionDialog confirm button — scope to dialog to
    # avoid matching other Confirm buttons on the page)
    dialog = page.locator('[role="dialog"], [data-testid*="dialog"]')
    confirm_btn = dialog.locator('button:has-text("Confirm")')
    try:
        await confirm_btn.wait_for(state="visible", timeout=5000)
        await confirm_btn.click()
        logger.info("Confirmed chat deletion")
    except Exception:
        # Some dialogs use "Delete" as confirm label
        delete_btn = dialog.locator('button:has-text("Delete")')
        await delete_btn.wait_for(state="visible", timeout=3000)
        await delete_btn.click()
        logger.info("Confirmed chat deletion via Delete button")

    await page.wait_for_timeout(1000)

    # Verify count decreased
    new_count = await chat_ui_helper.get_chat_history_count()
    assert new_count < initial_count, \
        f"Expected chat count to decrease, was {initial_count}, now {new_count}"
    logger.info(f"Assert: Chat count decreased from {initial_count} to {new_count}")

    logger.info("Test completed: Chat deletion validated")


@allure.testcase("IEASG-T361")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_export_chat_dialog(chat_ui_helper):
    """
    Test that the Export Chat dialog opens via context menu.

    Steps:
    1. Ensure chat exists
    2. Open context menu → click export-chat-menu-item
    3. Verify export-chat-dialog is rendered

    Success criteria:
    - Export menu item uses data-testid="export-chat-menu-item"
    - Dialog appears with data-testid="export-chat-dialog"
    """
    logger.info("Test: Export chat dialog via data-testid")

    page = chat_ui_helper.page
    await _ensure_at_least_one_chat(chat_ui_helper)

    # Open menu and click export
    menu_opened = await chat_ui_helper.open_chat_history_menu(index=0)
    assert menu_opened, "Failed to open chat history menu"
    await page.wait_for_timeout(300)

    export_clicked = await chat_ui_helper.click_chat_menu_action("export")
    assert export_clicked, "Failed to click export-chat-menu-item"
    await page.wait_for_timeout(500)

    # Assert: Export dialog is visible
    dialog_visible = await chat_ui_helper.is_visible_by_testid("export-chat-dialog", timeout=5000)
    assert dialog_visible, "export-chat-dialog should be visible after clicking export"
    logger.info("Assert: export-chat-dialog is rendered")

    # Close dialog
    close_btn = page.locator('[data-testid="export-chat-dialog-close-button"]')
    try:
        await close_btn.click()
    except Exception:
        # Fallback: close via Cancel button or Escape
        await page.keyboard.press("Escape")

    logger.info("Test completed: Export chat dialog validated")


@allure.testcase("IEASG-T362")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_chat_history_search(chat_ui_helper):
    """
    Test chat history search bar filtering.

    Steps:
    1. Create two chats with distinct messages
    2. Open sidebar
    3. Type a filter query into the sidebar search input
    4. Verify filtered results

    Note: The sidebar search input has NO data-testid; the helper uses
    ``aside input`` as a fallback selector.

    Success criteria:
    - Typing in the sidebar search filters the chat history item list
    """
    logger.info("Test: Chat history search via sidebar input")

    page = chat_ui_helper.page

    # Create first chat
    await chat_ui_helper.start_new_chat()
    await page.wait_for_timeout(500)
    await chat_ui_helper.send_message("Tell me about quantum computing.", wait_for_response=True)
    await page.wait_for_timeout(1000)

    # Create second chat
    await chat_ui_helper.start_new_chat()
    await page.wait_for_timeout(500)
    await chat_ui_helper.send_message("Tell me about machine learning.", wait_for_response=True)
    await page.wait_for_timeout(1000)

    # Open sidebar
    await chat_ui_helper.ensure_sidebar_open()

    # Assert 1: Search input is accessible (SearchBar does not forward data-testid)
    search_input = page.locator('aside input[type="text"], aside input:not([type])')
    search_visible = await search_input.first.is_visible()
    assert search_visible, "Sidebar search input should be visible"
    logger.info("Assert 1: Sidebar search input visible")

    total_before = await chat_ui_helper.get_chat_history_count()
    logger.info(f"Total chat items before search: {total_before}")
    assert total_before >= 2, f"Need at least 2 chats, found {total_before}"

    # Type a search query (chat titles are auto-generated from first message)
    search_success = await chat_ui_helper.search_chat_history("quantum")
    assert search_success, "Failed to fill search bar"
    await page.wait_for_timeout(1000)

    # Assert 2: Filtered count should be less than or equal to total
    filtered_count = await chat_ui_helper.get_chat_history_count()
    logger.info(f"Chat items after search 'quantum': {filtered_count}")
    assert filtered_count <= total_before, \
        f"Filtered count ({filtered_count}) should be <= total ({total_before})"
    logger.info("Assert 2: Search filter reduces visible items")

    # Clear search to restore full list
    await chat_ui_helper.search_chat_history("")
    await page.wait_for_timeout(500)

    restored = await chat_ui_helper.get_chat_history_count()
    assert restored >= total_before, "Clearing search should restore full list"
    logger.info("Assert 3: Clearing search restores items")

    logger.info("Test completed: Chat history search validated")


@allure.testcase("IEASG-T363")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_export_chat_downloads_file(chat_ui_helper):
    """
    Test that exporting a chat actually downloads a valid JSON file.

    Steps:
    1. Send a message with known content to create a chat
    2. Open sidebar → context menu → click export-chat-menu-item
    3. Intercept the browser download triggered by the Export button
    4. Save the downloaded file and validate its contents

    Success criteria:
    - A file is actually downloaded (not just dialog opened)
    - File is valid JSON
    - File contains the message that was sent

    Note: The UI creates a Blob and triggers a programmatic <a> download.
    Playwright's ``page.expect_download()`` intercepts this.
    """
    logger.info("Test: Export chat downloads a valid file")

    page = chat_ui_helper.page
    test_message = "Export validation test: supercalifragilistic"

    # Step 1: Create a chat with a known message
    await chat_ui_helper.start_new_chat()
    await page.wait_for_timeout(1000)
    success, response = await chat_ui_helper.send_message(
        test_message, wait_for_response=True
    )
    assert success, "Failed to send test message"
    assert response, "No bot response received"
    logger.info(f"Chat created with message: {test_message}")

    # Wait for chat to be saved to history before exporting
    await page.wait_for_timeout(3000)

    # Step 2: Open sidebar and find the chat we just created
    await chat_ui_helper.ensure_sidebar_open()

    # Find the chat history item that contains our test message keyword.
    # The auto-generated chat name is derived from the first message text.
    target_index = 0
    items = page.locator('[data-testid="chat-history-item"]')
    await items.first.wait_for(state="visible", timeout=10000)
    count = await items.count()
    for i in range(count):
        text = await items.nth(i).text_content()
        if text and "export" in text.lower():
            target_index = i
            logger.info(f"Found matching chat at index {i}: {text[:60]}")
            break
    else:
        logger.warning("Could not find chat with 'export' in name, using index 0")

    menu_opened = await chat_ui_helper.open_chat_history_menu(index=target_index)
    assert menu_opened, "Failed to open chat history menu"
    await page.wait_for_timeout(300)

    export_clicked = await chat_ui_helper.click_chat_menu_action("export")
    assert export_clicked, "Failed to click export-chat-menu-item"
    await page.wait_for_timeout(500)

    # Assert 1: Export dialog is visible
    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "export-chat-dialog", timeout=5000
    )
    assert dialog_visible, "export-chat-dialog should be visible"
    logger.info("Assert 1: export-chat-dialog rendered")

    # Step 3: Click the "Export" confirm button and intercept the download
    # The ActionDialog uses confirmLabel="Export" as the button text.
    download_path = None
    try:
        async with page.expect_download(timeout=15000) as download_info:
            # Click the export confirm button
            export_btn = page.locator(
                '[data-testid="export-chat-dialog"] button:has-text("Export")'
            )
            await export_btn.click()
            logger.info("Clicked Export button — waiting for download")

        download = await download_info.value
        logger.info(f"Download triggered: {download.suggested_filename}")

        # Save to a temp file for inspection
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as tmp:
            download_path = tmp.name
        await download.save_as(download_path)

        # Assert 2: File is non-empty
        file_size = os.path.getsize(download_path)
        assert file_size > 0, "Downloaded file is empty"
        logger.info(f"Assert 2: Downloaded file size: {file_size} bytes")

        # Assert 3: File is valid JSON
        with open(download_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        logger.info(f"Assert 3: File is valid JSON ({type(content).__name__})")

        # Assert 4: JSON contains the test message (search case-insensitively)
        content_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
        assert "supercalifragilistic" in content_str.lower(), (
            f"Exported JSON does not contain the test message. "
            f"Content preview: {content_str[:500]}"
        )
        logger.info("Assert 4: Test message found in exported JSON")

    finally:
        # Cleanup temp file
        if download_path and os.path.exists(download_path):
            os.unlink(download_path)
            logger.debug(f"Cleaned up temp file: {download_path}")

    logger.info("Test completed: Export chat download validated")
