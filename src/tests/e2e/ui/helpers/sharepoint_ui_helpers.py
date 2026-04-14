#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Shared Playwright helpers for SharePoint UI tests.

Extracted from test_sharepoint_sites.py and test_sharepoint_sso.py to
eliminate duplication.  All functions accept a ``ChatUIHelper`` (or
equivalent) plus a Playwright ``Page`` obtained via ``helper.page``.
"""

import logging

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DIALOG_TIMEOUT_MS = 10_000
SYNC_CHECK_TIMEOUT_MS = 30_000

# Emoji indicators used by the UI for SharePoint sources / destinations.
SP_GLOBE_EMOJI = "\U0001f310"  # globe — SharePoint destination in upload dropdown
SP_LINK_EMOJI = "\U0001f517"  # link  — SharePoint source in files table


# ---------------------------------------------------------------------------
# react-aria workarounds
# ---------------------------------------------------------------------------


async def force_reset_body(page):
    """Reset body state clobbered by react-aria ModalOverlay.

    react-aria sets ``pointer-events: none`` and ``aria-hidden="true"`` on
    ``<body>`` when a modal is open and sometimes fails to clean up.
    """
    await page.evaluate("""() => {
        document.querySelectorAll('[data-rac].react-aria-ModalOverlay')
            .forEach(el => el.remove());
        document.body.style.pointerEvents = '';
        document.body.removeAttribute('aria-hidden');
    }""")
    await page.wait_for_timeout(300)


async def dismiss_any_overlay(helper):
    """Dismiss modal overlays that may block interaction.

    Handles the react-aria ModalOverlay that intercepts pointer events and
    sets ``pointer-events: none`` on ``<body>``.  Also dismisses any visible
    SharePoint/upload dialogs left over from a previous step.
    """
    page = helper.page
    overlay = page.locator("[data-rac].react-aria-ModalOverlay")
    if await overlay.count() > 0:
        logger.debug("Dismissing lingering modal overlay via Escape + JS cleanup")
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1000)
        if await overlay.count() > 0:
            await force_reset_body(page)
    else:
        body_pe = await page.evaluate("getComputedStyle(document.body).pointerEvents")
        if body_pe == "none":
            logger.debug("Resetting stuck body pointer-events: none")
            await page.evaluate("document.body.style.pointerEvents = ''")
            await page.wait_for_timeout(300)

    # Dismiss any visible dialogs that may block navigation
    for testid in ["sharepoint-sites-dialog", "upload-dialog"]:
        if await helper.is_visible_by_testid(testid, timeout=500):
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)


async def js_click_testid(page, testid: str, timeout: int = 5000):
    """Click an element by data-testid using JavaScript (bypasses pointer-events)."""
    locator = page.locator(f'[data-testid="{testid}"]')
    await locator.wait_for(state="visible", timeout=timeout)
    await locator.evaluate("el => el.click()")
    logger.debug(f"JS-clicked [data-testid='{testid}']")


# ---------------------------------------------------------------------------
# SharePoint Sites dialog
# ---------------------------------------------------------------------------


async def open_sharepoint_dialog(helper) -> bool:
    """Navigate to Data Ingestion tab, click the SharePoint Sites trigger,
    and wait for the dialog to appear.

    Returns True if the dialog is visible, False otherwise.
    """
    page = helper.page
    await dismiss_any_overlay(helper)
    await force_reset_body(page)

    if not await helper.navigate_to_admin_tab("data-ingestion"):
        logger.error("Failed to navigate to data-ingestion tab")
        return False

    try:
        await js_click_testid(page, "trigger-sharepoint-sites-button")
    except Exception:
        logger.error("Failed to click trigger-sharepoint-sites-button")
        return False

    visible = await helper.is_visible_by_testid(
        "sharepoint-sites-dialog", timeout=DIALOG_TIMEOUT_MS
    )
    if not visible:
        logger.error("sharepoint-sites-dialog did not appear")
        return False

    await page.wait_for_timeout(500)
    return True


async def close_sharepoint_dialog(helper) -> bool:
    """Close the SharePoint Sites dialog via Escape and reset body state."""
    page = helper.page
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    hidden = await helper.wait_for_testid_hidden(
        "sharepoint-sites-dialog", timeout=5000
    )
    await force_reset_body(page)
    return hidden


async def add_sharepoint_site(helper, site_url: str) -> bool:
    """Fill the site URL input and click 'Add Site'.

    Assumes the SharePoint Sites dialog is already open.
    Returns True if the add button was clicked (not necessarily success).
    """
    page = helper.page

    fill_ok = await helper.fill_by_testid("sharepoint-site-url-input", site_url)
    if not fill_ok:
        logger.error("Failed to fill sharepoint-site-url-input")
        return False

    try:
        await js_click_testid(page, "add-sharepoint-site-button")
    except Exception as e:
        logger.error(f"Failed to JS-click add-sharepoint-site-button: {e}")
        return False

    await page.wait_for_timeout(3000)
    return True


async def is_site_in_table(helper, site_identifier: str) -> bool:
    """Check if a row containing *site_identifier* exists in the sites table
    inside the SharePoint Sites dialog.
    """
    dialog = helper.page.locator('[data-testid="sharepoint-sites-dialog"]')
    row = dialog.locator(f'tr:has-text("{site_identifier}")')
    return await row.count() > 0


async def disconnect_site_by_row_text(helper, site_identifier: str) -> bool:
    """Find a site row by text and click its Disconnect button.

    The disconnect button has a dynamic testid ``disconnect-sp-site-{siteId}``
    so we locate via the row text and then find the Disconnect button inside.
    """
    page = helper.page
    dialog = page.locator('[data-testid="sharepoint-sites-dialog"]')
    row = dialog.locator(f'tr:has-text("{site_identifier}")')

    if await row.count() == 0:
        logger.warning(f"Site row '{site_identifier}' not found for disconnect")
        return False

    disconnect_btn = row.first.locator('button:has-text("Disconnect")')
    if await disconnect_btn.count() == 0:
        logger.warning("Disconnect button not found in row")
        return False

    await disconnect_btn.evaluate("el => el.click()")
    await page.wait_for_timeout(2000)
    logger.info(f"JS-clicked Disconnect for site '{site_identifier}'")
    return True


async def count_sites_in_dialog(helper) -> int:
    """Count the number of site rows in the SharePoint Sites dialog."""
    dialog = helper.page.locator('[data-testid="sharepoint-sites-dialog"]')
    rows = dialog.locator("tbody tr")
    return await rows.count()


async def check_for_sync_updates(helper) -> bool:
    """Click 'Check for updates' and wait for the sync preview table.

    Assumes the SharePoint Sites dialog is open.
    Returns True if the button was clicked successfully.
    """
    page = helper.page

    click_ok = await helper.click_by_testid("check-sharepoint-sync-button")
    if not click_ok:
        logger.error("Failed to click check-sharepoint-sync-button")
        return False

    await page.wait_for_timeout(SYNC_CHECK_TIMEOUT_MS // 3)
    return True


# ---------------------------------------------------------------------------
# Upload dialog & file operations
# ---------------------------------------------------------------------------


async def open_upload_dialog(helper) -> bool:
    """Navigate to Data Ingestion tab and open the Upload Data dialog.

    Returns True if the dialog was opened successfully.
    """
    page = helper.page
    await dismiss_any_overlay(helper)
    await force_reset_body(page)

    if not await helper.navigate_to_admin_tab("data-ingestion"):
        logger.error("Failed to navigate to data-ingestion tab")
        return False

    try:
        await js_click_testid(page, "upload-data-trigger-button")
    except Exception:
        logger.error("Failed to click upload-data-trigger-button")
        return False

    dialog_visible = await helper.is_visible_by_testid(
        "upload-data-dialog", timeout=5000
    )
    if not dialog_visible:
        logger.error("upload-data-dialog did not appear")
        return False

    await page.wait_for_timeout(500)
    return True


async def select_sharepoint_destination(helper) -> bool:
    """In the Upload Data dialog, select a SharePoint site as the destination.

    SharePoint destinations are prefixed with the globe emoji.
    Returns True if a SharePoint destination was selected, False if none found.
    """
    page = helper.page
    dropdown = page.locator('[data-testid="destination-dropdown"]')
    try:
        await dropdown.wait_for(state="visible", timeout=10000)
    except Exception:
        logger.warning("destination-dropdown not visible")
        return False

    select_button = dropdown.locator("button").first
    await select_button.evaluate("el => el.click()")
    await page.wait_for_timeout(1000)

    options = page.locator('[role="option"]')
    count = await options.count()
    for i in range(count):
        text = await options.nth(i).text_content() or ""
        if SP_GLOBE_EMOJI in text:
            await options.nth(i).evaluate("el => el.click()")
            await page.wait_for_timeout(500)
            logger.info(f"Selected SharePoint destination: {text}")
            return True

    logger.warning("No SharePoint destination found in dropdown")
    await page.keyboard.press("Escape")
    return False


async def authenticate_to_seaweedfs(helper):
    """Visit the SeaweedFS subdomain to establish an authenticated session.

    Identical to the pattern in test_data_ingestion_e2e.py.
    """
    page = helper.page
    context = page.context
    fqdn = cfg.get("FQDN", "erag.com")
    seaweedfs_url = f"https://seaweedfs.{fqdn}/"

    logger.info(f"Authenticating browser session to SeaweedFS at {seaweedfs_url}")
    auth_page = await context.new_page()
    try:
        await auth_page.goto(seaweedfs_url, wait_until="commit", timeout=30000)
        await auth_page.wait_for_timeout(3000)
        logger.info(f"SeaweedFS auth complete -- URL: {auth_page.url}")
    except Exception as exc:
        logger.warning(f"SeaweedFS auth navigation warning (non-fatal): {exc}")
        await auth_page.wait_for_timeout(2000)
    finally:
        await auth_page.close()


async def delete_row_via_table(helper, identifier: str):
    """Find a row containing *identifier* and click its delete button."""
    page = helper.page
    row = page.locator(f'tr:has-text("{identifier}")')
    if await row.count() > 0:
        delete_btn = row.first.locator('[data-testid="delete-file-button"]')
        await delete_btn.click()
        await page.wait_for_timeout(1000)
        logger.info(f"Deleted row '{identifier}'")


async def get_file_rows_with_source(helper, source_emoji: str) -> int:
    """Count file rows in the Data Ingestion table matching a source emoji."""
    page = helper.page
    rows = page.locator("tbody tr")
    count = 0
    total = await rows.count()
    for i in range(total):
        text = await rows.nth(i).text_content() or ""
        if source_emoji in text:
            count += 1
    return count
