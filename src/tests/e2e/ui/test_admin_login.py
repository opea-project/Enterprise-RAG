#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)


@allure.testcase("IEASG-T266")
@pytest.mark.ui
@pytest.mark.asyncio
async def test_admin_login(page, admin_credentials):
    """Test admin login with KeycloakHelper credentials.
    
    Success criteria: User is redirected to ERAG_DOMAIN/chat after login.
    """
    USERNAME = admin_credentials['username']
    PASSWORD = admin_credentials['password']
    erag_domain = f"https://{cfg.get('FQDN')}"
    
    logger.info(f"Testing admin login with username: {USERNAME}")
    
    # Navigate to login page
    await page.goto(erag_domain)
    
    # Fill credentials
    await page.fill("#username", USERNAME)
    await page.fill("#password", PASSWORD)
    
    # Click login button
    await page.click("#kc-login")
    
    # Wait for navigation after login
    await page.wait_for_load_state("networkidle")
    
    # Verify success: should redirect to /chat
    current_url = page.url
    expected_url = f"{erag_domain}/chat"
    
    assert current_url == expected_url, \
        f"Login failed: expected redirect to {expected_url}, but got {current_url}"
    
    logger.info(f"Admin login successful: redirected to {current_url}")