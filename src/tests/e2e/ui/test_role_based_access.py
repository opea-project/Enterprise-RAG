#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Role-based access control (RBAC) UI tests for the chatqna application.

Validates that the 3-tier role system (admin / maintainer / user) enforces
correct visibility and access control:

1. All roles can access /chat
2. Admin and maintainer see the ViewSwitchButton; regular user does not
3. Regular user is redirected away from /admin-panel
4. Admin sees all 3 admin-panel tabs
5. Maintainer sees only Control Plane and Data Ingestion tabs (no Telemetry)
"""

import logging

import allure
import pytest

from tests.e2e.ui.conftest import requires_chatqa
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

pytestmark = requires_chatqa


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _admin_panel_url() -> str:
    return f"https://{cfg.get('FQDN')}/admin-panel"


# ---------------------------------------------------------------------------
# 1. Chat access (all roles)
# ---------------------------------------------------------------------------

@allure.testcase("IEASG-T543")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_admin_can_access_chat(chat_ui_helper):
    """Admin lands on /chat after login."""
    assert "/chat" in chat_ui_helper.page.url, (
        f"Admin should be on /chat, got {chat_ui_helper.page.url}"
    )


@allure.testcase("IEASG-T544")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_maintainer_can_access_chat(chat_ui_helper_maintainer):
    """Maintainer lands on /chat after login."""
    assert "/chat" in chat_ui_helper_maintainer.page.url, (
        f"Maintainer should be on /chat, got {chat_ui_helper_maintainer.page.url}"
    )


@allure.testcase("IEASG-T545")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_user_can_access_chat(chat_ui_helper_user):
    """Regular user lands on /chat after login."""
    assert "/chat" in chat_ui_helper_user.page.url, (
        f"User should be on /chat, got {chat_ui_helper_user.page.url}"
    )


# ---------------------------------------------------------------------------
# 2. ViewSwitchButton visibility
# ---------------------------------------------------------------------------

@allure.testcase("IEASG-T546")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_admin_sees_view_switch_button(chat_ui_helper):
    """Admin sees the 'Switch to Admin Panel' button on /chat."""
    visible = await chat_ui_helper.is_visible_by_testid(
        "view-switch-btn--to-admin-panel", timeout=10000
    )
    assert visible, "Admin should see view-switch-btn--to-admin-panel"


@allure.testcase("IEASG-T547")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_maintainer_sees_view_switch_button(chat_ui_helper_maintainer):
    """Maintainer sees the 'Switch to Admin Panel' button on /chat."""
    visible = await chat_ui_helper_maintainer.is_visible_by_testid(
        "view-switch-btn--to-admin-panel", timeout=10000
    )
    assert visible, "Maintainer should see view-switch-btn--to-admin-panel"


@allure.testcase("IEASG-T548")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_user_does_not_see_view_switch_button(chat_ui_helper_user):
    """Regular user must NOT see the 'Switch to Admin Panel' button."""
    visible = await chat_ui_helper_user.is_visible_by_testid(
        "view-switch-btn--to-admin-panel", timeout=5000
    )
    assert not visible, "Regular user should NOT see view-switch-btn--to-admin-panel"


# ---------------------------------------------------------------------------
# 3. Admin panel access control
# ---------------------------------------------------------------------------

@allure.testcase("IEASG-T549")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_user_redirected_from_admin_panel(chat_ui_helper_user):
    """Regular user navigating to /admin-panel is redirected back to /chat."""
    page = chat_ui_helper_user.page
    await page.goto(_admin_panel_url())
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)

    assert "/chat" in page.url, (
        f"Regular user should be redirected to /chat, got {page.url}"
    )


# ---------------------------------------------------------------------------
# 4. Admin panel tab visibility — admin
# ---------------------------------------------------------------------------

@allure.testcase("IEASG-T550")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_admin_sees_all_admin_tabs(chat_ui_helper):
    """Admin sees all 3 tabs: control-plane, data-ingestion, telemetry-authentication."""
    nav_ok = await chat_ui_helper.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Admin failed to navigate to control-plane tab"

    page = chat_ui_helper.page
    tabs_container = page.locator('[data-testid="admin-panel-tabs"]')
    await tabs_container.wait_for(state="visible", timeout=10000)

    tab_labels = {
        "control-plane": "Control Plane",
        "data-ingestion": "Data Ingestion",
        "telemetry-authentication": "Telemetry & Authentication",
    }
    for tab_id, label in tab_labels.items():
        tab = tabs_container.locator('[role="tab"]').filter(has_text=label)
        assert await tab.count() > 0, f"Admin should see tab '{tab_id}' ('{label}')"
        logger.info(f"Admin sees tab: {tab_id}")


# ---------------------------------------------------------------------------
# 5. Admin panel tab visibility — maintainer
# ---------------------------------------------------------------------------

@allure.testcase("IEASG-T551")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_maintainer_sees_only_allowed_tabs(chat_ui_helper_maintainer):
    """Maintainer sees control-plane and data-ingestion, but NOT telemetry-authentication."""
    nav_ok = await chat_ui_helper_maintainer.navigate_to_admin_tab("control-plane")
    assert nav_ok, "Maintainer failed to navigate to control-plane tab"

    page = chat_ui_helper_maintainer.page
    tabs_container = page.locator('[data-testid="admin-panel-tabs"]')
    await tabs_container.wait_for(state="visible", timeout=10000)

    # Should see these tabs
    for tab_id, label in (("control-plane", "Control Plane"),
                          ("data-ingestion", "Data Ingestion")):
        tab = tabs_container.locator('[role="tab"]').filter(has_text=label)
        assert await tab.count() > 0, f"Maintainer should see tab '{tab_id}'"
        logger.info(f"Maintainer sees tab: {tab_id}")

    # Should NOT see telemetry-authentication
    telemetry_tab = tabs_container.locator('[role="tab"]').filter(
        has_text="Telemetry & Authentication"
    )
    assert await telemetry_tab.count() == 0, (
        "Maintainer should NOT see telemetry-authentication tab"
    )
    logger.info("Maintainer correctly denied telemetry-authentication tab")
