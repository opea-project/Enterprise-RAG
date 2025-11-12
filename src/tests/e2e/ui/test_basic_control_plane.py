#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
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

from validation.constants import ERAG_DOMAIN

logger = logging.getLogger(__name__)


# ============================================================================
# TEST CASES
# ============================================================================

@allure.testcase("IEASG-T283")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_control_plane_navigation(chat_ui_helper):
    """
    Test navigation to Control Plane via Admin Panel button.
    
    Steps:
    1. Login as admin (handled by fixture)
    2. Click button with aria-label="Switch to Admin Panel"
    3. Verify navigation to https://erag.com/admin-panel
    
    Success criteria:
    - Admin Panel button is found and clickable
    - URL changes to /admin-panel (Control Plane default page)
    """
    logger.info("Test 1: Control Plane Navigation")
    
    # Navigate to Control Plane
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    
    # Assert 1: Navigation completed successfully
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Assert 1: Navigation to Control Plane successful")
    
    # Assert 2: URL is correct (admin-panel is the Control Plane landing page)
    url_verified = await chat_ui_helper.verify_control_plane_url("/admin-panel")
    assert url_verified, f"URL verification failed, expected {ERAG_DOMAIN}/admin-panel"
    logger.info("Assert 2: Control Plane URL verified")
    
    logger.info("Test completed: Control Plane navigation validated")


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
    
    # Check if no-service-selected card is rendered using CSS class
    card_rendered = await chat_ui_helper.check_element_rendered(
        css_class="no-service-selected-card",
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
    
    # Check if control-plane-panel is rendered with children using CSS class
    panel_rendered = await chat_ui_helper.check_element_rendered(
        css_class="control-plane-panel",
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
    3. Check if div with class "chatqna-graph-legend" exists
    4. Verify it has child elements
    
    Success criteria:
    - ChatQnA graph legend element is visible
    - Legend contains child elements (legend items)
    
    Note: The UI uses 'chatqna-graph-legend' (not 'chatqa')
    """
    logger.info("Test 4: ChatQnA Graph Legend Rendering")
    
    # Navigate to Control Plane
    navigation_success = await chat_ui_helper.navigate_to_control_plane()
    assert navigation_success, "Failed to navigate to Control Plane"
    logger.info("Navigated to Control Plane")
    
    # Check if chatqna-graph-legend is rendered with children using CSS class
    legend_rendered = await chat_ui_helper.check_element_rendered(
        css_class="chatqna-graph-legend",
        check_children=True,
        timeout=10000
    )
    
    # Assert: Legend is rendered with children
    assert legend_rendered, "ChatQnA graph legend not rendered or has no children"
    logger.info("Assert: ChatQnA graph legend rendered with child elements")
    
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
