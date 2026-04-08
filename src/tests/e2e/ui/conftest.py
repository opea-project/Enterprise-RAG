"""
UI-specific conftest.py for Playwright testing with enhanced artifact management.

This module provides:
- Browser and page fixtures optimized for UI testing
- Logged-in page fixture for authenticated sessions
- Artifact management (screenshots, videos, logs) with rotation
- E2E file-based credential loading (like main e2e tests)
- Conditional video recording (only on failures)
"""
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

import pytest_asyncio as _pytest_asyncio_mod  # noqa: F401 — used for shared audio fixtures

from tests.e2e.helpers.audio_test_helpers import (
    AudioArtifactCollector,
    UnifiedAudioInput,
    VirtualMicAudioPlayer,
    pulseaudio_available,
)
from tests.e2e.helpers.audioqa_api_helper import AudioData, SherpaTTS
from tests.e2e.helpers.ui_helper import (AudioChatUIHelper, ChatUIHelper,
                                         DocSumUIHelper)
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Parse viewport dimensions once at module level — reused by browser & context fixtures.
_viewport_env = os.getenv('VIEWPORT', '1920x1080')
try:
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT = (int(v) for v in _viewport_env.split('x'))
except (ValueError, AttributeError):
    logger.warning(f"Invalid VIEWPORT '{_viewport_env}', falling back to 1920x1080")
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT = 1920, 1080


def _has_pipeline(pipeline_type: str) -> bool:
    """Check whether a pipeline of the given type is deployed."""
    return any(p.get("type") == pipeline_type for p in cfg.get("pipelines", []))


# Shared skip markers — import these in test modules instead of copy-pasting
# the for/else config loop.
requires_chatqa = pytest.mark.skipif(
    not _has_pipeline("chatqa"),
    reason="ChatQA pipeline is not deployed",
)
requires_docsum = pytest.mark.skipif(
    not _has_pipeline("docsum"),
    reason="DocSum pipeline is not deployed",
)

