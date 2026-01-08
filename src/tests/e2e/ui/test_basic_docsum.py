#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for DocSum UI basic functionality.

Main Goal: Verify user can fill text and generate a summary.

This module validates the core user interaction flow:
1. User can access the Paste Text tab
2. User can fill text into the textarea
3. User can click Generate Summary and receive a summary

Entry Point: {domain}/docsum redirects to {domain}/docsum/paste-text
Authentication: Reuses existing Keycloak authentication flow
"""

import allure
import logging
import pytest

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Skip all tests if docsum pipeline is not deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "docsum":
        break
else:
    pytestmark = pytest.mark.skip(reason="DocSum pipeline is not deployed")


# Sample text for summary generation
SAMPLE_TEXT = """
Artificial Intelligence (AI) is transforming industries across the globe. 
From healthcare to finance, AI-powered solutions are improving efficiency, 
accuracy, and decision-making processes. Machine learning algorithms can 
analyze vast amounts of data to identify patterns and make predictions 
that would be impossible for humans to detect manually.

In healthcare, AI assists doctors in diagnosing diseases by analyzing 
medical images and patient records. In finance, AI models detect 
fraudulent transactions in real-time. The technology continues to evolve, 
with new applications emerging in autonomous vehicles, natural language 
processing, and robotic automation.
"""


@allure.testcase("IEASG-T300")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_paste_text_tab_rendered(docsum_ui_helper):
    """
    Test that the Paste Text tab is rendered in DocSum UI.
    
    Verifies: User can see the Paste Text tab after login.
    """
    logger.info("Test: Paste Text Tab Rendering")
    
    tab_rendered = await docsum_ui_helper.check_element_rendered(
        aria_label="Paste Text Tab",
        timeout=10000
    )
    
    assert tab_rendered, "Paste Text tab (aria-label='Paste Text Tab') not found"
    logger.info("Paste Text tab is rendered")


@allure.testcase("IEASG-T301")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_user_can_fill_textarea(docsum_ui_helper):
    """
    Test that user can fill text into the textarea.
    
    Verifies: Textarea exists, is editable, and accepts text input.
    """
    logger.info("Test: User Can Fill Textarea")
    
    # Check textarea exists
    textarea_rendered = await docsum_ui_helper.check_element_rendered(
        element_id="paste-text",
        timeout=10000
    )
    assert textarea_rendered, "Textarea (id='paste-text') not found"
    
    # Check textarea is editable
    is_editable = await docsum_ui_helper.is_element_editable("paste-text")
    assert is_editable, "Textarea should be editable"
    
    # Fill text and verify
    test_text = "Test input for DocSum."
    fill_success = await docsum_ui_helper.fill_textarea("paste-text", test_text)
    assert fill_success, "Failed to fill textarea"
    
    current_value = await docsum_ui_helper.get_textarea_value("paste-text")
    assert current_value == test_text, f"Text mismatch: got '{current_value}'"
    
    logger.info("User can fill textarea successfully")


@allure.testcase("IEASG-T302")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_user_can_generate_summary(docsum_ui_helper):
    """
    CORE TEST: User fills text and generates a summary.
    
    This is the main user flow:
    1. Fill textarea with text
    2. Click Generate Summary button
    3. Verify summary is generated
    """
    logger.info("Test: User Can Generate Summary (Core Flow)")
    
    # Step 1: Fill textarea with sample text
    fill_success = await docsum_ui_helper.fill_textarea("paste-text", SAMPLE_TEXT)
    assert fill_success, "Failed to fill textarea"
    logger.info("Step 1: Filled textarea with text")
    
    await docsum_ui_helper.page.wait_for_timeout(500)
    
    # Step 2: Verify Generate Summary button is enabled and click it
    button_enabled = await docsum_ui_helper.is_button_enabled("Generate Summary")
    assert button_enabled, "Generate Summary button should be enabled"
    
    click_success = await docsum_ui_helper.click_button("Generate Summary")
    assert click_success, "Failed to click Generate Summary button"
    logger.info("Step 2: Clicked Generate Summary button")
    
    # Step 3: Wait for and verify summary generation
    summary_text = await docsum_ui_helper.wait_for_summary(
        content_class="generated-summary__content",
        timeout=60000
    )
    
    assert summary_text is not None, "No summary was generated"
    assert len(summary_text.strip()) > 0, "Summary is empty"
    
    logger.info(f"Step 3: Summary generated ({len(summary_text)} chars)")
    logger.info(f"Summary preview: {summary_text[:100]}...")
    
    logger.info("SUCCESS: User can fill text and generate summary")
