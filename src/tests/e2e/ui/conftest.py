"""
UI-specific conftest.py for Playwright testing with enhanced artifact management.

This module provides:
- Browser and page fixtures optimized for UI testing
- Logged-in page fixture for authenticated sessions
- Artifact management (screenshots, videos, logs) with rotation
- E2E file-based credential loading (like main e2e tests)
- Conditional video recording (only on failures)
"""
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from tests.e2e.helpers.ui_helper import ChatUIHelper
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Artifact directories
ARTIFACT_BASE = Path(__file__).parent.parent.parent.parent.parent / "test-results"
UI_LOG_DIR = Path(__file__).parent.parent.parent.parent.parent / "test_logs" / "test_ui"
SCREENSHOT_DIR = ARTIFACT_BASE / "screenshots"
VIDEO_DIR = ARTIFACT_BASE / "videos"


@pytest.fixture(scope="session")
def admin_credentials(keycloak_helper):
    """Admin user credentials from KeycloakHelper."""
    return {
        'username': keycloak_helper.erag_admin_username,
        'password': keycloak_helper.erag_admin_password,
        'user_type': 'admin'
    }


def rotate_artifacts(directory: Path, keep_count: int = 2):
    """
    Keep only the most recent artifacts, removing older ones.

    Args:
        directory: Directory to clean up
        keep_count: Number of most recent files to keep
    """
    try:
        if not directory.exists():
            logger.debug(f"Directory {directory} does not exist, skipping cleanup")
            return

        logger.info(f"Cleaning up {directory}...")

        # Get all files sorted by modification time (newest first)
        files = list(directory.glob("*"))
        if not files:
            logger.debug(f"No files found in {directory}")
            return

        files_sorted = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
        files_to_remove = files_sorted[keep_count:]

        logger.info(f"Found {len(files)} files, keeping {min(len(files), keep_count)}, removing {len(files_to_remove)}")

        # Remove files beyond keep_count
        for i, file_to_remove in enumerate(files_to_remove):
            try:
                if file_to_remove.is_file():
                    file_to_remove.unlink()
                    logger.debug(f"Removed file: {file_to_remove.name}")
                elif file_to_remove.is_dir():
                    shutil.rmtree(file_to_remove)
                    logger.debug(f"Removed directory: {file_to_remove.name}")

                # Limit to avoid hanging on large directories
                if i >= 50:  # Max 50 files to remove per cleanup
                    logger.warning(f"Cleanup limit reached, stopped at {i+1} files")
                    break

            except OSError as e:
                logger.warning(f"Could not remove {file_to_remove}: {e}")

    except Exception as e:
        logger.error(f"Error during artifact cleanup for {directory}: {e}")


def setup_ui_logging(test_name: str) -> Path:
    """
    Set up logging for a specific UI test.

    Args:
        test_name: Name of the test for log file naming

    Returns:
        Path to the log file
    """
    # Create directory if it doesn't exist
    UI_LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = UI_LOG_DIR / f"ui_test_{test_name}_{timestamp}.log"

    # Only rotate if there are many files to avoid hanging
    try:
        existing_files = list(UI_LOG_DIR.glob("*.log"))
        if len(existing_files) > 10:  # Only cleanup when we have many files
            rotate_artifacts(UI_LOG_DIR, keep_count=3)
    except Exception as e:
        logger.warning(f"Failed to rotate log artifacts during setup: {e}")

    return log_file


@pytest_asyncio.fixture(scope="function")
async def playwright_instance():
    """Playwright instance for each test."""
    logger.debug("Starting Playwright instance...")
    async with async_playwright() as p:
        logger.debug("Playwright instance created successfully")
        yield p
    logger.debug("Playwright instance closed")


@pytest_asyncio.fixture(scope="function")
async def browser(playwright_instance):
    """
    Browser instance configured for UI testing.
    Uses Firefox with SSL verification disabled for testing environments.
    """
    # Detect if we should run headless or visible
    # Default to headless=True, but allow HEADLESS=false to enable VNC display
    headless_env = os.getenv('HEADLESS', 'true').lower()
    headless = headless_env in ('true', '1', 'yes')
    display = os.getenv('DISPLAY')

    logger.info(f"Launching Firefox browser... (headless={headless}, display={display})")

    # Configure launch arguments
    launch_args = [
        "--ignore-certificate-errors",
        "--ignore-ssl-errors",
        "--ignore-certificate-errors-spki-list",
        "--disable-web-security"
    ]

    # Add window size arguments for non-headless mode to fit screen
    if not headless:
        launch_args.extend([
            "--width=1920",
            "--height=1080"
        ])

    browser = await playwright_instance.firefox.launch(
        headless=headless,
        args=launch_args
    )
    logger.info("Firefox browser launched successfully")
    yield browser
    logger.info("Closing Firefox browser...")
    await browser.close()
    logger.debug("Firefox browser closed")