def _find_project_root() -> Path:
    """Walk up from this file to find the project root (contains src/)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "src").is_dir():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent.parent.parent


_PROJECT_ROOT = _find_project_root()

# Artifact directories
ARTIFACT_BASE = _PROJECT_ROOT / "test-results"
UI_LOG_DIR = _PROJECT_ROOT / "test_logs" / "test_ui"
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


@pytest.fixture(scope="session")
def maintainer_credentials(keycloak_helper):
    """Maintainer user credentials, with required actions temporarily removed."""
    username = keycloak_helper.erag_maintainer_username
    if username:
        required_actions = keycloak_helper.read_current_required_actions(
            keycloak_helper.admin_access_token, username
        )
        if required_actions:
            keycloak_helper.remove_required_actions(
                keycloak_helper.admin_access_token, username
            )
    return {
        'username': username,
        'password': keycloak_helper.erag_maintainer_password,
        'user_type': 'maintainer'
    }


@pytest.fixture(scope="session")
def user_credentials(keycloak_helper):
    """Regular user credentials, with required actions temporarily removed."""
    username = keycloak_helper.erag_user_username
    required_actions = keycloak_helper.read_current_required_actions(
        keycloak_helper.admin_access_token, username
    )
    if required_actions:
        keycloak_helper.remove_required_actions(
            keycloak_helper.admin_access_token, username
        )
    return {
        'username': username,
        'password': keycloak_helper.erag_user_password,
        'user_type': 'user'
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
                    file_to_remove.unlink(missing_ok=True)
                    logger.debug(f"Removed file: {file_to_remove.name}")
                elif file_to_remove.is_dir():
                    shutil.rmtree(file_to_remove, ignore_errors=True)
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

    vp_width, vp_height = VIEWPORT_WIDTH, VIEWPORT_HEIGHT

    logger.info(f"Launching Firefox browser... (headless={headless}, display={display}, viewport={vp_width}x{vp_height})")

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
            f"--width={vp_width}",
            f"--height={vp_height}"
        ])

    # Firefox preferences for audio testing - auto-grant microphone permissions
    # This is required for AudioQnA tests that use the microphone
    firefox_prefs = {
        "permissions.default.microphone": 1,  # Auto-grant microphone permission
        "media.navigator.streams.fake": True,  # Use fake media streams
        "media.navigator.permission.disabled": True,  # Disable permission prompts
        "dom.webnotifications.enabled": False,  # Disable notifications
        "dom.push.enabled": False,  # Disable push notifications
    }

    browser = await playwright_instance.firefox.launch(
        headless=headless,
        args=launch_args,
        firefox_user_prefs=firefox_prefs
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

    vp_width, vp_height = VIEWPORT_WIDTH, VIEWPORT_HEIGHT

    context = await browser.new_context(
        viewport={"width": vp_width, "height": vp_height},
        record_video_dir=str(video_path),
        record_video_size={"width": vp_width, "height": vp_height},
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

    # Add console logging — open file once, close in teardown
    log_handle = open(log_file, "a")  # noqa: SIM115

    def log_console(msg):
        log_handle.write(f"[CONSOLE] {msg.type}: {msg.text}\n")
        log_handle.flush()

    page.on("console", log_console)

    yield page

    log_handle.close()

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


@pytest_asyncio.fixture
async def chat_ui_helper_maintainer(page, maintainer_credentials):
    """Create chat helper authenticated as maintainer."""
    helper = ChatUIHelper(page, base_url=cfg.get('FQDN'))
    await helper.login(
        maintainer_credentials['username'],
        maintainer_credentials['password'],
    )
    logger.info("Chat helper (maintainer) ready")
    yield helper


@pytest_asyncio.fixture
async def chat_ui_helper_user(page, user_credentials):
    """Create chat helper authenticated as regular user."""
    helper = ChatUIHelper(page, base_url=cfg.get('FQDN'))
    await helper.login(
        user_credentials['username'],
        user_credentials['password'],
    )
    logger.info("Chat helper (user) ready")
    yield helper


@pytest_asyncio.fixture
async def docsum_ui_helper(page, admin_credentials):
    """
    Create DocSum UI helper with authenticated session.

    The DocSum UI has a different entry point ({domain}/docsum) than Chat.
    This fixture handles login and navigation to the DocSum paste-text page.

    Args:
        page: Playwright page fixture
        admin_credentials: Admin credentials fixture

    Yields:
        DocSumUIHelper instance ready for DocSum UI testing
    """
    username = admin_credentials['username']
    password = admin_credentials['password']

    # Initialize DocSum helper
    docsum_helper = DocSumUIHelper(page, base_url=cfg.get('FQDN'))

    # Login and navigate to DocSum UI
    login_success = await docsum_helper.login_and_navigate_to_docsum(username, password)

    if not login_success:
        pytest.fail("Failed to login and navigate to DocSum UI")

    logger.info("DocSum UI helper ready")
    yield docsum_helper


@pytest_asyncio.fixture
async def audio_chat_ui_helper(page, admin_credentials):
    """
    Create audio chat helper with authenticated session.

    Combines chat functionality with audio capabilities (mic, TTS).

    Args:
        page: Playwright page fixture
        admin_credentials: Admin credentials fixture

    Yields:
        AudioChatUIHelper instance
    """
    username = admin_credentials['username']
    password = admin_credentials['password']

    # Initialize and login
    helper = AudioChatUIHelper(page, base_url=cfg.get('FQDN'), credentials=admin_credentials)
    await helper.login_as_admin(username, password)

    logger.info("Audio chat helper ready")
    yield helper


# =============================================================================
# Shared Audio Fixtures (used by test_audio_prompting and test_tts_playback)
# =============================================================================

@pytest.fixture(scope="module")
def virtual_mic_player():
    """PulseAudio virtual microphone player. Skips if PulseAudio unavailable."""
    if not pulseaudio_available():
        pytest.skip("PulseAudio not available - audio tests require PulseAudio")

    player = VirtualMicAudioPlayer()
    if player.setup():
        logger.info("Virtual microphone player ready")
        yield player
        player.cleanup()
    else:
        pytest.skip("Failed to set up PulseAudio virtual microphone")


@pytest.fixture(scope="module")
def sherpa_tts():
    """SherpaTTS instance for audio generation (module-scoped for reuse)."""
    return SherpaTTS()


@pytest_asyncio.fixture
async def unified_audio_input(
    audio_chat_ui_helper,
    sherpa_tts,
    virtual_mic_player,
    request,
):
    """UnifiedAudioInput with PulseAudio virtual microphone and artifact collection."""
    test_name = request.node.name.replace("::", "_")
    artifact_collector = AudioArtifactCollector(test_name)

    def collect_audio(audio_data: AudioData = None, output_bytes: bytes = None, source: str = ""):
        if audio_data:
            artifact_collector.collect_input_audio(audio_data)
        if output_bytes:
            artifact_collector.collect_output_audio(output_bytes, source)

    unified = UnifiedAudioInput(
        audio_helper=audio_chat_ui_helper,
        tts=sherpa_tts,
        virtual_mic_player=virtual_mic_player,
        audio_artifacts_collector=collect_audio,
    )

    logger.info("UnifiedAudioInput ready with PulseAudio virtual microphone")

    yield unified

    await unified.cleanup()

    test_failed = (
        hasattr(request.node, "rep_call") and request.node.rep_call.failed
    ) or (
        hasattr(request.node, "rep_setup") and request.node.rep_setup.failed
    )

    if test_failed:
        saved = artifact_collector.save_artifacts(attach_to_allure=True)
        if saved:
            logger.info(f"Audio artifacts saved for failed test: {list(saved.keys())}")
        AudioArtifactCollector.rotate_old_artifacts(keep_count=10)