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
- DRY: Common functionality in BaseUIHelper, inherited by specific helpers
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
        # Ensure URL has a protocol prefix (required by Playwright)
        if url and not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
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


# ==================== Base UI Helper (DRY - Shared Methods) ====================

class BaseUIHelper:
    """Base class with common UI interaction methods.
    
    Provides shared functionality for element checking, form interactions,
    and button operations. Specific helpers (Chat, DocSum) inherit from this.
    
    DRY Principle: Common methods defined once, reused by all UI helpers.
    """
    
    def __init__(self, page: Page, base_url: str):
        """Initialize base helper.
        
        Args:
            page: Playwright page instance
            base_url: Base URL for the application
        """
        self.page = page
        # Ensure base_url has https:// prefix for URL operations
        if base_url and not base_url.startswith(('http://', 'https://')):
            self.base_url = f"https://{base_url}"
        else:
            self.base_url = base_url
        self.ui_helper = UIHelper(page, base_url=base_url)
    
    async def check_element_rendered(
        self,
        selector: str = None,
        aria_label: str = None,
        css_class: str = None,
        element_id: str = None,
        data_testid: str = None,
        check_children: bool = False,
        timeout: int = 10000
    ) -> bool:
        """Check if element is rendered using various selector strategies.
        
        Unified method supporting all common selector types.
        
        Args:
            selector: Direct CSS selector (e.g., '.my-class', '#my-id')
            aria_label: The aria-label attribute value
            css_class: CSS class name (without dot prefix)
            element_id: The id attribute value (without # prefix)
            data_testid: The data-testid attribute value
            check_children: Whether to verify element has child elements
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if element is rendered (and has children if checked), False otherwise
        """
        try:
            # Determine which selector to use (priority order)
            if data_testid:
                locator_str = f'[data-testid="{data_testid}"]'
                selector_desc = f"data-testid='{data_testid}'"
            elif element_id:
                locator_str = f'#{element_id}'
                selector_desc = f"id='{element_id}'"
            elif selector:
                locator_str = selector
                selector_desc = f"selector '{selector}'"
            elif aria_label:
                locator_str = f'[aria-label="{aria_label}"]'
                selector_desc = f"aria-label='{aria_label}'"
            elif css_class:
                locator_str = f'.{css_class}'
                selector_desc = f"class '{css_class}'"
            else:
                logger.error("No selector provided")
                return False
            
            logger.info(f"Checking if element with {selector_desc} is rendered...")
            
            element = self.page.locator(locator_str)
            await element.wait_for(state="visible", timeout=timeout)
            
            element_count = await element.count()
            if element_count == 0:
                logger.error(f"Element with {selector_desc} not found")
                return False
            
            logger.info(f"Element with {selector_desc} is rendered")
            
            # Check for children if required
            if check_children:
                children = element.locator('> *')
                children_count = await children.count()
                
                if children_count == 0:
                    logger.error("Element has no children")
                    return False
                
                logger.info(f"Element has {children_count} child elements")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check element: {e}")
            return False
    
    async def is_element_editable(self, element_id: str, timeout: int = 5000) -> bool:
        """Check if a textarea/input element is editable.
        
        Args:
            element_id: The id attribute of the element
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if element is editable, False otherwise
        """
        try:
            element = self.page.locator(f'#{element_id}')
            await element.wait_for(state="visible", timeout=timeout)
            
            is_editable = await element.is_editable()
            logger.info(f"Element #{element_id} editable: {is_editable}")
            return is_editable
            
        except Exception as e:
            logger.error(f"Failed to check if element is editable: {e}")
            return False
    
    async def fill_textarea(self, element_id: str, text: str, timeout: int = 5000) -> bool:
        """Fill a textarea element with text.
        
        Args:
            element_id: The id attribute of the textarea
            text: Text to fill into the textarea
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if fill successful, False otherwise
        """
        try:
            element = self.page.locator(f'#{element_id}')
            await element.wait_for(state="visible", timeout=timeout)
            
            await element.fill(text)
            logger.info(f"Filled textarea #{element_id} with {len(text)} characters")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill textarea: {e}")
            return False
    
    async def get_textarea_value(self, element_id: str, timeout: int = 5000) -> Optional[str]:
        """Get the current value of a textarea element.
        
        Args:
            element_id: The id attribute of the textarea
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            Current value of textarea, or None if failed
        """
        try:
            element = self.page.locator(f'#{element_id}')
            await element.wait_for(state="visible", timeout=timeout)
            
            value = await element.input_value()
            return value
            
        except Exception as e:
            logger.error(f"Failed to get textarea value: {e}")
            return None
    
    async def is_button_enabled(self, aria_label: str, timeout: int = 5000) -> bool:
        """Check if a button with specific aria-label is enabled.
        
        Args:
            aria_label: The aria-label attribute of the button
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if button is enabled, False otherwise
        """
        try:
            button = self.page.locator(f'button[aria-label="{aria_label}"]')
            await button.wait_for(state="visible", timeout=timeout)
            
            is_enabled = await button.is_enabled()
            logger.info(f"Button '{aria_label}' enabled: {is_enabled}")
            return is_enabled
            
        except Exception as e:
            logger.error(f"Failed to check button state: {e}")
            return False
    
    async def click_button(self, aria_label: str, timeout: int = 5000) -> bool:
        """Click a button with specific aria-label.
        
        Args:
            aria_label: The aria-label attribute of the button
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if click successful, False otherwise
        """
        try:
            button = self.page.locator(f'button[aria-label="{aria_label}"]')
            await button.wait_for(state="visible", timeout=timeout)
            
            if not await button.is_enabled():
                logger.error(f"Button '{aria_label}' is disabled, cannot click")
                return False
            
            await button.click()
            logger.info(f"Clicked button '{aria_label}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click button: {e}")
            return False


