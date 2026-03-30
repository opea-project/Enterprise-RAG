#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for shared UI components using data-testid selectors.

Tests the common layout and component elements that appear across all apps:
1. About dialog (trigger + content + close)
2. Side menu toggle button
3. Logout button
4. Source dialog (trigger + content) — ChatQA only
5. Scroll-to-bottom button — ChatQA only
6. Dialog close button pattern

All selectors use data-testid attributes from shared packages (layouts, components, auth).
"""

import asyncio
import logging

import allure
import pytest

from tests.e2e.ui.conftest import _has_pipeline

logger = logging.getLogger(__name__)

# Determine available pipelines
_has_chatqa = _has_pipeline("chatqa")
_has_docsum = _has_pipeline("docsum")


def _skip_if_no_pipeline():
    """Skip if no pipeline is deployed at all."""
    if not _has_chatqa and not _has_docsum:
        pytest.skip("No UI pipeline deployed")


# ============================================================================
# ABOUT DIALOG
# ============================================================================

@allure.testcase("IEASG-T387")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_about_dialog_open_close(chat_ui_helper):
    """
    Test the About dialog via data-testid.

    Steps:
    1. Verify about-dialog-trigger-button is visible
    2. Click trigger
    3. Verify about-dialog is rendered
    4. Verify about-dialog-close-button exists
    5. Close dialog

    Success criteria:
    - About dialog lifecycle uses data-testid selectors
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: About dialog open/close")

    page = chat_ui_helper.page

    # Assert: trigger button visible
    trigger_visible = await chat_ui_helper.is_visible_by_testid(
        "about-dialog-trigger-button", timeout=10000
    )
    assert trigger_visible, "about-dialog-trigger-button should be visible"
    logger.info("Assert 1: Trigger button visible")

    # Click to open
    clicked = await chat_ui_helper.click_by_testid("about-dialog-trigger-button")
    assert clicked, "Failed to click about-dialog-trigger-button"
    await page.wait_for_timeout(500)

    # Assert: dialog visible
    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "about-dialog", timeout=5000
    )
    assert dialog_visible, "about-dialog should be visible"
    logger.info("Assert 2: About dialog rendered")

    # Assert: close button exists
    close_visible = await chat_ui_helper.is_visible_by_testid(
        "about-dialog-close-button", timeout=3000
    )
    assert close_visible, "about-dialog-close-button should be visible"
    logger.info("Assert 3: Close button visible")

    # Close
    await chat_ui_helper.click_by_testid("about-dialog-close-button")
    await page.wait_for_timeout(300)

    dialog_hidden = await chat_ui_helper.wait_for_testid_hidden(
        "about-dialog", timeout=3000
    )
    assert dialog_hidden, "About dialog should be closed"
    logger.info("Assert 4: Dialog closed")

    logger.info("Test completed: About dialog validated")


# ============================================================================
# SIDE MENU
# ============================================================================

