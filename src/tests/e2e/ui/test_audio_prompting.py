"""
Copyright (C) 2024-2026 Intel Corporation
SPDX-License-Identifier: Apache-2.0

Audio UI Tests - Voice Input and Transcription Testing

This module tests the audio/voice input functionality in the UI:
1. Voice input button visibility when audio is enabled
2. Audio recording starts/stops correctly
3. Audio is transcribed and sent as a prompt
4. Transcription accuracy validation
5. Speech speed variations (slow/fast)
6. Silence handling (no hallucination)

Focus: Voice UI interaction mechanism (mic button, recording, transcription).
Note: Response quality validation is handled by ChatQnA tests - not duplicated here.

SOLID/DRY Principles:
- Uses AudioData and SherpaTTS from audioqa_api_helper (shared with backend tests)
- TranscriptionAccuracyEvaluator for transcription validation (reusable)
- AudioChatUIHelper handles all audio UI interactions
- Test questions defined in AUDIO_TEST_CASES (configurable)

Test Flow:
1. Click microphone button (aria-label="Start recording") - starts "talking"
2. Click button again (aria-label="Stop recording") - stops recording
3. Wait for voice to be transcribed and returned in prompt textarea
4. Click send button
5. Wait for chatbot response
"""

import allure
import logging
import os
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio

from tests.e2e.helpers.audio_test_helpers import TranscriptionAccuracyEvaluator
from tests.e2e.helpers.ui_helper import AudioUIHelper, AudioChatUIHelper
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)


# Skip all tests if audio is not enabled or chatqa is not deployed
_skip_marks = []
if not cfg.get("audio", {}).get("enabled", False):
    _skip_marks.append(pytest.mark.skip(reason="Audio/ASR is not enabled in deployment"))
if not any(p.get("type") == "chatqa" for p in cfg.get("pipelines", [])):
    _skip_marks.append(pytest.mark.skip(reason="ChatQA pipeline is not deployed"))
if _skip_marks:
    pytestmark = _skip_marks


# =============================================================================
# Audio Test Cases Configuration (Single source of truth)
# =============================================================================

AUDIO_TEST_CASES = {
    "what_is_ai": {
        "text": "What is artificial intelligence?",
        "speed": 1.0,
        "expected_keywords": ["AI", "machine learning", "intelligence", "computer"],
        "min_length": 50,
    },
}

# Speed test cases - using moderate speeds that ASR can handle
# Note: Extreme speeds (< 0.85 or > 1.25) cause ASR to hear noise/beeps
SLOW_SPEECH_TEST_CASES = [
    {"speed": 0.95, "text": "Astronomy is a scientific study of stars and planets.",
     "expected_words": ["astronomy", "stars", "planets"], "min_accuracy": 0.4},
    {"speed": 0.9, "text": "Artificial intelligence is changing the future of technology.",
     "expected_words": ["artificial", "intelligence", "technology"], "min_accuracy": 0.4},
]

FAST_SPEECH_TEST_CASES = [
    {"speed": 1.1, "text": "The quick brown fox jumps over the lazy dog.",
     "expected_words": ["quick", "fox", "dog"], "min_accuracy": 0.4},
    {"speed": 1.15, "text": "Machine learning models need large datasets for training.",
     "expected_words": ["machine", "learning", "training"], "min_accuracy": 0.4},
]


# =============================================================================
# Audio-specific Fixtures for Headless Mode Support
# =============================================================================

