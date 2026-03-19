#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
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
            
            # Wait for URL to include admin-panel (handles redirect)
            await self.page.wait_for_url("**/admin-panel/**", timeout=10000)
            
            # Wait for control plane panel to be visible
            control_plane_panel = self.page.locator('[data-testid="control-plane-panel"]')
            try:
                await control_plane_panel.wait_for(state="visible", timeout=10000)
            except Exception:
                logger.warning("Control plane panel not immediately visible, continuing...")
            
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
        """Verify current URL contains expected Control Plane path.
        
        Args:
            expected_path: Expected path to be contained in the URL
            
        Returns:
            True if URL contains the expected path, False otherwise
        """
        try:
            current_url = self.page.url
            
            if expected_path in current_url:
                logger.info(f"URL verified: {current_url} contains {expected_path}")
                return True
            else:
                logger.error(f"URL mismatch: expected '{expected_path}' to be in {current_url}")
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
    
    async def select_summary_strategy(
        self,
        strategy: str,
        timeout: int = 5000
    ) -> bool:
        """Select a summarization strategy from the dropdown.
        
        Args:
            strategy: Strategy value - one of 'map_reduce', 'stuff', 'refine'
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if strategy was selected successfully, False otherwise
        """
        try:
            # Map strategy values to display labels
            strategy_labels = {
                "map_reduce": "Map Reduce",
                "stuff": "Stuff",
                "refine": "Refine"
            }
            
            strategy_label = strategy_labels.get(strategy)
            if not strategy_label:
                logger.error(f"Unknown strategy: {strategy}")
                return False
            
            logger.info(f"Selecting summarization strategy: {strategy_label}")
            
            # Click the dropdown trigger button
            dropdown_trigger = self.page.locator('button[aria-label="Change summarization strategy"]')
            await dropdown_trigger.wait_for(state="visible", timeout=timeout)
            await dropdown_trigger.click()
            
            # Wait for menu to appear and click the strategy option by its text
            # React Aria renders menuitemradio when selectionMode="single"
            menu_item = self.page.get_by_role("menuitemradio", name=strategy_label)
            await menu_item.wait_for(state="visible", timeout=timeout)
            await menu_item.click()
            
            logger.info(f"Selected strategy: {strategy_label}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select summary strategy: {e}")
            return False
    
    async def click_generate_summary_button(self, timeout: int = 5000) -> bool:
        """Click the Generate Summary main button.
        
        The button may have text like 'Generate Summary (Map Reduce)' depending
        on the selected strategy.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if click successful, False otherwise
        """
        try:
            # The main button has class 'dropdown-button__main'
            button = self.page.locator('.dropdown-button__main')
            await button.wait_for(state="visible", timeout=timeout)
            
            if not await button.is_enabled():
                logger.error("Generate Summary button is disabled")
                return False
            
            await button.click()
            logger.info("Clicked Generate Summary button")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click Generate Summary button: {e}")
            return False
    
    async def is_generate_summary_button_enabled(self, timeout: int = 5000) -> bool:
        """Check if the Generate Summary main button is enabled.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if button is enabled, False otherwise
        """
        try:
            button = self.page.locator('.dropdown-button__main')
            await button.wait_for(state="visible", timeout=timeout)
            
            is_enabled = await button.is_enabled()
            logger.info(f"Generate Summary button enabled: {is_enabled}")
            return is_enabled
            
        except Exception as e:
            logger.error(f"Failed to check Generate Summary button state: {e}")
            return False


# =============================================================================
# Audio UI Helper - Voice Input and TTS Playback
# =============================================================================