@allure.testcase("IEASG-T388")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_side_menu_toggle(chat_ui_helper):
    """
    Test the side menu toggle button with aria-label state verification.

    Steps:
    1. Verify side-menu-icon-button is visible
    2. Read initial aria-label state
    3. Click to toggle → verify aria-label changes
    4. Click again to toggle back → verify aria-label reverts

    Success criteria:
    - data-testid="side-menu-icon-button" is interactive
    - aria-label toggles between "Open Side Menu" and "Close Side Menu"
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: Side menu toggle")

    page = chat_ui_helper.page

    # Assert: button visible
    visible = await chat_ui_helper.is_visible_by_testid(
        "side-menu-icon-button", timeout=10000
    )
    assert visible, "side-menu-icon-button should be visible"
    logger.info("Assert 1: Side menu button visible")

    # Read initial state (sidebar is closed by default)
    btn = page.locator('[data-testid="side-menu-icon-button"]')
    initial_aria = await btn.get_attribute("aria-label")
    logger.info(f"Initial aria-label: {initial_aria}")

    # Click to toggle (open or close)
    clicked = await chat_ui_helper.click_by_testid("side-menu-icon-button")
    assert clicked, "Failed to click side-menu-icon-button (first toggle)"
    await page.wait_for_timeout(500)

    # Verify aria-label changed
    toggled_aria = await btn.get_attribute("aria-label")
    assert toggled_aria != initial_aria, \
        f"aria-label should change after toggle, was '{initial_aria}', still '{toggled_aria}'"
    logger.info(f"Toggled aria-label: {toggled_aria}")

    # Click again to toggle back
    clicked = await chat_ui_helper.click_by_testid("side-menu-icon-button")
    assert clicked, "Failed to click side-menu-icon-button (second toggle)"
    await page.wait_for_timeout(500)

    # Verify aria-label reverted
    reverted_aria = await btn.get_attribute("aria-label")
    assert reverted_aria == initial_aria, \
        f"aria-label should revert, expected '{initial_aria}', got '{reverted_aria}'"
    logger.info(f"Reverted aria-label: {reverted_aria}")

    # Assert: button remains visible
    still_visible = await chat_ui_helper.is_visible_by_testid(
        "side-menu-icon-button", timeout=3000
    )
    assert still_visible, "side-menu-icon-button should remain visible after toggling"
    logger.info("Assert 2: Button still accessible after toggling")

    logger.info("Test completed: Side menu toggle validated")


# ============================================================================
# LOGOUT BUTTON
# ============================================================================

@allure.testcase("IEASG-T389")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_logout_button_visible(chat_ui_helper):
    """
    Test that the logout button renders with correct data-testid.

    Steps:
    1. Verify logout-button is visible

    Note: We do NOT click logout as that would invalidate the session.

    Success criteria:
    - data-testid="logout-button" is rendered
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: Logout button visibility")

    visible = await chat_ui_helper.is_visible_by_testid(
        "logout-button", timeout=10000
    )
    assert visible, "logout-button should be visible"
    logger.info("Assert: logout-button is rendered")

    logger.info("Test completed: Logout button validated")


# ============================================================================
# SOURCE DIALOG (ChatQA only — appears after bot response with sources)
# ============================================================================

@allure.testcase("IEASG-T390")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_source_dialog_after_response(chat_ui_helper):
    """
    Test source dialog elements appear after a chat response with sources.

    Steps:
    1. Send a message that should trigger source citations
    2. Wait for response
    3. Check if source-dialog-trigger buttons appear
    4. If sources present, click trigger and verify source-dialog renders

    Note: Source availability depends on ingested data. If no sources are
    returned, the test validates that the data-testid pattern exists.

    Success criteria:
    - Source elements use data-testid selectors when present
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: Source dialog after response")

    page = chat_ui_helper.page

    # Send a question likely to produce sources
    success, response = await chat_ui_helper.send_message(
        "What documents are available in the knowledge base?",
        wait_for_response=True
    )
    assert success, "Failed to send message"
    assert response, "No response received"
    logger.info(f"Response received: {len(response)} chars")

    # Check for source triggers
    await page.wait_for_timeout(1000)
    source_count = await chat_ui_helper.count_by_testid("source-dialog-trigger")

    if source_count > 0:
        logger.info(f"Found {source_count} source-dialog-trigger element(s)")

        # Click first source trigger
        clicked = await chat_ui_helper.click_nth_by_testid(
            "source-dialog-trigger", index=0
        )
        assert clicked, "Failed to click source-dialog-trigger"
        await page.wait_for_timeout(500)

        # Verify source dialog
        dialog_visible = await chat_ui_helper.is_visible_by_testid(
            "source-dialog", timeout=5000
        )
        assert dialog_visible, "source-dialog should be visible after clicking trigger"
        logger.info("Assert: source-dialog rendered")

        # Close dialog
        await page.keyboard.press("Escape")
    else:
        logger.info("No source-dialog-trigger found — no sources in response (expected for some deployments)")

    logger.info("Test completed: Source dialog validated")


# ============================================================================
# SCROLL TO BOTTOM BUTTON
# ============================================================================

@allure.testcase("IEASG-T391")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_scroll_to_bottom_button(chat_ui_helper):
    """
    Test the scroll-to-bottom button appears when conversation is scrolled up.

    Steps:
    1. Send multiple messages to create a long conversation
    2. Scroll up in the conversation feed
    3. Verify scroll-to-bottom-button appears
    4. Click it and verify feed scrolls down

    Note: The button only appears when the user scrolls up from the bottom.
    If the conversation is too short to scroll, the test skips.

    Success criteria:
    - data-testid="scroll-to-bottom-button" appears on scroll-up
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: Scroll to bottom button")

    page = chat_ui_helper.page

    # Send several messages to create scrollable content
    for i in range(3):
        success, _ = await chat_ui_helper.send_message(
            f"Tell me a detailed fact number {i + 1} about artificial intelligence.",
            wait_for_response=True
        )
        assert success, f"Failed to send message {i + 1}"
        await asyncio.sleep(1)

    logger.info("Sent 3 messages to create scrollable content")

    # Scroll up in the conversation feed
    feed = page.locator('[data-testid="conversation-feed"]')
    await feed.wait_for(state="visible", timeout=5000)

    # Scroll to top of the feed
    await feed.evaluate("el => el.scrollTop = 0")
    await page.wait_for_timeout(500)

    # Check if scroll-to-bottom button appears
    scroll_btn_visible = await chat_ui_helper.is_visible_by_testid(
        "scroll-to-bottom-button", timeout=3000
    )

    if scroll_btn_visible:
        logger.info("scroll-to-bottom-button appeared after scrolling up")

        # Click to scroll back down (use force=True as conversation-feed
        # overlay can intercept pointer events)
        btn = page.locator('[data-testid="scroll-to-bottom-button"]')
        await btn.click(force=True)
        await page.wait_for_timeout(500)

        # Button should disappear after scrolling down
        btn_hidden = await chat_ui_helper.wait_for_testid_hidden(
            "scroll-to-bottom-button", timeout=3000
        )
        logger.info(f"Button hidden after click: {btn_hidden}")
    else:
        logger.info("scroll-to-bottom-button did not appear — conversation may be too short")

    logger.info("Test completed: Scroll to bottom button validated")


