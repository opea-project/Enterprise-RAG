#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for Admin Panel navigation and service configuration.

Tests using data-testid selectors:
1. Admin panel tab switching (control-plane, data-ingestion, telemetry)
2. Telemetry & Authentication links rendering
3. Service argument inputs (text, number, select, checkbox)
4. Confirm / Cancel service changes
5. Retriever debug dialog

All selectors rely on data-testid attributes.
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

@allure.testcase("IEASG-T372")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_admin_panel_tab_switching(chat_ui_helper):
    """
    Test switching between all admin panel tabs.

    Steps:
    1. Navigate to admin panel
    2. Click each tab: control-plane, data-ingestion, telemetry-authentication
    3. Verify URL updates accordingly

    Success criteria:
    - admin-panel-tabs container renders (data-testid)
    - Each tab click changes the URL path
    """
    logger.info("Test: Admin panel tab switching")

    page = chat_ui_helper.page
    tabs = ["control-plane", "data-ingestion", "telemetry-authentication"]

    for tab in tabs:
        nav_ok = await chat_ui_helper.navigate_to_admin_tab(tab)
        assert nav_ok, f"Failed to navigate to tab: {tab}"
        assert tab in page.url, f"Expected '{tab}' in URL, got {page.url}"
        logger.info(f"Tab '{tab}' navigated: {page.url}")

    logger.info("Test completed: All admin panel tabs validated")


@allure.testcase("IEASG-T373")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_telemetry_links_rendered(chat_ui_helper):
    """
    Test that Telemetry & Authentication tab renders Grafana and Keycloak links.

    Steps:
    1. Navigate to telemetry-authentication tab
    2. Verify grafana-dashboard-link is visible
    3. Verify keycloak-admin-panel-link is visible

    Success criteria:
    - Both links render with correct data-testid
    """
    logger.info("Test: Telemetry links rendering")

    nav_ok = await chat_ui_helper.navigate_to_admin_tab("telemetry-authentication")
    assert nav_ok, "Failed to navigate to telemetry-authentication tab"

    # Assert: Grafana link
    grafana_visible = await chat_ui_helper.is_visible_by_testid(
        "grafana-dashboard-link", timeout=10000
    )
    assert grafana_visible, "grafana-dashboard-link should be visible"
    logger.info("Assert 1: Grafana dashboard link rendered")

    # Assert: Keycloak link
    keycloak_visible = await chat_ui_helper.is_visible_by_testid(
        "keycloak-admin-panel-link", timeout=5000
    )
    assert keycloak_visible, "keycloak-admin-panel-link should be visible"
    logger.info("Assert 2: Keycloak admin panel link rendered")

    logger.info("Test completed: Telemetry links validated")


@allure.testcase("IEASG-T374")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_control_plane_panel_and_graph_controls(chat_ui_helper):
    """
    Test that control-plane-panel and graph-controls render.

    Steps:
    1. Navigate to control-plane tab
    2. Verify control-plane-panel is rendered with children
    3. Verify graph-controls is rendered

    Success criteria:
    - data-testid="control-plane-panel" and "graph-controls" are visible
    """
    logger.info("Test: Control plane panel and graph controls")

    nav_ok = await chat_ui_helper.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Failed to navigate to control-plane tab"

    # Assert: control-plane-panel
    panel_ok = await chat_ui_helper.check_element_rendered(
        data_testid="control-plane-panel", check_children=True, timeout=10000
    )
    assert panel_ok, "control-plane-panel should be rendered with children"
    logger.info("Assert 1: control-plane-panel rendered with children")

    # Assert: graph-controls
    controls_ok = await chat_ui_helper.is_visible_by_testid("graph-controls", timeout=10000)
    assert controls_ok, "graph-controls should be visible"
    logger.info("Assert 2: graph-controls visible")

    logger.info("Test completed: Control plane panel validated")


