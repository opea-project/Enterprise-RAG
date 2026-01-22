#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for Control Plane basic functionality.

This module contains tests for validating:
1. Navigation to Control Plane
2. No service selected card rendering
3. Control Plane panel rendering with child elements
4. ChatQA graph legend rendering
5. Zoom controls (Zoom In, Zoom Out, Fit View) functionality

These tests ensure the Control Plane interface renders correctly
and interactive elements are functional.
"""

import allure
import logging
import pytest

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Skip all tests if chatqa pipeline is not deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        break
else:
    pytestmark = pytest.mark.skip(reason="ChatQA pipeline is not deployed")


# ============================================================================
# TEST CASES
# ============================================================================

@allure.testcase("IEASG-T283")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_control_plane_navigation(chat_ui_helper):
    """
    Test navigation to Control Plane and back to Chat using data-testid.
    
    Steps:
    1. Login as admin (handled by fixture)
    2. Verify starting in Chat view
    3. Click view switch button (data-testid="view-switch-btn--to-admin-panel")
    4. Verify navigation to admin-panel
    5. Click view switch button (data-testid="view-switch-btn--to-chat")
    6. Verify navigation back to chat
    
    Success criteria:
    - Navigation to Control Plane succeeds with correct data-testid
    - URL changes to /admin-panel
    - Navigation back to Chat succeeds with correct data-testid
    - URL changes back to /chat
    """
    logger.info("Test 1: Control Plane Navigation (round-trip)")
    
    page = chat_ui_helper.page
    
    # Verify we're starting in Chat view
    assert "/chat" in page.url, "Should start in Chat view"
    logger.info("Assert 1: Starting in Chat view")
    
    # Navigate to Control Plane using data-testid
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    
    # Assert 2: Navigation completed successfully
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Assert 2: Navigation to Control Plane successful")
    
    # Assert 3: URL is correct (admin-panel is the Control Plane landing page)
    url_verified = await chat_ui_helper.verify_control_plane_url("/admin-panel/control-plane")
    assert url_verified, "URL verification failed, expected /admin-panel/control-plane"
    logger.info("Assert 3: Control Plane URL verified")
    
    # Navigate back to Chat using data-testid
    navigation_success = await chat_ui_helper.navigate_to_chat()
    assert navigation_success, "Failed to navigate back to Chat"
    logger.info("Assert 4: Successfully navigated back to Chat")
    
    # Verify URL changed back to chat
    assert "/chat" in page.url, "Should be back in Chat view"
    logger.info("Assert 5: URL updated back to chat")
    
    logger.info("Test completed: Control Plane round-trip navigation validated")


@allure.testcase("IEASG-T284")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_no_service_selected_card(chat_ui_helper):
    """
    Test if 'no-service-selected-card' is rendered.
    
    Steps:
    1. Login as admin (handled by fixture)
    2. Navigate to Control Plane
    3. Check if element with class 'no-service-selected-card' exists
    
    Success criteria:
    - No service selected card is visible in the UI
    """
    logger.info("Test 2: No Service Selected Card")
    
    # Navigate to Control Plane
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Navigated to Control Plane")
    
    # Check if no-service-selected card is rendered using data-testid
    card_rendered = await chat_ui_helper.check_element_rendered(
        data_testid="no-service-selected-card",
        timeout=10000
    )
    
    # Assert: Card is rendered
    assert card_rendered, "No service selected card not found in the UI"
    logger.info("Assert: No service selected card is rendered")
    
    logger.info("Test completed: No service selected card validated")


@allure.testcase("IEASG-T285")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_control_plane_panel_rendered(chat_ui_helper):
    """
    Test if Control Plane panel is rendered with child elements.
    
    Steps:
    1. Login as admin (handled by fixture)
    2. Navigate to Control Plane
    3. Check if div with class "control-plane-panel" exists
    4. Verify it has child elements
    
    Success criteria:
    - Control plane panel element is visible
    - Panel contains child elements
    """
    logger.info("Test 3: Control Plane Panel Rendering")
    
    # Navigate to Control Plane
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Navigated to Control Plane")
    
    # Check if control-plane-panel is rendered with children using data-testid
    panel_rendered = await chat_ui_helper.check_element_rendered(
        data_testid="control-plane-panel",
        check_children=True,
        timeout=10000
    )
    
    # Assert: Panel is rendered with children
    assert panel_rendered, "Control Plane panel not rendered or has no children"
    logger.info("Assert: Control Plane panel rendered with child elements")
    
    logger.info("Test completed: Control Plane panel validated")


@allure.testcase("IEASG-T286")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_chatqa_graph_legend_rendered(chat_ui_helper):
    """
    Test if ChatQnA graph legend is rendered with child elements.
    
    Steps:
    1. Login as admin (handled by fixture)
    2. Navigate to Control Plane
    3. Check if div with class "graph-legend" exists
    4. Verify it has child elements
    
    Success criteria:
    - Graph legend element is visible
    - Legend contains child elements (legend items)
    
    Note: The UI uses 'graph-legend' class for the service status legend
    """
    logger.info("Test 4: ChatQnA Graph Legend Rendering")
    
    # Navigate to Control Plane
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Navigated to Control Plane")
    
    # Check if graph-legend is rendered with children using data-testid
    legend_rendered = await chat_ui_helper.check_element_rendered(
        data_testid="graph-legend",
        check_children=True,
        timeout=10000
    )
    
    # Assert: Legend is rendered with children
    assert legend_rendered, "Graph legend not rendered or has no children"
    logger.info("Assert: Graph legend rendered with child elements")
    
    logger.info("Test completed: ChatQnA graph legend validated")


@allure.testcase("IEASG-T287")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_control_plane_zoom_controls(chat_ui_helper):
    """
    Test if Control Plane zoom controls are rendered and functional.
    
    Steps:
    1. Login as admin (handled by fixture)
    2. Navigate to Control Plane
    3. Locate ReactFlow Controls panel
    4. Verify Zoom In, Zoom Out, and Fit View buttons exist
    5. Click each button to test functionality
    
    Success criteria:
    - ReactFlow Controls panel is visible
    - All three zoom control buttons are visible and clickable
    - Clicking buttons doesn't cause errors
    
    Note: ReactFlow v12 uses .react-flow__controls with button.react-flow__controls-button
    """
    logger.info("Test 5: Control Plane Zoom Controls")
    
    # Navigate to Control Plane
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Navigated to Control Plane")
    
    page = chat_ui_helper.page
    
    # Wait for ReactFlow to load and render controls
    await page.wait_for_timeout(2000)
    
    # Check if ReactFlow controls panel exists
    controls_panel = page.locator('.react-flow__controls')
    try:
        await controls_panel.wait_for(state="visible", timeout=10000)
        logger.info("ReactFlow controls panel found")
    except Exception as e:
        logger.error(f"ReactFlow controls panel not found: {e}")
        pytest.fail("ReactFlow controls panel not found")
    
    # Get all control buttons
    control_buttons = page.locator('.react-flow__controls button.react-flow__controls-button')
    button_count = await control_buttons.count()
    
    # Assert: At least 3 buttons exist (zoom-in, zoom-out, fit-view, and possibly others)
    assert button_count >= 3, f"Expected at least 3 control buttons, found {button_count}"
    logger.info(f"Found {button_count} control buttons in ReactFlow controls")
    
    # Test each button - ReactFlow typically has buttons in order: zoom-in, zoom-out, fit-view, interactive
    button_names = ["Zoom In", "Zoom Out", "Fit View"]
    for i in range(min(3, button_count)):  # Test first 3 buttons
        try:
            button = control_buttons.nth(i)
            
            # Assert: Button is visible
            await button.wait_for(state="visible", timeout=5000)
            logger.info(f"Assert: {button_names[i]} button (index {i}) is visible")
            
            # Assert: Button is enabled
            is_enabled = await button.is_enabled()
            assert is_enabled, f"{button_names[i]} button is disabled"
            logger.info(f"Assert: {button_names[i]} button is enabled")
            
            # Click button to test functionality
            await button.click()
            await page.wait_for_timeout(500)  # Wait for potential animations
            logger.info(f"Successfully clicked {button_names[i]} button")
            
        except Exception as e:
            logger.error(f"Failed to verify {button_names[i]} button: {e}")
            pytest.fail(f"{button_names[i]} button verification failed: {e}")
    
    logger.info("Assert: All zoom controls are functional")
    logger.info("Test completed: Control Plane zoom controls validated")


@allure.testcase("IEASG-T288")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_stop_button_during_streaming(chat_ui_helper):
    """
    Test that stop button appears and can interrupt streaming response.
    
    Steps:
    1. Send a prompt that generates a long response
    2. Verify stop button appears (data-testid="prompt-stop-button")
    3. Click stop button
    4. Verify response generation stops and send button reappears
    
    Success criteria:
    - Stop button is rendered during streaming with correct data-testid
    - Stop button is clickable
    - Response stops when button is clicked
    - Send button reappears after stopping
    """
    logger.info("Test 6: Stop Button During Streaming")
    
    # Send a prompt that will generate a long response
    long_prompt = "Write a detailed 500-word essay about artificial intelligence and its impact on society."
    
    page = chat_ui_helper.page
    
    # Fill textarea using data-testid
    textarea = page.locator('[data-testid="prompt-input-textarea"]')
    await textarea.fill(long_prompt)
    logger.info("Filled textarea with long prompt")
    
    # Click send button using data-testid
    send_button = page.locator('[data-testid="prompt-send-button"]')
    await send_button.click()
    logger.info("Clicked send button")
    
    # Wait for stop button to appear using data-testid
    stop_button = page.locator('[data-testid="prompt-stop-button"]')
    try:
        await stop_button.wait_for(state="visible", timeout=5000)
        logger.info("Assert 1: Stop button appeared during streaming")
    except Exception as e:
        logger.error(f"Stop button did not appear: {e}")
        pytest.fail("Stop button should appear during response streaming")
    
    # Assert 2: Stop button is enabled
    is_enabled = await stop_button.is_enabled()
    assert is_enabled, "Stop button should be enabled"
    logger.info("Assert 2: Stop button is enabled")
    
    # Click stop button
    await stop_button.click()
    logger.info("Clicked stop button")
    
    # Wait a moment for the stop to take effect
    await page.wait_for_timeout(1000)
    
    # Verify stop button is gone (replaced by send button)
    send_button_visible = await send_button.is_visible()
    assert send_button_visible, "Send button should reappear after stopping"
    logger.info("Assert 3: Send button reappeared after stop")
    
    logger.info("Test completed: Stop button functionality validated")