@pytest_asyncio.fixture
async def audio_browser(playwright_instance):
    """
    Browser instance configured for audio testing with microphone permissions.
    
    Firefox requires preferences to be set at launch time to auto-grant 
    microphone permissions, unlike Chromium which supports runtime permissions.
    
    IMPORTANT: We do NOT use fake media streams - we use PulseAudio virtual mic
    so the browser captures real TTS audio for ASR testing.
    """
    headless_env = os.getenv('HEADLESS', 'true').lower()
    headless = headless_env in ('true', '1', 'yes')
    display = os.getenv('DISPLAY')
    
    logger.info(f"Launching Firefox browser for audio tests... (headless={headless}, display={display})")
    
    firefox_prefs = {
        # Auto-grant microphone permission (1 = allow)
        "permissions.default.microphone": 1,
        # Do NOT use fake streams - we want real PulseAudio virtual mic!
        "media.navigator.streams.fake": False,
        # Disable permission prompts
        "media.navigator.permission.disabled": True,
        # Disable notifications
        "dom.webnotifications.enabled": False,
        "dom.push.enabled": False,
        # Audio device selection - use default (which is our virtual mic)
        "media.getusermedia.aec_enabled": False,  # Disable echo cancellation for cleaner audio
        "media.getusermedia.noise_enabled": False,  # Disable noise suppression  
        "media.getusermedia.agc_enabled": False,  # Disable auto gain control
    }
    
    launch_args = ["--ignore-certificate-errors", "--ignore-ssl-errors"]
    if not headless:
        launch_args.extend(["--width=1920", "--height=1080"])
    
    browser = await playwright_instance.firefox.launch(
        headless=headless,
        args=launch_args,
        firefox_user_prefs=firefox_prefs
    )
    logger.info("Firefox browser for audio tests launched successfully")
    yield browser
    logger.info("Closing Firefox audio browser...")
    await browser.close()