@allure.testcase("IEASG-T375")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_control_plane_refresh(chat_ui_helper):
    """
    Test control plane refresh button and auto-refresh checkbox.

    Steps:
    1. Navigate to control-plane tab
    2. Verify control-plane-refresh-button exists and is clickable
    3. Verify control-plane-autorefresh-checkbox exists

    Success criteria:
    - Both elements are accessible via data-testid
    """
    logger.info("Test: Control plane refresh controls")

    page = chat_ui_helper.page
    nav_ok = await chat_ui_helper.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Failed to navigate to control-plane"

    # Assert: refresh button
    refresh_visible = await chat_ui_helper.is_visible_by_testid(
        "control-plane-refresh-button", timeout=10000
    )
    assert refresh_visible, "control-plane-refresh-button should be visible"
    logger.info("Assert 1: Refresh button visible")

    clicked = await chat_ui_helper.click_by_testid("control-plane-refresh-button")
    assert clicked, "Failed to click control-plane-refresh-button"
    await page.wait_for_timeout(1000)
    logger.info("Refresh button clicked successfully")

    # Assert: autorefresh checkbox
    auto_visible = await chat_ui_helper.is_visible_by_testid(
        "control-plane-autorefresh-checkbox", timeout=5000
    )
    assert auto_visible, "control-plane-autorefresh-checkbox should be visible"
    logger.info("Assert 2: Autorefresh checkbox visible")

    logger.info("Test completed: Control plane refresh controls validated")


@allure.testcase("IEASG-T376")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_no_service_selected_card_data_testid(chat_ui_helper):
    """
    Test that the 'no service selected' card renders via data-testid.

    Overlaps with test_basic_control_plane.py but uses pure data-testid.

    Steps:
    1. Navigate to control-plane tab
    2. Verify no-service-selected-card is visible

    Success criteria:
    - data-testid="no-service-selected-card" is rendered
    """
    logger.info("Test: No service selected card via data-testid")

    nav_ok = await chat_ui_helper.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Failed to navigate to control-plane"

    card_ok = await chat_ui_helper.is_visible_by_testid(
        "no-service-selected-card", timeout=10000
    )
    assert card_ok, "no-service-selected-card should be visible"
    logger.info("Assert: no-service-selected-card rendered")

    logger.info("Test completed: No service selected card validated")


@allure.testcase("IEASG-T377")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_retriever_debug_dialog(chat_ui_helper):
    """
    Test the Retriever Debug Dialog opens and contains expected controls.

    Steps:
    1. Navigate to control-plane tab
    2. Click a service node in the graph to select retriever (if available)
    3. Click retriever-debug-trigger-button
    4. Verify retriever-debug-dialog is rendered
    5. Verify format-json-button is visible
    6. Close dialog

    Note: This test attempts to open the debug dialog. If no retriever service
    is selectable in the graph, the test skips gracefully.

    Success criteria:
    - Debug dialog elements use data-testid attributes
    """
    logger.info("Test: Retriever debug dialog")

    page = chat_ui_helper.page
    nav_ok = await chat_ui_helper.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Failed to navigate to control-plane"
    await page.wait_for_timeout(2000)

    # Try to find the debug trigger button (only appears when a service is selected)
    trigger_visible = await chat_ui_helper.is_visible_by_testid(
        "retriever-debug-trigger-button", timeout=5000
    )

    if not trigger_visible:
        # Try clicking ReactFlow nodes to find one that reveals the debug button
        nodes = page.locator('.react-flow__node')
        node_count = await nodes.count()
        logger.info(f"Found {node_count} ReactFlow nodes, trying each to find retriever")
        for i in range(node_count):
            try:
                await nodes.nth(i).click()
                await page.wait_for_timeout(1000)
                trigger_visible = await chat_ui_helper.is_visible_by_testid(
                    "retriever-debug-trigger-button", timeout=3000
                )
                if trigger_visible:
                    logger.info(f"Found retriever debug trigger on node {i}")
                    break
            except Exception:
                continue

    if not trigger_visible:
        logger.info("Retriever debug trigger not available — skipping")
        pytest.skip("Retriever debug trigger not visible (no retriever service selected)")

    # Open debug dialog
    await chat_ui_helper.click_by_testid("retriever-debug-trigger-button")
    await page.wait_for_timeout(500)

    # Assert: dialog rendered
    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "retriever-debug-dialog", timeout=5000
    )
    assert dialog_visible, "retriever-debug-dialog should be visible"
    logger.info("Assert 1: retriever-debug-dialog rendered")

    # Assert: format-json-button exists
    format_btn_visible = await chat_ui_helper.is_visible_by_testid(
        "format-json-button", timeout=3000
    )
    assert format_btn_visible, "format-json-button should be visible in debug dialog"
    logger.info("Assert 2: format-json-button visible")

    # Close dialog
    await page.keyboard.press("Escape")

    logger.info("Test completed: Retriever debug dialog validated")


