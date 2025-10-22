#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
UI Helper for Playwright-based UI automation tests.

This module follows SOLID principles:
- Single Responsibility: Each class/method has one clear purpose
- Open/Closed: Easy to extend without modifying existing code
- Liskov Substitution: Page objects can be substituted
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depends on abstractions (Page interface)
"""

import logging
from typing import Optional, Tuple
from playwright.async_api import Page

logger = logging.getLogger(__name__)


# ==================== Page Object Models (Interface Segregation) ====================

class LoginPageSelectors:
    """Encapsulates all selectors for the login page.
    
    Single Responsibility: Manages selectors only.
    Makes selector changes easy without touching logic.
    """
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#kc-login"


class LoginPageActions:
    """Handles all actions on the login page.
    
    Single Responsibility: Page interactions only.
    Dependency Inversion: Depends on Page abstraction, not concrete implementation.
    """
    
    def __init__(self, page: Page):
        """Initialize with Playwright Page object.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
        self.selectors = LoginPageSelectors()
    
    async def navigate_to(self, url: str) -> None:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
        """
        logger.debug(f"Navigating to: {url}")
        await self.page.goto(url)
    
    async def fill_username(self, username: str) -> None:
        """Fill the username field.
        
        Args:
            username: Username to enter
        """
        logger.debug("Filling username field")
        await self.page.fill(self.selectors.USERNAME_INPUT, username)
    
    async def fill_password(self, password: str) -> None:
        """Fill the password field.
        
        Args:
            password: Password to enter
        """
        logger.debug("Filling password field")
        await self.page.fill(self.selectors.PASSWORD_INPUT, password)
    
    async def click_login(self) -> None:
        """Click the login button."""
        logger.debug("Clicking login button")
        await self.page.click(self.selectors.LOGIN_BUTTON)
    
    async def wait_for_navigation(self, timeout: int = 30000) -> None:
        """Wait for page navigation to complete.
        
        Args:
            timeout: Timeout in milliseconds
        """
        logger.debug("Waiting for navigation to complete")
        await self.page.wait_for_load_state("networkidle", timeout=timeout)


# ==================== Business Logic (Single Responsibility) ====================

class LoginFlowManager:
    """Manages the complete login flow.
    
    Single Responsibility: Orchestrates login steps.
    Open/Closed: Can be extended for new login flows (SSO, MFA, etc.)
    """
    
    def __init__(self, page_actions: LoginPageActions):
        """Initialize with page actions.
        
        Args:
            page_actions: LoginPageActions instance
        """
        self.actions = page_actions
    
    async def perform_login(
        self,
        username: str,
        password: str,
        expected_redirect_url: str
    ) -> str:
        """Perform standard login.
        
        Args:
            username: Username to login with
            password: Password to use
            expected_redirect_url: URL to expect after login
            
        Returns:
            Final URL after login
        """
        logger.info(f"Performing login for user: {username}")
        
        # Fill and submit login form
        await self.actions.fill_username(username)
        await self.actions.fill_password(password)
        await self.actions.click_login()
        
        # Wait for navigation to complete
        await self.actions.wait_for_navigation()
        
        # Give extra time for OAuth redirects to complete (Keycloak does multiple redirects)
        await self.actions.page.wait_for_timeout(5000)  # Increased from 2000ms
        
        return self.actions.page.url


# ==================== Main UI Helper (Facade Pattern) ====================

class UIHelper:
    """Main UI Helper - Facade for all UI operations.
    
    Provides high-level interface for common UI operations.
    Follows SOLID principles throughout the design.
    """
    
    def __init__(self, page: Page, base_url: str):
        """Initialize UI Helper.
        
        Args:
            page: Playwright Page instance
            base_url: Base URL for the application
        """
        self.page = page
        self.base_url = base_url
        
        # Initialize page actions
        self.actions = LoginPageActions(page)
        
        # Initialize flow managers
        self.login_manager = LoginFlowManager(self.actions)
    
    async def navigate_to_login(self) -> None:
        """Navigate to the login page."""
        await self.actions.navigate_to(self.base_url)
    
    async def login_as_admin(self, username: str, password: str) -> str:
        """Login as admin user.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Final URL after login
        """
        await self.navigate_to_login()
        expected_url = f"{self.base_url}/chat"
        return await self.login_manager.perform_login(username, password, expected_url)


# ==================== Chat UI Helper ====================

class ChatUIHelper:
    """Helper class for chat UI interactions.
    
    Provides methods for sending messages, waiting for responses,
    and retrieving chat history from the UI.
    
    Single Responsibility: Manages chat interface interactions only.
    """
    
    def __init__(self, page: Page, base_url: str):
        """Initialize chat helper.
        
        Args:
            page: Playwright page instance
            base_url: Base URL for the application
        """
        self.page = page
        self.ui_helper = UIHelper(page, base_url=base_url)
    
    async def _extract_message_text(self, bot_message) -> Optional[str]:
        """Extract combined text from all descendant text nodes of a bot message.

        Generic implementation: does not rely on specific child tag names.
        Captures any visible text appearing within the bot message container,
        including paragraphs, lists, code blocks, inline fragments, etc.

        Args:
            bot_message: Playwright locator for the bot message root element.
        Returns:
            Space-joined text from all text nodes or None if no text.
        """
        try:
            element_handle = await bot_message.element_handle()
            if not element_handle:
                return None
            texts = await element_handle.evaluate("(el) => { const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false); const arr = []; let node; while ((node = walker.nextNode())) { const t = node.textContent.trim(); if (t) arr.push(t); } return arr; }")
            return ' '.join(texts)
        except Exception as e:
            logger.debug(f"_extract_message_text failed: {e}")
            return None

    async def login_as_admin(self, username: str, password: str) -> str:
        """Login as admin user"""
        await self.ui_helper.login_as_admin(username, password)

    async def send_message(
        self,
        message: str,
        wait_for_response: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Send a chat message.

        Args:
            message: Message text to send
            wait_for_response: Whether to wait for bot response

        Returns:
            Tuple of (success: bool, response: str or None)
        """
        try:
            logger.info(f"Sending message: {message[:50]}...")

            # Find and fill textarea
            textarea = self.page.locator('.prompt-input')
            if not await textarea.count():
                logger.error("Textarea not found")
                return False, None

            await textarea.fill(message)
            await self.page.wait_for_timeout(500)

            # Find and click send button
            send_button = self.page.locator('button[type="submit"]')
            if not await send_button.count():
                logger.error("Send button not found")
                return False, None

            if not await send_button.is_enabled():
                logger.error("Send button is disabled")
                return False, None

            await send_button.click()
            logger.info("Message sent")

            # Wait for response if requested
            if wait_for_response:
                response = await self.wait_for_response()
                return True, response
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False, None
    
    async def wait_for_response(self, timeout: int = 60000) -> Optional[str]:
        """Wait for bot response with streaming support.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            Response text or None if timeout
        """
        try:
            logger.info("Waiting for response...")
            
            # Wait for bot message element to appear
            bot_message = self.page.locator('.bot-message__text').last
            await bot_message.wait_for(state="visible", timeout=timeout)
            
            # Wait for streaming to complete by monitoring text length stabilization
            logger.info("Waiting for streaming to complete...")
            previous_length = 0
            stable_count = 0
            max_stable_checks = 3  # Require 3 consecutive stable checks
            
            while stable_count < max_stable_checks:
                await self.page.wait_for_timeout(500)
                
                # Extract current text from all children
                current_text = await self._extract_message_text(bot_message)

                if current_text is None:
                    logger.error("No bot message found within timeout")
                    return None
                
                current_length = len(current_text)
                
                if current_length == previous_length and current_length > 0:
                    stable_count += 1
                else:
                    stable_count = 0
                
                previous_length = current_length
            
            # Final text extraction
            final_text = await self._extract_message_text(bot_message)

            if final_text:
                logger.info(f"Received response ({len(final_text)} chars)")
                return final_text
            
            # Fallback to direct text content
            response_text = await bot_message.text_content()
            if response_text:
                logger.info(f"Received response ({len(response_text)} chars)")
                return response_text.strip()
            
            logger.error("No text content in response")
            return None
                    
        except Exception as e:
            logger.error(f"Failed to get response: {e}")
            return None