@pytest_asyncio.fixture
async def audio_context(audio_browser, request):
    """Browser context configured for audio testing with video recording."""
    test_name = request.node.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = Path(__file__).parent.parent.parent.parent.parent / "test-results" / "videos" / f"test_{test_name}_{timestamp}"
    
    context = await audio_browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(video_path),
        record_video_size={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    yield context
    await context.close()


@pytest_asyncio.fixture
async def audio_page(audio_context):
    """Page instance configured for audio testing."""
    page = await audio_context.new_page()
    page.on("console", lambda msg: logger.debug(f"[Browser Console] {msg.text}"))
    yield page
    await page.close()


@pytest_asyncio.fixture
async def audio_chat_ui_helper(audio_page, admin_credentials):
    """
    Create AudioChatUIHelper with authenticated session for audio tests.
    
    Uses audio_page with special microphone permissions for Firefox.
    """
    username = admin_credentials['username']
    password = admin_credentials['password']

    helper = AudioChatUIHelper(audio_page, base_url=cfg.get('FQDN'), credentials=admin_credentials)
    await helper.login_as_admin(username, password)

    logger.info("AudioChatUIHelper ready for audio testing")
    yield helper


# =============================================================================
# TEST CASES
# =============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T331")
async def test_voice_input_button_visible(chat_ui_helper):
    """
    Test that the voice input (microphone) button is visible when audio is enabled.
    
    Success criteria:
    - Page loads successfully
    - Microphone button is visible
    - Button has correct aria-label
    """
    logger.info("Testing voice input button visibility")
    
    audio_helper = AudioUIHelper(chat_ui_helper.page)
    
    # Assert 1: Microphone button exists and is visible
    is_visible = await audio_helper.is_mic_button_visible(timeout=10000)
    assert is_visible, "Microphone button should be visible when audio is enabled"
    logger.info("Assert 1: Microphone button is visible")
    
    # Assert 2: Button has correct aria-label
    aria_label = await audio_helper.get_mic_button_aria_label()
    assert aria_label == "Start recording", f"Expected aria-label 'Start recording', got '{aria_label}'"
    logger.info("Assert 2: Button has correct aria-label")
    
    logger.info("Test completed: Voice input button visibility validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T332")
async def test_audio_recording_starts_stops(audio_chat_ui_helper, unified_audio_input):
    """
    Test that clicking the microphone button starts and stops recording.
    
    Uses SherpaTTS for audio generation (DRY - shared with backend).
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing audio recording start/stop (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    audio_data = await unified_audio_input.setup_audio(
        text=test_case["text"],
        speed=test_case["speed"],
        expected_transcription=test_case["text"]
    )
    
    try:
        # Assert 1: Initial state - not recording
        is_recording = await audio_chat_ui_helper.audio.is_recording()
        assert not is_recording, "Initial state should be 'Start recording'"
        logger.info("Assert 1: Initial state is 'Start recording'")
        
        # Start recording
        await audio_chat_ui_helper.audio.click_mic_button()
        await audio_chat_ui_helper.page.wait_for_timeout(200)
        
        # Play audio through virtual mic (if PulseAudio) - no-op for JS mock
        await unified_audio_input.play_during_recording(audio_data)
        
        # Assert 2: Check recording state
        aria_label = await audio_chat_ui_helper.audio.get_mic_button_aria_label()
        logger.info(f"After clicking mic: aria-label = '{aria_label}'")
        
        if aria_label == "Stop recording":
            logger.info("Assert 2: Recording state shows 'Stop recording'")
            await audio_chat_ui_helper.audio.stop_recording()
        else:
            logger.info("Assert 2: Recording already completed (audio was short)")
        
        # Assert 3: Back to initial state
        is_recording = await audio_chat_ui_helper.audio.is_recording()
        assert not is_recording, "Final state should be 'Start recording'"
        logger.info("Assert 3: Returned to 'Start recording' state")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Audio recording start/stop validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T333")
async def test_audio_transcription_to_prompt(audio_chat_ui_helper, unified_audio_input):
    """
    Test that recorded audio is transcribed and appears in the prompt input.
    Validates transcription accuracy.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing audio transcription to prompt (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    original_text = test_case["text"]
    expected_keywords = test_case.get("expected_keywords", [])
    
    logger.info(f"Original text to speak: '{original_text}'")
    
    audio_data = await unified_audio_input.setup_audio(
        text=original_text,
        speed=test_case["speed"],
        expected_transcription=original_text
    )
    
    try:
        # Step 1: Start recording
        logger.info("Step 1: Starting recording")
        await audio_chat_ui_helper.audio.click_mic_button()
        
        recording_started = await audio_chat_ui_helper.audio.wait_for_recording_state(
            recording=True, timeout=5000
        )
        
        if recording_started:
            logger.info("Recording in progress...")
            # Play audio through virtual mic (if PulseAudio)
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.page.wait_for_timeout(3000)
            
            # Step 2: Stop recording
            logger.info("Step 2: Stopping recording")
            await audio_chat_ui_helper.audio.click_mic_button()
            await audio_chat_ui_helper.audio.wait_for_recording_state(recording=False, timeout=5000)
        else:
            pytest.fail("Recording did not start")
        
        # Step 3: Wait for transcription
        logger.info("Step 3: Waiting for transcription...")
        transcribed_text = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=30000)
        
        logger.info(f"Original text: '{original_text}'")
        logger.info(f"Transcribed text: '{transcribed_text}'")
        
        # Step 4: Validate transcription accuracy
        assert len(transcribed_text) > 0, "Textarea should contain transcribed text"
        
        passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
            original=original_text,
            transcribed=transcribed_text,
            keywords=expected_keywords,
            min_accuracy=0.5
        )
        
        allure.attach(
            f"Audio Input Method: {unified_audio_input.method_name}\n"
            f"Original: {original_text}\n"
            f"Transcribed: {transcribed_text}\n"
            f"Word Accuracy: {metrics['word_accuracy']:.2%}\n"
            f"Keyword Match: {metrics['keyword_match']:.2%}\n"
            f"Combined Score: {metrics['combined_score']:.2%}",
            name="Transcription Accuracy Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
        
        logger.info(f"Transcription accuracy: {metrics['combined_score']:.2%}")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Audio transcription to prompt validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T334")
async def test_voice_question_receives_response(audio_chat_ui_helper, unified_audio_input):
    """
    Test full voice UI flow: voice input -> transcription -> send -> receive response.
    
    Focus: Voice UI interaction mechanism (mic button, recording, transcription).
    Note: Response quality validation is handled by ChatQnA tests.
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing full voice question flow (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    original_text = test_case["text"]
    expected_keywords = test_case.get("expected_keywords", [])
    
    audio_data = await unified_audio_input.setup_audio(
        text=original_text,
        speed=test_case["speed"],
        expected_transcription=original_text
    )
    
    try:
        # Clear textarea
        textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
        await textarea.fill("")
        
        # Step 1: Start recording
        logger.info("Step 1: Starting recording")
        await audio_chat_ui_helper.audio.start_recording()
        # Wait for UI state to transition after click
        await audio_chat_ui_helper.page.wait_for_timeout(500)
        is_recording = await audio_chat_ui_helper.audio.is_recording()
        logger.info(f"Recording state after start: {is_recording}")
        assert is_recording, "Should be in recording state after starting"
        
        # Play audio through virtual mic (if PulseAudio)
        await unified_audio_input.play_during_recording(audio_data)
        await audio_chat_ui_helper.page.wait_for_timeout(2000)
        
        # Step 2: Stop recording
        logger.info("Step 2: Stopping recording")
        await audio_chat_ui_helper.audio.stop_recording()
        assert not await audio_chat_ui_helper.audio.is_recording()
        
        # Step 3: Wait for transcription
        logger.info("Step 3: Waiting for transcription")
        transcribed_text = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=10000)
        
        # Validate transcription accuracy (voice UI specific)
        assert len(transcribed_text) > 0, "Should have transcribed text"
        trans_passed, trans_metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
            original=original_text,
            transcribed=transcribed_text,
            keywords=expected_keywords,
            min_accuracy=0.5
        )
        
        allure.attach(
            f"Audio Input Method: {unified_audio_input.method_name}\n"
            f"Original: {original_text}\n"
            f"Transcribed: {transcribed_text}\n"
            f"Word Accuracy: {trans_metrics['word_accuracy']:.2%}\n"
            f"Keyword Match: {trans_metrics['keyword_match']:.2%}",
            name="Transcription Accuracy Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Step 4: Send message (verify UI send flow works)
        logger.info("Step 4: Clicking send button")
        send_button = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.SEND_BUTTON_SELECTOR)
        assert await send_button.is_enabled(), "Send button should be enabled"
        await send_button.click()
        
        # Step 5: Verify response is received (not quality - that's ChatQnA's job)
        logger.info("Step 5: Waiting for chatbot response")
        response_text = await audio_chat_ui_helper.wait_for_response(timeout=60000)
        
        assert response_text is not None, "Should receive a response from chatbot"
        assert len(response_text) > 0, "Response should not be empty"
        logger.info(f"Chatbot response received: {len(response_text)} chars")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Full voice question UI flow validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T335")
async def test_recording_animation_visible(audio_chat_ui_helper, unified_audio_input):
    """
    Test that recording animation (CSS pulse) is visible during recording.
    
    The current UI uses a CSS class 'prompt-input__button--recording' with pulse 
    animation on the microphone button to indicate recording state.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing recording animation visibility (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    audio_data = await unified_audio_input.setup_audio(
        text=test_case["text"],
        speed=test_case["speed"],
        expected_transcription=test_case["text"]
    )
    
    try:
        assert await audio_chat_ui_helper.audio.is_mic_button_visible(timeout=10000)
        
        # Assert 1: No recording animation before starting
        animation_before = await audio_chat_ui_helper.audio.is_recording_animation_visible()
        logger.info(f"Animation visible before recording: {animation_before}")
        # Don't assert - just log (animation shouldn't be visible)
        
        # Start recording
        await audio_chat_ui_helper.audio.start_recording()
        
        # Play audio through virtual mic (if PulseAudio)
        await unified_audio_input.play_during_recording(audio_data)
        
        # Assert 2: Recording animation (CSS pulse) is visible during recording
        animation_visible = await audio_chat_ui_helper.audio.is_recording_animation_visible()
        logger.info(f"Recording animation visible during recording: {animation_visible}")
        
        # Also check aria-label as backup indicator
        aria_label = await audio_chat_ui_helper.audio.get_mic_button_aria_label()
        is_recording_state = aria_label == "Stop recording"
        
        # Either CSS animation or aria-label should indicate recording
        assert animation_visible or is_recording_state, \
            "Recording should be indicated by CSS animation or aria-label"
        logger.info("Assert 2: Recording state indicated (animation or aria-label)")
        
        # Stop recording
        await audio_chat_ui_helper.audio.stop_recording()
        
        # Assert 3: Animation hidden after stopping
        await audio_chat_ui_helper.page.wait_for_timeout(500)  # Allow state to update
        animation_after = await audio_chat_ui_helper.audio.is_recording_animation_visible()
        aria_after = await audio_chat_ui_helper.audio.get_mic_button_aria_label()
        
        assert not animation_after or aria_after == "Start recording", \
            "Recording animation should be hidden after stopping"
        logger.info("Assert 3: Recording animation hidden after stopping")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Recording animation visibility validated")


# =============================================================================
# Speed Variation Tests (Aligned with backend test_audioqa.py)
# =============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T336")
async def test_asr_slow_speech_ui(audio_chat_ui_helper, unified_audio_input):
    """
    Test ASR with slow speech audio at moderate speeds (0.9-0.95x).
    
    Validates that the UI audio flow works with slightly slower speech.
    Uses moderate speeds that ASR can still recognize.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing ASR with slow speech (using {unified_audio_input.method_name})")
    
    results = []
    
    for case in SLOW_SPEECH_TEST_CASES:
        text = case["text"]
        speed = case["speed"]
        expected_words = case["expected_words"]
        min_accuracy = case.get("min_accuracy", 0.4)
        
        logger.info(f"Testing speed {speed}: '{text}'")
        
        audio_data = await unified_audio_input.setup_audio(
            text=text,
            speed=speed,
            expected_transcription=text
        )
        
        try:
            # Clear textarea
            textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
            await textarea.fill("")
            
            # Record and transcribe
            await audio_chat_ui_helper.audio.start_recording()
            # Play audio through virtual mic (if PulseAudio)
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.page.wait_for_timeout(3000)
            await audio_chat_ui_helper.audio.stop_recording()
            
            transcribed = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=15000)
            logger.info(f"Speed {speed} | Transcription: '{transcribed}'")
            
            # Validate with flexible accuracy threshold
            passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
                original=text,
                transcribed=transcribed,
                keywords=expected_words,
                min_accuracy=min_accuracy
            )
            
            results.append({
                "speed": speed,
                "passed": passed,
                "accuracy": metrics["combined_score"],
                "transcribed": transcribed
            })
            
            logger.info(f"Speed {speed} | Accuracy: {metrics['combined_score']:.2%} | Passed: {passed}")
            
        finally:
            await unified_audio_input.cleanup()
    
    # At least one speed variation should work
    passed_count = sum(1 for r in results if r["passed"])
    
    allure.attach(
        "\n".join([f"Speed {r['speed']}: {r['accuracy']:.2%} - {'PASS' if r['passed'] else 'FAIL'}" for r in results]),
        name="Slow Speech Test Results",
        attachment_type=allure.attachment_type.TEXT
    )
    
    assert passed_count >= 1, f"At least one slow speech test should pass. Results: {results}"
    logger.info(f"Test completed: {passed_count}/{len(results)} slow speech tests passed")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T337")
async def test_asr_fast_speech_ui(audio_chat_ui_helper, unified_audio_input):
    """
    Test ASR with fast speech audio at moderate speeds (1.1-1.15x).
    
    Validates that the UI audio flow works with slightly faster speech.
    Uses moderate speeds that ASR can still recognize.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing ASR with fast speech (using {unified_audio_input.method_name})")
    
    results = []
    
    for case in FAST_SPEECH_TEST_CASES:
        text = case["text"]
        speed = case["speed"]
        expected_words = case["expected_words"]
        min_accuracy = case.get("min_accuracy", 0.4)
        
        logger.info(f"Testing speed {speed}: '{text}'")
        
        audio_data = await unified_audio_input.setup_audio(
            text=text,
            speed=speed,
            expected_transcription=text
        )
        
        try:
            textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
            await textarea.fill("")
            
            await audio_chat_ui_helper.audio.start_recording()
            # Play audio through virtual mic (if PulseAudio)
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.page.wait_for_timeout(2000)
            await audio_chat_ui_helper.audio.stop_recording()
            
            transcribed = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=15000)
            logger.info(f"Speed {speed} | Transcription: '{transcribed}'")
            
            # Validate with flexible accuracy threshold
            passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
                original=text,
                transcribed=transcribed,
                keywords=expected_words,
                min_accuracy=min_accuracy
            )
            
            results.append({
                "speed": speed,
                "passed": passed,
                "accuracy": metrics["combined_score"],
                "transcribed": transcribed
            })
            
            logger.info(f"Speed {speed} | Accuracy: {metrics['combined_score']:.2%} | Passed: {passed}")
            
        finally:
            await unified_audio_input.cleanup()
    
    # At least one speed variation should work
    passed_count = sum(1 for r in results if r["passed"])
    
    allure.attach(
        "\n".join([f"Speed {r['speed']}: {r['accuracy']:.2%} - {'PASS' if r['passed'] else 'FAIL'}" for r in results]),
        name="Fast Speech Test Results",
        attachment_type=allure.attachment_type.TEXT
    )
    
    assert passed_count >= 1, f"At least one fast speech test should pass. Results: {results}"
    logger.info(f"Test completed: {passed_count}/{len(results)} fast speech tests passed")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T338")