# ==================== Chat UI Helper ====================

class ChatUIHelper(BaseUIHelper):
    """Helper class for chat UI interactions.
    
    Inherits common methods from BaseUIHelper.
    Provides Chat-specific methods for sending messages, waiting for responses,
    and navigating between Chat and Control Plane.
    
    Single Responsibility: Manages chat interface interactions only.
    """
    
    def __init__(self, page: Page, base_url: str):
        """Initialize chat helper.
        
        Args:
            page: Playwright page instance
            base_url: Base URL for the application
        """
        super().__init__(page, base_url)
    
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

            # Find and fill textarea using data-testid
            textarea = self.page.locator('[data-testid="prompt-input-textarea"]')
            if not await textarea.count():
                logger.error("Textarea not found")
                return False, None

            await textarea.fill(message)
            await self.page.wait_for_timeout(500)

            # Find and click send button using data-testid
            send_button = self.page.locator('[data-testid="prompt-send-button"]')
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
            
            # Wait for bot message element to appear using data-testid
            bot_message = self.page.locator('[data-testid="bot-message__text"]').last
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

    async def navigate_to_control_plane(self) -> bool:
        """Navigate to Control Plane by clicking the Admin Panel button.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            logger.info("Navigating to Control Plane...")
            
            # Locate and click the Admin Panel button using data-testid
            admin_button = self.page.locator('[data-testid="view-switch-btn--to-admin-panel"]')
            
            if not await admin_button.count():
                logger.error("Admin Panel button not found")
                return False
            
            await admin_button.click()
            
            # Wait for navigation
            await self.page.wait_for_load_state("networkidle")
            
            logger.info(f"Navigated to: {self.page.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to Control Plane: {e}")
            return False
    
    async def navigate_to_chat(self) -> bool:
        """Navigate back to Chat from Control Plane.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            logger.info("Navigating to Chat...")
            
            # Locate the Chat button using data-testid
            chat_button = self.page.locator('[data-testid="view-switch-btn--to-chat"]')
            
            try:
                # Wait for the button to be visible
                await chat_button.wait_for(state="visible", timeout=10000)
            except Exception:
                logger.error("Chat button not found or not visible")
                # Debug: Print all data-testids on the page
                elements = await self.page.locator('[data-testid]').all()
                logger.info(f"Found {len(elements)} elements with data-testid:")
                for i, element in enumerate(elements):
                    try:
                        testid = await element.get_attribute("data-testid")
                        visible = await element.is_visible()
                        logger.info(f"  {i}: {testid} (visible={visible})")
                    except Exception as e:
                        logger.warning(f"  {i}: Error getting attribute: {e}")
                return False
            
            await chat_button.click()
            
            # Wait for navigation
            await self.page.wait_for_load_state("networkidle")
            
            logger.info(f"Navigated to: {self.page.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to Chat: {e}")
            return False
    
    async def verify_control_plane_url(self, expected_path: str = "/admin-panel/control-plane") -> bool:
        """Verify current URL matches expected Control Plane path.
        
        Args:
            expected_path: Expected path after base URL
            
        Returns:
            True if URL matches, False otherwise
        """
        try:
            current_url = self.page.url
            expected_url = f"{self.ui_helper.base_url}{expected_path}"
            
            if current_url == expected_url:
                logger.info(f"URL verified: {current_url}")
                return True
            else:
                logger.error(f"URL mismatch: expected {expected_url}, got {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify URL: {e}")
            return False