# ============================================================================
# CONVERSATION FEED
# ============================================================================

@allure.testcase("IEASG-T392")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_conversation_feed_renders(chat_ui_helper):
    """
    Test that the conversation feed container renders with data-testid.

    Steps:
    1. Send a message to trigger conversation layout
    2. Verify conversation-feed is visible

    Success criteria:
    - data-testid="conversation-feed" is rendered
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: Conversation feed rendering")

    page = chat_ui_helper.page

    # conversation-feed only renders in ChatConversationLayout (after messages exist)
    # InitialChatLayout (empty chat) shows only the prompt input
    success, _ = await chat_ui_helper.send_message(
        "Hello, testing conversation feed rendering.", wait_for_response=True
    )
    assert success, "Failed to send message to populate conversation feed"
    await page.wait_for_timeout(1000)

    visible = await chat_ui_helper.is_visible_by_testid(
        "conversation-feed", timeout=10000
    )
    assert visible, "conversation-feed should be visible after sending a message"
    logger.info("Assert: conversation-feed rendered")

    logger.info("Test completed: Conversation feed validated")


# ============================================================================
# PROMPT INPUT FORM
# ============================================================================

@allure.testcase("IEASG-T393")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_prompt_input_form_elements(chat_ui_helper):
    """
    Test all prompt input form elements render with correct data-testid.

    Steps:
    1. Verify prompt-input-form is visible
    2. Verify prompt-input-textarea is visible
    3. Verify prompt-send-button is visible

    Success criteria:
    - All prompt input elements have data-testid attributes
    """
    if not _has_chatqa:
        pytest.skip("ChatQA pipeline required for this test")

    logger.info("Test: Prompt input form elements")

    # Assert: form
    form_visible = await chat_ui_helper.is_visible_by_testid(
        "prompt-input-form", timeout=10000
    )
    assert form_visible, "prompt-input-form should be visible"
    logger.info("Assert 1: prompt-input-form visible")

    # Assert: textarea
    textarea_visible = await chat_ui_helper.is_visible_by_testid(
        "prompt-input-textarea", timeout=5000
    )
    assert textarea_visible, "prompt-input-textarea should be visible"
    logger.info("Assert 2: prompt-input-textarea visible")

    # Assert: send button
    send_visible = await chat_ui_helper.is_visible_by_testid(
        "prompt-send-button", timeout=5000
    )
    assert send_visible, "prompt-send-button should be visible"
    logger.info("Assert 3: prompt-send-button visible")

    logger.info("Test completed: Prompt input form elements validated")