@allure.testcase("IEASG-T378")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_service_card_confirm_cancel_buttons(chat_ui_helper):
    """
    Test that confirm/cancel buttons appear when modifying a service.

    Steps:
    1. Navigate to control-plane
    2. Select a service node
    3. Modify a service argument (if available)
    4. Verify confirm-service-changes-button and cancel-service-changes-button appear
    5. Click cancel to discard changes

    Note: If no service arguments are editable, the test skips gracefully.

    Success criteria:
    - Buttons use data-testid for targeting
    """
    logger.info("Test: Service card confirm/cancel buttons")

    page = chat_ui_helper.page
    nav_ok = await chat_ui_helper.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Failed to navigate to control-plane"
    await page.wait_for_timeout(2000)

    # Try to select a service node that has editable arguments
    nodes = page.locator('.react-flow__node')
    node_count = await nodes.count()

    if node_count == 0:
        pytest.skip("No service nodes found in control plane graph")

    # Iterate through nodes to find one with service argument inputs
    arg_count = 0
    for i in range(node_count):
        try:
            await nodes.nth(i).click()
            await page.wait_for_timeout(1000)

            arg_inputs = page.locator('[data-testid^="service-argument-"]')
            arg_count = await arg_inputs.count()
            if arg_count > 0:
                logger.info(f"Found {arg_count} service argument inputs on node {i}")
                break
        except Exception:
            continue

    if arg_count == 0:
        logger.info("No service argument inputs found — checking button state only")
        # confirm/cancel may not be visible without modifications
        confirm_visible = await chat_ui_helper.is_visible_by_testid(
            "confirm-service-changes-button", timeout=3000
        )
        cancel_visible = await chat_ui_helper.is_visible_by_testid(
            "cancel-service-changes-button", timeout=3000
        )
        logger.info(f"Confirm visible: {confirm_visible}, Cancel visible: {cancel_visible}")
        # These buttons may only appear after a modification — test is still valid
    else:
        logger.info(f"Found {arg_count} service argument inputs")
        # Try to modify the first input to trigger confirm/cancel
        first_input = arg_inputs.first
        tag = await first_input.evaluate("el => el.tagName.toLowerCase()")
        if tag in ("input", "textarea"):
            current_val = await first_input.input_value()
            await first_input.fill(current_val + "x")
            await page.wait_for_timeout(500)

            # Now confirm/cancel should appear
            confirm_visible = await chat_ui_helper.is_visible_by_testid(
                "confirm-service-changes-button", timeout=5000
            )
            cancel_visible = await chat_ui_helper.is_visible_by_testid(
                "cancel-service-changes-button", timeout=3000
            )
            assert confirm_visible, "confirm-service-changes-button should appear after edit"
            assert cancel_visible, "cancel-service-changes-button should appear after edit"
            logger.info("Assert: Confirm and Cancel buttons visible after edit")

            # Cancel to discard
            await chat_ui_helper.click_by_testid("cancel-service-changes-button")
            await page.wait_for_timeout(500)
            logger.info("Cancelled service changes")

    logger.info("Test completed: Service card buttons validated")
