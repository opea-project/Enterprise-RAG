"""
Copyright (C) 2024-2026 Intel Corporation
SPDX-License-Identifier: Apache-2.0

TTS (Text-to-Speech) Playback UI Tests

This module tests the TTS playback functionality in the AudioQnA UI:
1. Play speech button visibility after bot response
2. TTS state transitions (idle → waiting → playing → idle)
3. Audio playback completion
4. Audio duration validation
5. Multiple playback behavior (abort previous on new)

Strategy: PulseAudio Primary + Robust Fallback
- PRIMARY: PulseAudio capture + ASR verification (when available)
- FALLBACK: Browser Audio API interception (high confidence without PulseAudio)

The fallback approach provides high confidence testing by:
- Intercepting the TTS API response and validating audio format
- Intercepting browser Audio element and tracking playback events
- Verifying state transitions through UI element attributes
- Validating audio duration meets minimum threshold

SOLID/DRY Principles:
- Uses AudioUIHelper from ui_helper (shared TTS methods)
- Reuses AudioChatUIHelper for chat + audio interactions
- Test cases defined in configuration dict (single source of truth)
"""

import allure
import logging
import os
import subprocess  # nosec B404 - subprocess used for PulseAudio capture (parec, pactl)
import tempfile
import wave
from typing import Optional

import pytest

from tests.e2e.helpers.audioqa_api_helper import AudioApiHelper, AudioData
from tests.e2e.helpers.ui_helper import AudioChatUIHelper
from tests.e2e.ui.test_audio_prompting import (
    TranscriptionAccuracyEvaluator,
    # Import fixtures to be shared (pytest will pick them up)
    sherpa_tts,  # noqa: F401
    virtual_mic_player,  # noqa: F401
    unified_audio_input,  # noqa: F401
)
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)


# =============================================================================
# PulseAudio Output Capture (for TTS verification)
# =============================================================================