@pytest_asyncio.fixture(scope="function")
async def context(browser, request):
    """
    Browser context with video recording configured.
    Videos are only kept on test failures.
    """
    test_name = request.node.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = VIDEO_DIR / f"test_{test_name}_{timestamp}"

    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(video_path),
        record_video_size={"width": 1920, "height": 1080},
        ignore_https_errors=True  # Ignore SSL errors for testing
    )

    yield context

    # Handle video recording based on test outcome
    await context.close()

    # Check if test failed (video should be kept)
    test_failed = (
        hasattr(request.node, 'rep_call') and request.node.rep_call.failed
    ) or (
        hasattr(request.node, 'rep_setup') and request.node.rep_setup.failed
    )

    if not test_failed:
        # Remove video directory if test passed
        try:
            if video_path.exists():
                shutil.rmtree(video_path)
        except OSError as e:
            logger.warning(f"Could not remove video directory {video_path}: {e}")
    else:
        # Rotate old videos (keep only recent failures)
        rotate_artifacts(VIDEO_DIR)


@pytest_asyncio.fixture(scope="function")
async def page(context, request):
    """
    Page instance with screenshot capability on failures.
    """
    page = await context.new_page()

    # Set up UI logging for this test
    test_name = request.node.name.replace("::", "_")
    log_file = setup_ui_logging(test_name)

    # Add console logging
    def log_console(msg):
        with open(log_file, 'a') as f:
            f.write(f"[CONSOLE] {msg.type}: {msg.text}\n")

    page.on("console", log_console)

    yield page

    # Take screenshot on failure
    test_failed = (
        hasattr(request.node, 'rep_call') and request.node.rep_call.failed
    ) or (
        hasattr(request.node, 'rep_setup') and request.node.rep_setup.failed
    )

    if test_failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = SCREENSHOT_DIR / f"failure_{test_name}_{timestamp}.png"
        try:
            # Take screenshot and save to file
            await page.screenshot(path=str(screenshot_path), full_page=True)

            # Attach screenshot to Allure report using file path
            # This ensures it appears in the test body, not just fixture teardown
            try:
                import allure
                allure.attach.file(
                    str(screenshot_path),
                    name=f"Screenshot: {test_name}",
                    attachment_type=allure.attachment_type.PNG
                )
                logger.debug(f"Screenshot attached to Allure report: {test_name}")
            except ImportError:
                logger.debug("Allure not available, screenshot saved to file only")

            # Rotate old screenshots
            rotate_artifacts(SCREENSHOT_DIR)
        except Exception as e:
            logger.warning(f"Could not take screenshot: {e}")

    await page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results for conditional artifact management.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session", autouse=True)
def cleanup_old_artifacts():
    """
    Session-level fixture to clean up old artifacts before starting tests.
    """
    import time

    # Skip cleanup if disabled by environment variable
    if os.getenv('SKIP_ARTIFACT_CLEANUP', '').lower() in ('true', '1', 'yes'):
        logger.info("Artifact cleanup skipped (SKIP_ARTIFACT_CLEANUP set)")
        yield
        return

    start_time = time.time()

    logger.info("Cleaning up old test artifacts...")
    directories = [UI_LOG_DIR, SCREENSHOT_DIR, VIDEO_DIR]

    for directory in directories:
        try:
            # Timeout protection - skip if taking too long
            if time.time() - start_time > 10:  # 10 second timeout
                logger.warning("Cleanup timeout reached, skipping remaining directories")
                break

            rotate_artifacts(directory, keep_count=2)
        except Exception as e:
            logger.error(f"Failed to cleanup {directory}: {e}")

    cleanup_time = time.time() - start_time
    logger.info(f"Artifact cleanup completed in {cleanup_time:.2f} seconds")
    logger.debug("Proceeding with test setup...")

    yield

    # No final cleanup to avoid hanging at teardown
    logger.debug("Test session completed")


@pytest_asyncio.fixture
async def chat_ui_helper(page, admin_credentials):
    """
    Create chat helper with authenticated session.

    Args:
        page: Playwright page fixture
        admin_credentials: Admin credentials fixture

    Yields:
        ChatUIHelper instance
    """
    username = admin_credentials['username']
    password = admin_credentials['password']

    # Initialize and login
    chat_ui_helper = ChatUIHelper(page, base_url=cfg.get('FQDN'))
    await chat_ui_helper.login_as_admin(username, password)

    logger.info("Chat helper ready")
    yield chat_ui_helper
