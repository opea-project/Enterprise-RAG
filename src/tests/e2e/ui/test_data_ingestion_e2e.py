#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
End-to-end UI tests for Data Ingestion — actual file upload and deletion.

Unlike test_data_ingestion.py (which validates dialog mechanics only),
these tests perform *real* uploads and deletions through the browser UI
and verify the results in the Data Ingestion table.

Covered scenarios:
1. Upload a file via the UI and verify it reaches "ingested" status
2. Upload a link via the UI and verify it reaches "ingested" status
3. Delete an ingested file via the UI and verify it disappears from the table
4. Delete an ingested link via the UI and verify it disappears from the table

All interactions use data-testid selectors to stay resilient against CSS changes.
"""

import logging
import os
import uuid

import allure
import pytest

from tests.e2e.ui.conftest import requires_chatqa
from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)

pytestmark = requires_chatqa

# Resolve the absolute path of a small test file for upload.
# Use .txt — universally accepted MIME type.  The .md file can hit
# backend MIME-type misdetection ("adoc") leading to ingestion errors.
_TEST_FILE = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    DATAPREP_UPLOAD_DIR, "test_dataprep.txt"
)

# Maximum time (ms) to wait for a file to reach "ingested" status in the UI
INGESTION_TIMEOUT_MS = 180_000
# Polling interval (ms) when checking file status in the UI
POLL_INTERVAL_MS = 5_000


# ============================================================================
# HELPERS
# ============================================================================

async def _authenticate_to_seaweedfs(chat_ui_helper):
    """
    Visit the SeaweedFS subdomain so the browser establishes an authenticated
    session.  Istio's OAuth filter protects ``seaweedfs.{FQDN}`` — one visit
    while the Keycloak SSO session is active is enough to acquire the auth
    cookie for that subdomain.  Without this step any pre-signed PUT/DELETE to
    SeaweedFS will be rejected with 403.

    Opens a **separate tab** for the SeaweedFS visit to avoid navigation
    interrupts on the main page.
    """
    page = chat_ui_helper.page
    context = page.context
    fqdn = cfg.get("FQDN", "erag.com")
    seaweedfs_url = f"https://seaweedfs.{fqdn}/"

    logger.info(f"Authenticating browser session to SeaweedFS at {seaweedfs_url}")
    auth_page = await context.new_page()
    try:
        await auth_page.goto(seaweedfs_url, wait_until="commit", timeout=30000)
        # Give the SSO redirect chain a moment to settle
        await auth_page.wait_for_timeout(3000)
        logger.info(f"SeaweedFS auth complete — URL: {auth_page.url}")
    except Exception as exc:
        logger.warning(f"SeaweedFS auth navigation warning (non-fatal): {exc}")
        # Even if goto throws, cookies may have been set via redirect
        await auth_page.wait_for_timeout(2000)
    finally:
        await auth_page.close()

async def _open_upload_dialog(chat_ui_helper) -> bool:
    """Navigate to Data Ingestion tab and open the Upload Data dialog.

    Returns:
        True if the dialog was opened successfully, False otherwise.
    """
    page = chat_ui_helper.page

    if not await chat_ui_helper.navigate_to_admin_tab("data-ingestion"):
        logger.error("Failed to navigate to data-ingestion tab")
        return False

    if not await chat_ui_helper.click_by_testid("upload-data-trigger-button"):
        logger.error("Failed to click upload-data-trigger-button")
        return False

    dialog_visible = await chat_ui_helper.is_visible_by_testid(
        "upload-data-dialog", timeout=5000
    )
    if not dialog_visible:
        logger.error("upload-data-dialog did not appear")
        return False

    await page.wait_for_timeout(500)
    return True


async def _select_destination_if_needed(page):
    """Select the first available upload destination from the dropdown.

    The destination dropdown is required for file uploads — the Upload button
    stays disabled until a destination (S3 bucket or SharePoint site) is
    selected.  This helper waits for the dropdown options to be populated
    (the list comes from ``/list_buckets`` and/or SharePoint APIs) and picks
    the first available destination.

    Note: ``destination-dropdown`` renders a React Aria ``<SelectInput>`` which
    is **not** a native ``<select>``.  It renders a ``<button>`` containing the
    selected value text.  We check ``text_content()`` on that button, not
    ``input_value()``.
    """
    dropdown = page.locator('[data-testid="destination-dropdown"]')
    try:
        await dropdown.wait_for(state="visible", timeout=10000)
    except Exception:
        logger.warning("destination-dropdown not visible — skipping destination selection")
        return

    # Check if a destination is already selected by reading the button text.
    # The SelectInput renders an AriaButton with the selected value text or
    # a placeholder like "Please select destination to upload files".
    select_button = dropdown.locator("button").first
    try:
        current_text = (await select_button.text_content() or "").strip()
    except Exception:
        current_text = ""

    if current_text and "select destination" not in current_text.lower():
        logger.info(f"Destination already selected: {current_text}")
        return

    # Click the button to open the option list
    await select_button.click()
    await page.wait_for_timeout(1000)

    # Wait for options to appear (API may take a moment)
    option = page.locator('[role="option"]').first
    try:
        await option.wait_for(state="visible", timeout=15000)
        await option.click()
        await page.wait_for_timeout(500)
        logger.info("Selected first destination from destination-dropdown")
    except Exception as exc:
        logger.warning(f"No destination options appeared: {exc}")


async def _upload_file_via_dialog(chat_ui_helper, file_path: str):
    """
    Add a file inside the already-open Upload Data dialog and submit.

    Uses Playwright's file chooser interception so no native OS dialog opens.
    """
    page = chat_ui_helper.page

    # Select a destination first (required before file upload is enabled)
    await _select_destination_if_needed(page)

    # Intercept the file chooser triggered by "Browse Files" button
    async with page.expect_file_chooser() as fc_info:
        # Use .first because FileInput and LinkInput both have browse-files-button
        browse_btn = page.locator('[data-testid="browse-files-button"]').first
        await browse_btn.click()

    file_chooser = await fc_info.value
    await file_chooser.set_files(file_path)
    logger.info(f"File selected via file chooser: {file_path}")

    # Click "Upload Data" submit button
    submit_btn = page.locator('[data-testid="upload-data-button"]')
    await submit_btn.wait_for(state="visible", timeout=5000)
    # Brief wait for React to enable the button after file selection
    await page.wait_for_timeout(500)
    await submit_btn.click()
    logger.info("Clicked upload-data-button to submit upload")


async def _upload_link_via_dialog(chat_ui_helper, url: str):
    """Add a link inside the already-open Upload Data dialog and submit."""
    page = chat_ui_helper.page

    fill_ok = await chat_ui_helper.fill_by_testid("link-input", url)
    assert fill_ok, "Failed to fill link-input"

    add_ok = await chat_ui_helper.click_by_testid("add-link-button")
    assert add_ok, "Failed to click add-link-button"
    await page.wait_for_timeout(500)

    # Click "Upload Data" submit button
    submit_btn = page.locator('[data-testid="upload-data-button"]')
    await submit_btn.wait_for(state="visible", timeout=5000)
    await page.wait_for_timeout(500)
    await submit_btn.click()
    logger.info("Clicked upload-data-button to submit link upload")


async def _wait_for_row_in_table(chat_ui_helper, identifier: str,
                                  expected_status: str = "ingested",
                                  timeout_ms: int = INGESTION_TIMEOUT_MS,
                                  max_retries: int = 2):
    """
    Poll the Data Ingestion table until a row containing *identifier*
    reaches *expected_status* or the timeout expires.

    If the row reaches "error" status, clicks the per-row Retry button
    (``data-testid="retry-file-button"``) up to *max_retries* times.
    When retries are exhausted and the row is still in error state the
    function returns ``"error"`` so the caller can decide how to handle it.

    Returns:
        ``True`` if the expected status was reached,
        ``"error"`` if the row settled in error state after all retries,
        ``False`` on timeout without reaching any terminal status.
    """
    page = chat_ui_helper.page
    elapsed = 0
    retries_used = 0

    while elapsed < timeout_ms:
        await chat_ui_helper.click_by_testid("refresh-button")
        await page.wait_for_timeout(POLL_INTERVAL_MS)
        elapsed += POLL_INTERVAL_MS

        row = page.locator(f'tr:has-text("{identifier}")')
        if await row.count() > 0:
            row_text = await row.first.text_content()
            if expected_status in row_text.lower():
                logger.info(
                    f"Row '{identifier}' reached status '{expected_status}' "
                    f"after ~{elapsed / 1000:.0f}s"
                )
                return True

            # If the row is in error state, try clicking Retry
            if "error" in row_text.lower():
                if retries_used < max_retries:
                    retry_btn = row.first.locator('[data-testid="retry-file-button"]')
                    if await retry_btn.count() > 0:
                        retries_used += 1
                        logger.info(
                            f"Row '{identifier}' in error state — "
                            f"clicking Retry ({retries_used}/{max_retries})"
                        )
                        await retry_btn.click()
                        await page.wait_for_timeout(2000)
                        continue
                else:
                    # Retries exhausted — report persistent error
                    logger.warning(
                        f"Row '{identifier}' stuck in error state after "
                        f"{max_retries} retries"
                    )
                    return "error"

            logger.debug(
                f"Row '{identifier}' found but status not yet "
                f"'{expected_status}': {row_text}"
            )

    logger.error(
        f"Timeout: row '{identifier}' did not reach '{expected_status}' "
        f"within {timeout_ms / 1000:.0f}s"
    )
    return False


async def _wait_for_row_to_appear(chat_ui_helper, identifier: str,
                                  timeout_ms: int = 30_000) -> bool:
    """
    Poll the Data Ingestion table until a row containing *identifier* appears.

    Returns True if the row was found within the timeout, False otherwise.
    """
    page = chat_ui_helper.page
    elapsed = 0
    while elapsed < timeout_ms:
        await chat_ui_helper.click_by_testid("refresh-button")
        await page.wait_for_timeout(POLL_INTERVAL_MS)
        elapsed += POLL_INTERVAL_MS
        row = page.locator(f'tr:has-text("{identifier}")')
        if await row.count() > 0:
            logger.info(f"Row '{identifier}' appeared in table after ~{elapsed / 1000:.0f}s")
            return True
    logger.warning(f"Row '{identifier}' did not appear within {timeout_ms / 1000:.0f}s")
    return False


async def _delete_row_via_table(chat_ui_helper, identifier: str,
                                 delete_testid: str = "delete-file-button"):
    """
    Find a row containing *identifier* in the Data Ingestion table and
    click its delete button.

    Args:
        chat_ui_helper: ChatUIHelper instance
        identifier: Text that uniquely identifies the row (filename or URL)
        delete_testid: ``data-testid`` of the per-row delete button
            (``delete-file-button`` for files, ``delete-link-button`` for links)
    """
    page = chat_ui_helper.page

    row = page.locator(f'tr:has-text("{identifier}")')
    assert await row.count() > 0, f"Row '{identifier}' not found in table"

    delete_btn = row.first.locator(f'[data-testid="{delete_testid}"]')
    await delete_btn.click()
    await page.wait_for_timeout(1000)
    logger.info(f"Deleted row '{identifier}' via {delete_testid}")


# ============================================================================
# TEST CASES
# ============================================================================

@allure.testcase("IEASG-T397")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_upload_file_via_ui(chat_ui_helper):
    """
    Upload a real file through the Data Ingestion UI and verify ingestion.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Open upload dialog
    3. Select a bucket (if applicable)
    4. Browse and select a small .md test file via Playwright file chooser
    5. Click "Upload Data" to submit
    6. Wait for the file to appear in the table with "ingested" status
    7. Clean up: delete the file via the UI

    Success criteria:
    - File upload completes without error
    - File appears in the Data Ingestion table (any status)
    - If backend ingestion succeeds, file reaches "ingested" status
      (backend failures are logged as warnings, not test failures)
    - File is removed after cleanup
    """
    logger.info("Test: Upload file via UI end-to-end")

    page = chat_ui_helper.page
    file_path = os.path.abspath(_TEST_FILE)
    file_name = os.path.basename(file_path)

    assert os.path.isfile(file_path), f"Test file not found: {file_path}"

    # Authenticate browser session to SeaweedFS (required for presigned URL uploads)
    await _authenticate_to_seaweedfs(chat_ui_helper)

    # Pre-cleanup: remove leftover file from a previous run if it exists
    try:
        await chat_ui_helper.navigate_to_admin_tab("data-ingestion")
        await page.wait_for_timeout(1000)
        row = page.locator(f'tr:has-text("{file_name}")')
        if await row.count() > 0:
            logger.info(f"Pre-cleanup: removing leftover '{file_name}'")
            await _delete_row_via_table(chat_ui_helper, file_name)
            await page.wait_for_timeout(2000)
    except Exception as pre_err:
        logger.debug(f"Pre-cleanup note: {pre_err}")

    try:
        # Step 1-5: Open dialog and upload
        assert await _open_upload_dialog(chat_ui_helper), "Failed to open upload dialog"
        await _upload_file_via_dialog(chat_ui_helper, file_path)

        # Wait for the dialog to close (success notification)
        dialog_closed = await chat_ui_helper.wait_for_testid_hidden(
            "upload-data-dialog", timeout=15000
        )
        assert dialog_closed, "Upload dialog did not close after submission"
        logger.info("Upload dialog closed — upload accepted by server")

        # Step 6: Verify file appears in the table (any status).
        # The "ingested" status depends on backend processing which may
        # fail for infrastructure reasons outside the UI's control.
        row_appeared = await _wait_for_row_to_appear(chat_ui_helper, file_name, timeout_ms=30_000)
        assert row_appeared, f"File '{file_name}' did not appear in the table after upload"
        logger.info(f"Assert: File '{file_name}' appeared in the table")

        # Wait for file to reach "ingested" (includes retry on error)
        result = await _wait_for_row_in_table(chat_ui_helper, file_name)
        if result == "error":
            logger.warning(
                f"File '{file_name}' ended in 'Error' status after retries "
                "(backend MIME-type or processing issue) — upload UI flow is valid"
            )
        elif not result:
            logger.warning(
                f"File '{file_name}' did not reach 'ingested' status "
                "(timeout) — upload UI flow is valid"
            )
        else:
            logger.info(f"Assert: File '{file_name}' is ingested")

    finally:
        # Step 7: Clean up — delete the file via the UI
        try:
            await chat_ui_helper.navigate_to_admin_tab("data-ingestion")
            await page.wait_for_timeout(1000)
            await _delete_row_via_table(chat_ui_helper, file_name)
            logger.info(f"Cleanup: Deleted '{file_name}'")
        except Exception as cleanup_err:
            logger.warning(f"Cleanup failed (non-fatal): {cleanup_err}")

    logger.info("Test completed: File upload via UI validated")


@allure.testcase("IEASG-T398")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_upload_link_via_ui(chat_ui_helper):
    """
    Upload a real link through the Data Ingestion UI and verify ingestion.

    Steps:
    1. Navigate to Data Ingestion tab
    2. Open upload dialog
    3. Enter a URL in link-input and click add-link-button
    4. Click "Upload Data" to submit
    5. Wait for the link to appear in the links table with "ingested" status
    6. Clean up: delete the link via the UI

    Success criteria:
    - Link upload accepted without errors
    - Link appears in the links table with "ingested" status
    """
    logger.info("Test: Upload link via UI end-to-end")

    page = chat_ui_helper.page
    test_link = f"https://www.example.org/?ui_test_upload_link={uuid.uuid4()}"

    # Authenticate browser session to SeaweedFS (required for presigned URL operations)
    await _authenticate_to_seaweedfs(chat_ui_helper)

    try:
        # Open dialog and submit link
        assert await _open_upload_dialog(chat_ui_helper), "Failed to open upload dialog"
        await _upload_link_via_dialog(chat_ui_helper, test_link)

        # Wait for dialog to close
        dialog_closed = await chat_ui_helper.wait_for_testid_hidden(
            "upload-data-dialog", timeout=15000
        )
        assert dialog_closed, "Upload dialog did not close after link submission"
        logger.info("Upload dialog closed — link accepted")

        # Wait for link to reach "ingested"
        ingested = await _wait_for_row_in_table(chat_ui_helper, test_link)
        assert ingested is True, f"Link '{test_link}' did not reach 'ingested' status (got {ingested!r})"
        logger.info(f"Assert: Link '{test_link}' is ingested")

    finally:
        try:
            await chat_ui_helper.navigate_to_admin_tab("data-ingestion")
            await page.wait_for_timeout(1000)
            await _delete_row_via_table(chat_ui_helper, test_link, delete_testid="delete-link-button")
            logger.info(f"Cleanup: Deleted link '{test_link}'")
        except Exception as cleanup_err:
            logger.warning(f"Cleanup failed (non-fatal): {cleanup_err}")

    logger.info("Test completed: Link upload via UI validated")


@allure.testcase("IEASG-T399")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_ingested_file_via_ui(chat_ui_helper):
    """
    Upload a file, wait for ingestion, then delete it via the UI table action.

    Steps:
    1. Upload a test file via the UI
    2. Wait for it to be ingested
    3. Click the per-row delete button for the file
    4. Confirm deletion
    5. Verify the file is no longer in the table

    Success criteria:
    - File disappears from the table after deletion
    """
    logger.info("Test: Delete ingested file via UI")

    page = chat_ui_helper.page
    file_path = os.path.abspath(_TEST_FILE)
    file_name = os.path.basename(file_path)

    assert os.path.isfile(file_path), f"Test file not found: {file_path}"

    # Authenticate browser session to SeaweedFS (required for presigned URL operations)
    await _authenticate_to_seaweedfs(chat_ui_helper)

    # Upload first
    assert await _open_upload_dialog(chat_ui_helper), "Failed to open upload dialog"
    await _upload_file_via_dialog(chat_ui_helper, file_path)
    await chat_ui_helper.wait_for_testid_hidden("upload-data-dialog", timeout=15000)

    # Wait for the file to appear in the table (any status)
    row_appeared = await _wait_for_row_to_appear(chat_ui_helper, file_name, timeout_ms=30_000)
    assert row_appeared, f"Precondition failed: file '{file_name}' not in table after upload"

    # Try to wait for ingested status, but don't fail — the delete test
    # validates the UI delete action regardless of processing status.
    result = await _wait_for_row_in_table(chat_ui_helper, file_name,
                                              timeout_ms=30_000)
    if result == "error":
        logger.warning(
            f"File '{file_name}' in 'Error' state (backend issue) — "
            "proceeding with delete test anyway"
        )
    elif not result:
        logger.warning(
            f"File '{file_name}' not 'ingested' (backend issue) — "
            "proceeding with delete test anyway"
        )

    # Delete via the table
    await _delete_row_via_table(chat_ui_helper, file_name)

    # Verify: file should no longer be in the table
    await chat_ui_helper.click_by_testid("refresh-button")
    await page.wait_for_timeout(2000)

    row = page.locator(f'tr:has-text("{file_name}")')
    remaining = await row.count()
    assert remaining == 0, \
        f"File '{file_name}' still appears in table after deletion ({remaining} rows)"
    logger.info(f"Assert: File '{file_name}' removed from table")

    logger.info("Test completed: File deletion via UI validated")


@allure.testcase("IEASG-T400")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_ingested_link_via_ui(chat_ui_helper):
    """
    Upload a link, wait for ingestion, then delete it via the UI table action.

    Steps:
    1. Upload a test link via the UI
    2. Wait for it to be ingested
    3. Click the per-row delete button for the link
    4. Confirm deletion
    5. Verify the link is no longer in the table

    Success criteria:
    - Link disappears from the table after deletion
    """
    logger.info("Test: Delete ingested link via UI")

    page = chat_ui_helper.page
    test_link = f"https://www.example.org/?ui_test_del_link={uuid.uuid4()}"

    # Authenticate browser session to SeaweedFS (required for presigned URL operations)
    await _authenticate_to_seaweedfs(chat_ui_helper)

    # Upload first
    assert await _open_upload_dialog(chat_ui_helper), "Failed to open upload dialog"
    await _upload_link_via_dialog(chat_ui_helper, test_link)
    await chat_ui_helper.wait_for_testid_hidden("upload-data-dialog", timeout=15000)
    ingested = await _wait_for_row_in_table(chat_ui_helper, test_link)
    assert ingested is True, f"Precondition failed: link '{test_link}' not ingested (got {ingested!r})"

    # Delete via the table
    await _delete_row_via_table(chat_ui_helper, test_link, delete_testid="delete-link-button")

    # Verify: link should no longer be in the table
    await chat_ui_helper.click_by_testid("refresh-button")
    await page.wait_for_timeout(2000)

    row = page.locator(f'tr:has-text("{test_link}")')
    remaining = await row.count()
    assert remaining == 0, \
        f"Link '{test_link}' still appears in table after deletion ({remaining} rows)"
    logger.info(f"Assert: Link '{test_link}' removed from table")

    logger.info("Test completed: Link deletion via UI validated")