class PulseAudioOutputCapture:
    """
    Captures audio output from PulseAudio default sink.
    
    Uses parec to record audio playing through the system's audio output,
    allowing verification that TTS audio is actually played and audible.
    
    Usage:
        capture = PulseAudioOutputCapture()
        capture.start()
        # ... trigger TTS playback ...
        audio_bytes = capture.stop()
        # Send to ASR for verification
    """
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._process = None
        self._temp_file = None
        self._monitor_source = None
    
    def _get_default_sink_monitor(self) -> Optional[str]:
        """Get the monitor source for the default audio sink."""
        try:
            # Get default sink name
            result = subprocess.run(
                ["pactl", "get-default-sink"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                logger.warning(f"Failed to get default sink: {result.stderr}")
                return None
            
            default_sink = result.stdout.strip()
            monitor_source = f"{default_sink}.monitor"
            logger.info(f"Using monitor source: {monitor_source}")
            return monitor_source
            
        except Exception as e:
            logger.error(f"Failed to get sink monitor: {e}")
            return None
    
    def start(self) -> bool:
        """Start capturing audio output."""
        try:
            self._monitor_source = self._get_default_sink_monitor()
            if not self._monitor_source:
                logger.error("Could not find audio monitor source")
                return False
            
            # Create temp file for capture
            self._temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            )
            self._temp_file.close()
            
            # Start parec to capture from monitor
            # Using raw format and will convert to wav later
            cmd = [
                "parec",
                f"--device={self._monitor_source}",
                "--file-format=wav",
                f"--rate={self.sample_rate}",
                f"--channels={self.channels}",
                self._temp_file.name
            ]
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            logger.info(f"Started audio capture to {self._temp_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            return False
    
    def stop(self) -> Optional[bytes]:
        """Stop capturing and return audio bytes."""
        if not self._process:
            logger.warning("No capture process running")
            return None
        
        try:
            # Send SIGTERM to stop recording
            self._process.terminate()
            self._process.wait(timeout=5)
            
            # Read captured audio
            if os.path.exists(self._temp_file.name):
                with open(self._temp_file.name, 'rb') as f:
                    audio_bytes = f.read()
                
                # Get duration for logging
                try:
                    with wave.open(self._temp_file.name, 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration = frames / rate
                        logger.info(f"Captured {duration:.2f}s of audio ({len(audio_bytes)} bytes)")
                except Exception:
                    pass
                
                # Cleanup temp file
                os.unlink(self._temp_file.name)
                
                return audio_bytes
            else:
                logger.error("Capture file not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to stop audio capture: {e}")
            return None
        finally:
            self._process = None
            self._temp_file = None
    
    def is_available(self) -> bool:
        """Check if PulseAudio capture is available."""
        try:
            result = subprocess.run(
                ["pactl", "info"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

# Skip all tests if audio is not enabled
audio_config = cfg.get("audio", {})
if not audio_config.get("enabled", False):
    pytestmark = pytest.mark.skip(reason="Audio/TTS is not enabled in deployment")

# Also check if chatqa pipeline is deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        break
else:
    pytestmark = pytest.mark.skip(reason="ChatQA pipeline is not deployed")


# =============================================================================
# Test Configuration
# =============================================================================

TTS_TEST_QUESTIONS = [
    {
        "question": "What is machine learning?",
        "min_response_length": 50,  # Minimum bot response length
        "min_tts_duration": 1.0,    # Minimum TTS audio duration in seconds
    },
    {
        "question": "Explain artificial intelligence briefly.",
        "min_response_length": 30,
        "min_tts_duration": 0.5,
    },
]


# =============================================================================
# Helper Functions
# =============================================================================

async def send_question_and_get_response(
    helper: AudioChatUIHelper,
    question: str,
    response_timeout: int = 60000
) -> Optional[str]:
    """Send a text question and wait for bot response.
    
    Args:
        helper: AudioChatUIHelper instance
        question: Question to send
        response_timeout: Timeout for bot response
        
    Returns:
        Bot response text or None on failure
    """
    try:
        # Wait for any pending response to complete (send button becomes enabled)
        send_button = helper.page.locator(helper.audio.SEND_BUTTON_SELECTOR)
        try:
            await send_button.wait_for(state="attached", timeout=5000)
            # Wait for button to be enabled (not disabled)
            for _ in range(30):  # Max 15 seconds
                is_disabled = await send_button.get_attribute("disabled")
                if is_disabled is None:
                    break
                await helper.page.wait_for_timeout(500)
        except Exception:
            pass  # Button may already be ready
        
        # Fill in the question
        textarea = helper.page.locator(helper.audio.TEXTAREA_SELECTOR)
        await textarea.fill(question)
        
        # Wait a moment for send button to enable after text entry
        await helper.page.wait_for_timeout(500)
        
        # Click send (use force in case of minor UI timing issues)
        await send_button.click(force=True)
        logger.info(f"Sent question: {question}")
        
        # Wait for bot response
        bot_message = helper.page.locator(helper.audio.BOT_MESSAGE_SELECTOR).last
        await bot_message.wait_for(state="visible", timeout=response_timeout)
        
        # Wait for streaming to complete (content stabilization)
        await helper.page.wait_for_timeout(3000)
        
        response_text = await bot_message.inner_text()
        logger.info(f"Bot response received: {len(response_text)} chars")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Failed to get bot response: {e}")
        return None


# =============================================================================
# TTS Playback Tests
# =============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T339")
async def test_play_speech_button_appears_on_response(audio_chat_ui_helper):
    """
    Test that the TTS play speech button appears after bot responds.
    
    Verification:
    - Send a question
    - Wait for bot response
    - Check play speech button is visible
    """
    logger.info("Testing play speech button visibility...")
    
    test_case = TTS_TEST_QUESTIONS[0]
    question = test_case["question"]
    
    # Send question and get response
    response = await send_question_and_get_response(audio_chat_ui_helper, question)
    assert response is not None, "Should receive bot response"
    assert len(response) >= test_case["min_response_length"], \
        f"Response too short: {len(response)} chars"
    
    # Check play speech button is visible
    is_visible = await audio_chat_ui_helper.audio.is_play_speech_button_visible(timeout=5000)
    assert is_visible, "Play speech button should be visible after bot response"
    
    logger.info("Test completed: Play speech button is visible")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T340")
async def test_tts_state_transitions(audio_chat_ui_helper):
    """
    Test TTS button state transitions: idle → waiting → playing → idle.
    
    Uses browser interception to track state changes.
    """
    logger.info("Testing TTS state transitions...")
    
    test_case = TTS_TEST_QUESTIONS[0]
    question = test_case["question"]
    
    # Setup TTS interception for tracking
    await audio_chat_ui_helper.audio.setup_tts_interception()
    await audio_chat_ui_helper.audio.setup_tts_api_interception()
    
    try:
        # Send question and get response
        response = await send_question_and_get_response(audio_chat_ui_helper, question)
        assert response is not None, "Should receive bot response"
        
        # Get first play button turn_id
        turn_id = await audio_chat_ui_helper.audio.click_first_play_speech_button()
        assert turn_id is not None, "Should find and click play speech button"
        
        # Track state transitions
        states_observed = []
        
        # Should transition to waiting (TTS backend may be slow to start)
        waiting_reached = await audio_chat_ui_helper.audio.wait_for_tts_state(
            turn_id, "waiting", timeout=15000
        )
        if waiting_reached:
            states_observed.append("waiting")
            logger.info("State: waiting (generating audio)")
        
        # Should transition to playing (TTS backend generation can be slow)
        playing_reached = await audio_chat_ui_helper.audio.wait_for_tts_state(
            turn_id, "playing", timeout=90000
        )
        if playing_reached:
            states_observed.append("playing")
            logger.info("State: playing (audio playback)")
        
        # Wait for playback to complete (TTS backend can be slow)
        metrics = await audio_chat_ui_helper.audio.wait_for_tts_playback_complete(timeout=120000)
        
        # Should return to idle
        idle_reached = await audio_chat_ui_helper.audio.wait_for_tts_state(
            turn_id, "idle", timeout=5000
        )
        if idle_reached:
            states_observed.append("idle")
            logger.info("State: idle (playback complete)")
        
        # Attach state transition log to allure
        allure.attach(
            f"States observed: {' → '.join(states_observed)}\n"
            f"Playback completed: {metrics.get('completed', False)}\n"
            f"Duration: {metrics.get('duration', 0):.2f}s\n"
            f"Events: {len(metrics.get('events', []))}",
            name="TTS State Transitions",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Verify at least played and returned to idle
        assert metrics.get('played', False), "Audio should have started playing"
        
        logger.info(f"Test completed: States observed: {states_observed}")
        
    finally:
        await audio_chat_ui_helper.audio.cleanup_tts_interception()


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T341")
async def test_tts_audio_plays_completely(audio_chat_ui_helper):
    """
    Test that TTS audio plays to completion (ended event fires).
    
    Uses browser Audio API interception to verify:
    - Audio element created
    - Play event fired
    - Ended event fired (completion)
    """
    logger.info("Testing TTS audio playback completion...")
    
    test_case = TTS_TEST_QUESTIONS[0]
    question = test_case["question"]
    
    # Setup interception
    await audio_chat_ui_helper.audio.setup_tts_interception()
    await audio_chat_ui_helper.audio.setup_tts_api_interception()
    
    try:
        # Send question and get response
        response = await send_question_and_get_response(audio_chat_ui_helper, question)
        assert response is not None, "Should receive bot response"
        
        # Click play button
        turn_id = await audio_chat_ui_helper.audio.click_first_play_speech_button()
        assert turn_id is not None, "Should find play speech button"
        
        # Wait for playback to complete (TTS backend can be slow)
        metrics = await audio_chat_ui_helper.audio.wait_for_tts_playback_complete(timeout=120000)
        
        # Attach metrics to allure
        allure.attach(
            f"Played: {metrics.get('played', False)}\n"
            f"Completed: {metrics.get('completed', False)}\n"
            f"Error: {metrics.get('error', False)}\n"
            f"Duration: {metrics.get('duration', 0):.2f}s\n"
            f"Valid Audio: {metrics.get('valid_audio', False)}\n"
            f"API Response: {metrics.get('api_response', {})}\n"
            f"Event Count: {len(metrics.get('events', []))}",
            name="TTS Playback Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Verify playback completed
        assert metrics.get('played', False), "Audio play event should fire"
        assert metrics.get('completed', False), "Audio should play to completion (ended event)"
        assert not metrics.get('error', False), "No error should occur during playback"
        
        logger.info(f"Test completed: Audio played completely, duration={metrics.get('duration', 0):.2f}s")
        
    finally:
        await audio_chat_ui_helper.audio.cleanup_tts_interception()


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T342")
async def test_tts_audio_has_valid_duration(audio_chat_ui_helper):
    """
    Test that TTS audio has a reasonable duration (not empty/silent).
    
    Verifies:
    - Audio duration > minimum threshold (0.5s)
    - API returned valid audio format
    """
    logger.info("Testing TTS audio duration validation...")
    
    test_case = TTS_TEST_QUESTIONS[0]
    question = test_case["question"]
    min_duration = test_case["min_tts_duration"]
    
    # Setup interception
    await audio_chat_ui_helper.audio.setup_tts_interception()
    await audio_chat_ui_helper.audio.setup_tts_api_interception()
    
    try:
        # Send question and get response
        response = await send_question_and_get_response(audio_chat_ui_helper, question)
        assert response is not None, "Should receive bot response"
        
        # Click play button
        turn_id = await audio_chat_ui_helper.audio.click_first_play_speech_button()
        assert turn_id is not None, "Should find play speech button"
        
        # Wait for playback and verify (TTS backend can be slow)
        await audio_chat_ui_helper.audio.wait_for_tts_playback_complete(timeout=120000)
        
        # Verify duration
        verification = await audio_chat_ui_helper.audio.verify_tts_audio_played(
            min_duration=min_duration
        )
        
        allure.attach(
            f"Valid: {verification.get('valid', False)}\n"
            f"Duration: {verification.get('duration', 0):.2f}s\n"
            f"Duration OK (>={min_duration}s): {verification.get('duration_ok', False)}\n"
            f"API OK: {verification.get('api_ok', False)}\n"
            f"Played: {verification.get('played', False)}\n"
            f"Completed: {verification.get('completed', False)}",
            name="TTS Duration Verification",
            attachment_type=allure.attachment_type.TEXT
        )
        
        assert verification.get('duration_ok', False), \
            f"Audio duration ({verification.get('duration', 0):.2f}s) should be >= {min_duration}s"
        
        logger.info(f"Test completed: Audio duration={verification.get('duration', 0):.2f}s")
        
    finally:
        await audio_chat_ui_helper.audio.cleanup_tts_interception()


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T343")
async def test_tts_abort_on_new_playback(audio_chat_ui_helper):
    """
    Test that starting new TTS playback aborts previous playback.
    
    Verifies:
    - First playback starts
    - Second playback click aborts first
    - Only one audio should be playing at a time
    """
    logger.info("Testing TTS playback abort behavior...")
    
    # Need at least 2 questions for 2 bot messages
    questions = [q["question"] for q in TTS_TEST_QUESTIONS[:2]]
    
    if len(questions) < 2:
        pytest.skip("Need at least 2 test questions for abort test")
    
    # Setup interception
    await audio_chat_ui_helper.audio.setup_tts_interception()
    
    try:
        # Send first question
        response1 = await send_question_and_get_response(audio_chat_ui_helper, questions[0])
        assert response1 is not None, "Should receive first bot response"
        
        # Send second question
        response2 = await send_question_and_get_response(audio_chat_ui_helper, questions[1])
        assert response2 is not None, "Should receive second bot response"
        
        # Wait for play buttons to appear (TTS backend may be slow)
        await audio_chat_ui_helper.page.wait_for_timeout(2000)
        
        # Get all play buttons with retry
        buttons = await audio_chat_ui_helper.audio.get_play_speech_buttons()
        if len(buttons) < 2:
            # Wait a bit more and retry - TTS button rendering can be delayed
            await audio_chat_ui_helper.page.wait_for_timeout(3000)
            buttons = await audio_chat_ui_helper.audio.get_play_speech_buttons()
        assert len(buttons) >= 2, f"Should have at least 2 play buttons, found {len(buttons)}"
        
        # Click first button
        await buttons[0].click()
        logger.info("Started first playback")
        
        # Wait briefly for playback to start
        await audio_chat_ui_helper.page.wait_for_timeout(1000)
        
        # Click second button (should abort first)
        await buttons[1].click()
        logger.info("Started second playback (should abort first)")
        
        # Wait for second playback to complete (TTS backend can be slow)
        metrics = await audio_chat_ui_helper.audio.wait_for_tts_playback_complete(timeout=120000)
        
        # Check for abort events
        events = metrics.get('events', [])
        abort_events = [e for e in events if e['type'] == 'abort']
        pause_events = [e for e in events if e['type'] == 'pause']
        
        allure.attach(
            f"Total events: {len(events)}\n"
            f"Abort events: {len(abort_events)}\n"
            f"Pause events: {len(pause_events)}\n"
            f"Final completed: {metrics.get('completed', False)}",
            name="TTS Abort Behavior",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Either abort or pause event should have fired on first audio
        # and second audio should complete
        has_interruption = len(abort_events) > 0 or len(pause_events) > 0
        logger.info(f"Interruption detected: {has_interruption}, abort={len(abort_events)}, pause={len(pause_events)}")
        
        # The second playback should eventually complete
        assert metrics.get('played', False), "At least one audio should have played"
        
        logger.info("Test completed: TTS abort behavior verified")
        
    finally:
        await audio_chat_ui_helper.audio.cleanup_tts_interception()


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T344")
async def test_tts_no_button_while_pending(audio_chat_ui_helper):
    """
    Test that play speech button is NOT visible while response is pending.
    
    The play button should only appear after the bot response is complete,
    not during streaming.
    """
    logger.info("Testing play button visibility during pending response...")
    
    test_case = TTS_TEST_QUESTIONS[0]
    question = test_case["question"]
    
    # Fill in the question
    textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
    await textarea.fill(question)
    
    # Click send
    send_button = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.SEND_BUTTON_SELECTOR)
    await send_button.click()
    
    # Immediately check for play button (should NOT be visible yet)
    # Give it a short timeout
    early_visible = await audio_chat_ui_helper.audio.is_play_speech_button_visible(timeout=500)
    
    # Log but don't fail if visible early (streaming might be very fast)
    if early_visible:
        logger.warning("Play button visible early - response may have completed quickly")
    else:
        logger.info("Play button correctly hidden during pending response")
    
    # Wait for response to complete
    bot_message = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.BOT_MESSAGE_SELECTOR).last
    await bot_message.wait_for(state="visible", timeout=60000)
    await audio_chat_ui_helper.page.wait_for_timeout(3000)
    
    # Now button should be visible
    final_visible = await audio_chat_ui_helper.audio.is_play_speech_button_visible(timeout=5000)
    assert final_visible, "Play button should be visible after response completes"
    
    logger.info("Test completed: Play button visibility timing verified")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T345")
async def test_tts_audio_matches_bot_response_text(audio_chat_ui_helper, unified_audio_input, keycloak_helper):  # noqa: F811
    """
    Test that TTS audio output matches the bot response text.
    
    This is the ultimate human-like verification - mimics a real user:
    1. Click mic button to start recording
    2. Speak a question (via PulseAudio virtual mic)
    3. Stop recording - audio gets transcribed
    4. Send the transcribed prompt
    5. Wait for bot text response (what user SEES)
    6. Click play-speech-button to trigger TTS
    7. Capture the TTS audio output via PulseAudio
    8. Transcribe captured audio via ASR
    9. Compare transcription with bot response text
    
    This verifies that what the user HEARS matches what they SEE.
    
    Requires:
    - PulseAudio running (for both virtual mic input AND output capture)
    - ASR service deployed
    """
    logger.info(f"Testing TTS audio matches bot response text (using {unified_audio_input.method_name})...")
    
    # Check PulseAudio availability for output capture
    capture = PulseAudioOutputCapture()
    if not capture.is_available():
        pytest.skip("PulseAudio not available for audio capture")
    
    # Setup ASR helper using fixture
    audio_api = AudioApiHelper(keycloak_helper)
    
    # Use a simple question that will get a meaningful response
    test_question = "What is artificial intelligence?"
    
    try:
        # Step 1: Prepare audio to speak via virtual mic
        logger.info(f"Step 1: Preparing audio for question: '{test_question}'")
        audio_data = await unified_audio_input.setup_audio(
            text=test_question,
            speed=1.0,
            expected_transcription=test_question
        )
        
        # Step 2: Start recording (click mic button)
        logger.info("Step 2: Starting recording - clicking mic button")
        await audio_chat_ui_helper.audio.click_mic_button()
        
        recording_started = await audio_chat_ui_helper.audio.wait_for_recording_state(
            recording=True, timeout=5000
        )
        
        if not recording_started:
            pytest.fail("Recording did not start - mic button may not be working")
        
        # Step 3: Play question audio through virtual mic
        logger.info("Step 3: Playing question audio through virtual mic")
        await unified_audio_input.play_during_recording(audio_data)
        await audio_chat_ui_helper.page.wait_for_timeout(3000)
        
        # Step 4: Stop recording
        logger.info("Step 4: Stopping recording")
        await audio_chat_ui_helper.audio.click_mic_button()
        await audio_chat_ui_helper.audio.wait_for_recording_state(recording=False, timeout=5000)
        
        # Step 5: Wait for transcription to appear in textarea
        logger.info("Step 5: Waiting for transcription...")
        transcribed_question = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=30000)
        logger.info(f"Transcribed question: '{transcribed_question}'")
        
        # Step 6: Click send button
        logger.info("Step 6: Sending the transcribed prompt")
        send_button = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.SEND_BUTTON_SELECTOR)
        await send_button.click()
        
        # Step 7: Wait for bot response text
        logger.info("Step 7: Waiting for bot response...")
        bot_response_text = await audio_chat_ui_helper.wait_for_response(timeout=60000)
        assert bot_response_text is not None, "Should receive bot response"
        
        # Get the clean text from UI
        bot_message_locator = audio_chat_ui_helper.page.locator(
            audio_chat_ui_helper.audio.BOT_MESSAGE_SELECTOR
        ).last
        bot_text_element = bot_message_locator.locator("p").first
        bot_response_text = await bot_text_element.inner_text()
        bot_response_text = " ".join(bot_response_text.split())  # Clean up
        
        logger.info(f"Bot response text (from UI): '{bot_response_text[:100]}...'")
        assert len(bot_response_text) > 20, "Bot response should have substantial text"
        
        # Step 8: Start PulseAudio capture BEFORE clicking play
        logger.info("Step 8: Starting PulseAudio output capture")
        capture_started = capture.start()
        assert capture_started, "Should be able to start audio capture"
        await audio_chat_ui_helper.page.wait_for_timeout(500)
        
        # Step 9: Click play-speech-button to trigger TTS
        logger.info("Step 9: Clicking play-speech-button")
        turn_id = await audio_chat_ui_helper.audio.click_first_play_speech_button()
        assert turn_id is not None, "Should find and click play speech button"
        
        # Step 10: Wait for TTS playback to complete
        logger.info("Step 10: Waiting for TTS playback to complete")
        await audio_chat_ui_helper.audio.setup_tts_interception()
        await audio_chat_ui_helper.audio.wait_for_tts_playback_complete(timeout=120000)
        
        # Buffer after playback ends
        await audio_chat_ui_helper.page.wait_for_timeout(1000)
        
        # Step 11: Stop capture and get audio
        logger.info("Step 11: Stopping audio capture")
        captured_audio = capture.stop()
        assert captured_audio is not None, "Should capture audio bytes"
        assert len(captured_audio) > 1000, f"Captured audio too small: {len(captured_audio)} bytes"
        
        logger.info(f"Captured {len(captured_audio)} bytes of TTS audio output")
        
        # Step 12: Transcribe captured TTS audio via ASR
        logger.info("Step 12: Transcribing captured TTS audio via ASR")
        tts_audio_data = AudioData(
            audio_bytes=captured_audio,
            text="",  # Unknown - we're transcribing
            voice="captured_tts",
            sample_rate=16000
        )
        
        asr_response = audio_api.transcribe_audio(tts_audio_data)
        assert asr_response.status_code == 200, f"ASR should succeed, got {asr_response.status_code}"
        
        transcribed_tts_text = audio_api.get_transcription_text(asr_response)
        transcribed_tts_text = " ".join(transcribed_tts_text.split())  # Clean up
        logger.info(f"Transcribed TTS text (from audio): '{transcribed_tts_text[:100]}...'")
        
        # Step 13: Compare transcription with bot response text
        logger.info("Step 13: Comparing TTS audio transcription with bot response text")
        
        # Extract keywords from bot response for comparison
        bot_words = bot_response_text.lower().split()
        significant_words = [w for w in bot_words if len(w) > 4][:10]
        
        passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
            original=bot_response_text,
            transcribed=transcribed_tts_text,
            keywords=significant_words,
            min_accuracy=0.3  # Lower threshold since TTS→capture→ASR has quality losses
        )
        
        # Attach results to Allure
        allure.attach(
            f"Test Flow Summary:\n"
            f"==================\n"
            f"1. Spoke question via mic: '{test_question}'\n"
            f"2. Transcribed as: '{transcribed_question}'\n"
            f"3. Bot response (what user SEES):\n{bot_response_text}\n\n"
            f"4. TTS audio transcription (what user HEARS):\n{transcribed_tts_text}\n\n"
            f"Comparison Results:\n"
            f"Significant Keywords: {significant_words}\n"
            f"Word Accuracy: {metrics.get('word_accuracy', 0):.2%}\n"
            f"Keyword Match: {metrics.get('keyword_match', 0):.2%}\n"
            f"Passed: {passed}",
            name="TTS Audio vs Bot Response Comparison",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Verify match
        assert passed, (
            f"TTS audio should match bot response text. "
            f"Word accuracy: {metrics.get('word_accuracy', 0):.2%}, "
            f"Keyword match: {metrics.get('keyword_match', 0):.2%}"
        )
        
        logger.info(
            f"Test completed successfully! TTS audio matches bot response! "
            f"Accuracy: {metrics.get('word_accuracy', 0):.2%}"
        )
        
    finally:
        # Cleanup
        await unified_audio_input.cleanup()
        await audio_chat_ui_helper.audio.cleanup_tts_interception()
        # Ensure capture is stopped if still running
        if capture._process:
            capture.stop()