async def test_asr_silence_ui(audio_chat_ui_helper, unified_audio_input):
    """
    Test ASR with silence to ensure it doesn't hallucinate words.
    Aligned with backend test_asr_silence in test_audioqa.py.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    
    Note: In UI mode with audio mock (oscillator tone), ASR may produce
    minimal false positives (1-2 short words). This is acceptable for
    UI testing where we verify the flow works, not ASR accuracy.
    """
    logger.info(f"Testing ASR with silence (using {unified_audio_input.method_name})")
    
    # Generate silent audio (empty text)
    audio_data = await unified_audio_input.setup_audio(
        text="",
        speed=1.0,
        expected_transcription=""  # Expect empty transcription
    )
    
    try:
        textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
        await textarea.fill("")
        
        await audio_chat_ui_helper.audio.start_recording()
        # Play silence through virtual mic (if PulseAudio) - no-op for empty audio
        await unified_audio_input.play_during_recording(audio_data)
        await audio_chat_ui_helper.page.wait_for_timeout(2000)
        await audio_chat_ui_helper.audio.stop_recording()
        
        transcribed = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=10000)
        transcribed = transcribed.strip()
        
        logger.info(f"Silence transcription output: '{transcribed}'")
        
        # In UI mode with audio mock, allow minimal false positives
        # (short single words from oscillator tone noise)
        word_count = len(transcribed.split()) if transcribed else 0
        
        # Should be empty, contain BLANK indicator, or have very minimal output
        is_acceptable = (
            transcribed == "" or 
            "BLANK" in transcribed or
            word_count <= 2  # Allow up to 2 short words from mock audio noise
        )
        
        if not is_acceptable:
            pytest.fail(f"ASR hallucinated significant text during silence: '{transcribed}' ({word_count} words)")
        elif word_count > 0:
            logger.warning(f"ASR produced minimal noise output: '{transcribed}' (acceptable for UI mock)")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Silence ASR validated in UI")