# ==================== DocSum UI Helper ====================

class DocSumUIHelper(BaseUIHelper):
    """Helper class for DocSum UI interactions.
    
    Inherits common methods from BaseUIHelper.
    Provides DocSum-specific methods for navigating to DocSum UI,
    generating summaries, and waiting for summary output.
    """
    
    def __init__(self, page: Page, base_url: str):
        """Initialize DocSum helper.
        
        Args:
            page: Playwright page instance
            base_url: Base URL for the application (FQDN without protocol)
        """
        super().__init__(page, base_url)
    
    async def login_and_navigate_to_docsum(self, username: str, password: str) -> bool:
        """Login and navigate to DocSum UI.
        
        DocSum has a different entry point ({domain}/docsum) than Chat ({domain}/chat).
        This method handles the Keycloak authentication flow and navigates to DocSum.
        
        Args:
            username: Admin username for Keycloak
            password: Admin password for Keycloak
            
        Returns:
            True if login and navigation successful, False otherwise
        """
        try:
            logger.info("Logging in and navigating to DocSum UI...")
            
            # Navigate to DocSum entry point (will redirect to Keycloak if not authenticated)
            docsum_url = f"{self.base_url}/docsum"
            await self.page.goto(docsum_url)
            await self.page.wait_for_load_state("networkidle")
            
            # Check if we're redirected to Keycloak login
            current_url = self.page.url
            
            if "auth" in current_url or "login" in current_url.lower():
                # Need to authenticate
                logger.info("Redirected to Keycloak, performing login...")
                await self.ui_helper.actions.fill_username(username)
                await self.ui_helper.actions.fill_password(password)
                await self.ui_helper.actions.click_login()
                await self.ui_helper.actions.wait_for_navigation()
                
                # Give extra time for OAuth redirects to complete
                await self.page.wait_for_timeout(3000)
            
            # Verify we ended up at DocSum paste-text page
            current_url = self.page.url
            expected_url = f"{self.base_url}/docsum/paste-text"
            
            if expected_url in current_url or "/docsum" in current_url:
                logger.info(f"Successfully navigated to DocSum: {current_url}")
                return True
            else:
                logger.error(f"Unexpected URL after login: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to login and navigate to DocSum: {e}")
            return False
    
    async def wait_for_summary(
        self,
        content_class: str = "generated-summary__content",
        timeout: int = 60000
    ) -> Optional[str]:
        """Wait for summary to be generated and return its content.
        
        The summary appears inside a div with class 'generated-summary__content',
        containing <p> elements with the summary text.
        
        Args:
            content_class: CSS class of the summary content container
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            Summary text or None if timeout/failure
        """
        try:
            logger.info("Waiting for summary generation...")
            
            # Wait for the summary content div to appear
            content_div = self.page.locator(f'.{content_class}')
            await content_div.wait_for(state="visible", timeout=timeout)
            
            # Wait for content to stabilize (streaming may take time)
            previous_length = 0
            stable_count = 0
            max_stable_checks = 3
            
            while stable_count < max_stable_checks:
                await self.page.wait_for_timeout(500)
                
                # Get all paragraph text
                paragraphs = content_div.locator('p')
                p_count = await paragraphs.count()
                
                if p_count > 0:
                    texts = []
                    for i in range(p_count):
                        text = await paragraphs.nth(i).text_content()
                        if text:
                            texts.append(text.strip())
                    current_text = ' '.join(texts)
                    current_length = len(current_text)
                else:
                    # Fallback to all text content
                    current_text = await content_div.text_content()
                    current_length = len(current_text) if current_text else 0
                
                if current_length == previous_length and current_length > 0:
                    stable_count += 1
                else:
                    stable_count = 0
                
                previous_length = current_length
            
            # Get final summary text
            paragraphs = content_div.locator('p')
            p_count = await paragraphs.count()
            
            if p_count > 0:
                texts = []
                for i in range(p_count):
                    text = await paragraphs.nth(i).text_content()
                    if text:
                        texts.append(text.strip())
                summary_text = ' '.join(texts)
            else:
                summary_text = await content_div.text_content()
            
            if summary_text:
                summary_text = summary_text.strip()
                logger.info(f"Summary generated: {len(summary_text)} characters")
                return summary_text
            
            logger.error("No summary text found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return None