class AudioUIHelper:
    """
    Helper class for audio-related UI interactions.
    
    Handles:
    - Microphone button interactions (start/stop recording)
    - TTS play button interactions
    - Audio state tracking via browser interception
    - Recording animation visibility
    
    Strategy: PulseAudio Primary + Browser-Based Fallback
    - Primary: PulseAudio for actual audio capture/playback
    - Fallback: Browser Audio API interception for validation
    """
    
    # Selectors for audio UI elements
    MIC_BUTTON_SELECTOR = '[data-testid="prompt-microphone-button"]'
    MIC_BUTTON_RECORDING_CLASS = "prompt-input__button--recording"
    PLAY_SPEECH_BUTTON_SELECTOR = '[data-testid^="play-speech-button"]'
    PLAY_SPEECH_BUTTON_BY_ID = '[data-testid="play-speech-button-{turn_id}"]'
    TEXTAREA_SELECTOR = '[data-testid="prompt-input-textarea"]'
    SEND_BUTTON_SELECTOR = '[data-testid="prompt-send-button"]'
    BOT_MESSAGE_SELECTOR = '[data-testid="bot-message__text"]'
    
    def __init__(self, page: Page):
        """Initialize with Playwright Page object."""
        self.page = page
        self._tts_interception_active = False
        self._tts_api_interception_active = False
    
    # =========================================================================
    # Microphone Button Methods
    # =========================================================================
    
    async def is_mic_button_visible(self, timeout: int = 5000) -> bool:
        """Check if microphone button is visible."""
        try:
            mic_button = self.page.locator(self.MIC_BUTTON_SELECTOR)
            await mic_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
    
    async def get_mic_button_aria_label(self) -> str:
        """Get the aria-label of the microphone button."""
        mic_button = self.page.locator(self.MIC_BUTTON_SELECTOR)
        return await mic_button.get_attribute("aria-label") or ""
    
    async def is_recording(self) -> bool:
        """Check if currently recording (mic button shows 'Stop recording')."""
        try:
            aria_label = await self.get_mic_button_aria_label()
            return aria_label == "Stop recording"
        except Exception:
            return False
    
    async def click_mic_button(self) -> bool:
        """Click the microphone button (regardless of state).
        
        Uses force=True to handle CSS animations that make the button appear unstable.
        """
        try:
            mic_button = self.page.locator(self.MIC_BUTTON_SELECTOR)
            await mic_button.click(force=True)
            logger.info("Clicked microphone button")
            return True
        except Exception as e:
            logger.error(f"Failed to click mic button: {e}")
            return False

    async def start_recording(self) -> bool:
        """Click mic button to start recording."""
        try:
            mic_button = self.page.locator(self.MIC_BUTTON_SELECTOR)
            aria_label = await mic_button.get_attribute("aria-label")
            
            if aria_label == "Start recording":
                await mic_button.click(force=True)
                logger.info("Started recording")
                return True
            else:
                logger.warning(f"Mic button not in start state: {aria_label}")
                return False
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False
    
    async def stop_recording(self) -> bool:
        """Click mic button to stop recording.
        
        Uses force=True because the recording button has a CSS pulse animation
        that makes Playwright consider it 'unstable'.
        """
        try:
            mic_button = self.page.locator(self.MIC_BUTTON_SELECTOR)
            aria_label = await mic_button.get_attribute("aria-label")
            
            if aria_label == "Stop recording":
                await mic_button.click(force=True)
                logger.info("Stopped recording")
                return True
            else:
                logger.warning(f"Mic button not in recording state: {aria_label}")
                return False
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
    
    async def is_recording_animation_visible(self) -> bool:
        """Check if recording animation (CSS pulse) is visible on mic button."""
        try:
            mic_button = self.page.locator(self.MIC_BUTTON_SELECTOR)
            class_attr = await mic_button.get_attribute("class") or ""
            return self.MIC_BUTTON_RECORDING_CLASS in class_attr
        except Exception:
            return False

    async def wait_for_recording_state(self, recording: bool, timeout: int = 5000) -> bool:
        """
        Wait for recording state to change.
        
        Args:
            recording: True to wait for recording to start, False for stop
            timeout: Maximum wait time in ms
            
        Returns:
            True if desired state was reached
        """
        try:
            expected_label = "Stop recording" if recording else "Start recording"
            start_time = await self.page.evaluate("Date.now()")
            
            while True:
                current_label = await self.get_mic_button_aria_label()
                if current_label == expected_label:
                    return True
                
                elapsed = await self.page.evaluate("Date.now()") - start_time
                if elapsed > timeout:
                    logger.warning(f"Timeout waiting for recording={recording}, current: {current_label}")
                    return False
                await self.page.wait_for_timeout(100)
        except Exception as e:
            logger.error(f"Error waiting for recording state: {e}")
            return False

    async def wait_for_transcription(self, timeout: int = 30000) -> str:
        """
        Wait for transcription to appear in textarea.
        
        Alias for get_transcribed_text for better semantics.
        """
        return await self.get_transcribed_text(timeout=timeout)

    async def get_transcribed_text(self, timeout: int = 30000) -> str:
        """Wait for and get the transcribed text from textarea."""
        try:
            textarea = self.page.locator(self.TEXTAREA_SELECTOR)
            
            # Wait for text to appear
            start_time = await self.page.evaluate("Date.now()")
            while True:
                text = await textarea.input_value()
                if text and text.strip():
                    return text.strip()
                
                elapsed = await self.page.evaluate("Date.now()") - start_time
                if elapsed > timeout:
                    break
                await self.page.wait_for_timeout(500)
            
            return ""
        except Exception as e:
            logger.error(f"Failed to get transcribed text: {e}")
            return ""
    
    # =========================================================================
    # TTS Play Button Methods
    # =========================================================================
    
    async def is_play_speech_button_visible(self, timeout: int = 5000) -> bool:
        """Check if any play speech button is visible."""
        try:
            play_button = self.page.locator(self.PLAY_SPEECH_BUTTON_SELECTOR).first
            await play_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
    
    async def get_play_speech_buttons(self):
        """Get all play speech buttons."""
        return await self.page.locator(self.PLAY_SPEECH_BUTTON_SELECTOR).all()
    
    async def click_first_play_speech_button(self) -> Optional[str]:
        """Click the first play speech button and return its turn_id."""
        try:
            play_button = self.page.locator(self.PLAY_SPEECH_BUTTON_SELECTOR).first
            await play_button.wait_for(state="visible", timeout=5000)
            
            # Extract turn_id from data-testid
            testid = await play_button.get_attribute("data-testid")
            turn_id = testid.replace("play-speech-button-", "") if testid else None
            
            await play_button.click()
            logger.info(f"Clicked play speech button: {turn_id}")
            return turn_id
        except Exception as e:
            logger.error(f"Failed to click play speech button: {e}")
            return None
    
    async def get_play_speech_button_state(self, turn_id: str) -> str:
        """Get the state of a play speech button: 'idle', 'waiting', or 'playing'."""
        try:
            selector = self.PLAY_SPEECH_BUTTON_BY_ID.format(turn_id=turn_id)
            button = self.page.locator(selector)
            
            # Check data-state attribute or class for state
            state = await button.get_attribute("data-state")
            if state:
                return state
            
            class_attr = await button.get_attribute("class") or ""
            if "playing" in class_attr:
                return "playing"
            elif "waiting" in class_attr or "loading" in class_attr:
                return "waiting"
            return "idle"
        except Exception:
            return "idle"
    
    async def wait_for_tts_state(self, turn_id: str, state: str, timeout: int = 60000) -> bool:
        """Wait for TTS button to reach a specific state (default 60s for slow TTS)."""
        try:
            start = await self.page.evaluate("Date.now()")
            while True:
                current_state = await self.get_play_speech_button_state(turn_id)
                if current_state == state:
                    return True
                
                elapsed = await self.page.evaluate("Date.now()") - start
                if elapsed > timeout:
                    return False
                await self.page.wait_for_timeout(200)
        except Exception:
            return False
    
    # =========================================================================
    # TTS Browser Interception (Fallback Strategy)
    # =========================================================================
    
    async def setup_tts_interception(self) -> None:
        """
        Inject JavaScript to intercept browser Audio element for TTS tracking.
        
        This provides high-confidence testing without requiring PulseAudio:
        - Tracks Audio element creation
        - Monitors play, pause, ended, error events
        - Records playback duration
        """
        if self._tts_interception_active:
            return
        
        await self.page.evaluate("""
            () => {
                window.__ttsMetrics = {
                    played: false,
                    completed: false,
                    error: false,
                    duration: 0,
                    events: []
                };
                
                // Store original Audio constructor
                const OriginalAudio = window.Audio;
                
                // Override Audio constructor
                window.Audio = function(src) {
                    const audio = new OriginalAudio(src);
                    
                    audio.addEventListener('play', () => {
                        window.__ttsMetrics.played = true;
                        window.__ttsMetrics.events.push({type: 'play', time: Date.now()});
                    });
                    
                    audio.addEventListener('ended', () => {
                        window.__ttsMetrics.completed = true;
                        window.__ttsMetrics.duration = audio.duration || 0;
                        window.__ttsMetrics.events.push({type: 'ended', time: Date.now()});
                    });
                    
                    audio.addEventListener('error', (e) => {
                        window.__ttsMetrics.error = true;
                        window.__ttsMetrics.events.push({type: 'error', time: Date.now(), error: e.message});
                    });
                    
                    audio.addEventListener('pause', () => {
                        window.__ttsMetrics.events.push({type: 'pause', time: Date.now()});
                    });
                    
                    audio.addEventListener('abort', () => {
                        window.__ttsMetrics.events.push({type: 'abort', time: Date.now()});
                    });
                    
                    return audio;
                };
                
                // Preserve prototype chain
                window.Audio.prototype = OriginalAudio.prototype;
            }
        """)
        self._tts_interception_active = True
        logger.info("TTS browser interception set up")
    
    async def setup_tts_api_interception(self) -> None:
        """
        Set up route interception to validate TTS API responses.
        
        Intercepts /v1/audio/speech requests and validates:
        - Response status
        - Content type (audio/*)
        - Audio format validation (WAV/MP3/OGG headers)
        """
        if self._tts_api_interception_active:
            return
        
        async def handle_tts_route(route):
            response = await route.fetch()
            body = await response.body()
            
            # Check audio format by magic bytes
            is_valid_audio = False
            if body:
                # WAV: RIFF header
                if body[:4] == b'RIFF' and body[8:12] == b'WAVE':
                    is_valid_audio = True
                # MP3: ID3 or sync bits
                elif body[:3] == b'ID3' or (body[0] == 0xFF and (body[1] & 0xE0) == 0xE0):
                    is_valid_audio = True
                # OGG: OggS header
                elif body[:4] == b'OggS':
                    is_valid_audio = True
            
            # Store validation result
            await self.page.evaluate(f"""
                () => {{
                    window.__ttsApiResponse = {{
                        status: {response.status},
                        contentType: '{response.headers.get("content-type", "")}',
                        size: {len(body)},
                        isValidAudio: {str(is_valid_audio).lower()}
                    }};
                }}
            """)
            
            await route.fulfill(response=response)
        
        await self.page.route("**/v1/audio/speech**", handle_tts_route)
        self._tts_api_interception_active = True
        logger.info("TTS API interception set up")
    
    async def get_tts_metrics(self) -> dict:
        """Get TTS playback metrics from browser interception."""
        try:
            return await self.page.evaluate("() => window.__ttsMetrics || {}")
        except Exception:
            return {}
    
    async def get_tts_api_response(self) -> Optional[dict]:
        """Get TTS API response validation data."""
        try:
            return await self.page.evaluate("() => window.__ttsApiResponse || null")
        except Exception:
            return None
    
    async def wait_for_tts_playback_complete(self, timeout: int = 120000) -> dict:
        """Wait for TTS audio playback to complete (default 120s for slow TTS)."""
        try:
            start = await self.page.evaluate("Date.now()")
            while True:
                metrics = await self.get_tts_metrics()
                if metrics.get('completed') or metrics.get('error'):
                    return metrics
                
                elapsed = await self.page.evaluate("Date.now()") - start
                if elapsed > timeout:
                    logger.warning("TTS playback timeout")
                    return metrics
                
                await self.page.wait_for_timeout(500)
        except Exception as e:
            logger.error(f"Error waiting for TTS playback: {e}")
            return {}
    
    async def verify_tts_audio_played(self, min_duration: float = 0.5) -> dict:
        """
        Verify TTS audio was played with minimum duration.
        
        Args:
            min_duration: Minimum expected duration in seconds
            
        Returns:
            Dict with validation results
        """
        metrics = await self.get_tts_metrics()
        api_response = await self.get_tts_api_response()
        
        result = {
            'valid': False,
            'played': metrics.get('played', False),
            'completed': metrics.get('completed', False),
            'duration': metrics.get('duration', 0),
            'duration_ok': metrics.get('duration', 0) >= min_duration,
            'api_ok': api_response.get('isValidAudio', False) if api_response else False,
            'error': metrics.get('error', False)
        }
        
        result['valid'] = (
            result['played'] and
            result['completed'] and
            result['duration_ok'] and
            not result['error']
        )
        
        return result
    
    async def cleanup_tts_interception(self) -> None:
        """Clean up TTS interception."""
        try:
            if self._tts_api_interception_active:
                await self.page.unroute("**/v1/audio/speech**")
                self._tts_api_interception_active = False
            
            if self._tts_interception_active:
                await self.page.evaluate("""
                    () => {
                        delete window.__ttsMetrics;
                        delete window.__ttsApiResponse;
                    }
                """)
                self._tts_interception_active = False
        except Exception as e:
            logger.warning(f"Error cleaning up TTS interception: {e}")


class AudioChatUIHelper(ChatUIHelper):
    """
    Combined helper for audio-enabled chat UI testing.
    
    Extends ChatUIHelper with audio capabilities via composition.
    Provides unified interface for chat + audio interactions.
    """
    
    def __init__(self, page: Page, base_url: str, credentials: dict = None):
        """Initialize with Page, base URL, and optional credentials."""
        super().__init__(page, base_url)
        self.credentials = credentials or {}
        self.audio = AudioUIHelper(page)
    
    async def send_text_and_wait_response(self, text: str, timeout: int = 60000) -> Optional[str]:
        """Send text message and wait for bot response."""
        try:
            textarea = self.page.locator(self.audio.TEXTAREA_SELECTOR)
            await textarea.fill(text)
            
            send_button = self.page.locator(self.audio.SEND_BUTTON_SELECTOR)
            await send_button.click()
            
            bot_message = self.page.locator(self.audio.BOT_MESSAGE_SELECTOR).last
            await bot_message.wait_for(state="visible", timeout=timeout)
            await self.page.wait_for_timeout(3000)  # Wait for streaming
            
            return await bot_message.inner_text()
        except Exception as e:
            logger.error(f"Failed to send text and get response: {e}")
            return None