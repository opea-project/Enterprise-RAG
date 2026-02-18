#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import concurrent.futures
import logging
import pytest
import statistics
from tests.e2e.validation.buildcfg import cfg
from tests.e2e.helpers.audioqa_api_helper import AudioApiHelper

# Skip all tests if audio is not deployed
if not cfg.get("audio", {}).get("enabled", False):
    pytestmark = pytest.mark.skip(reason="AudioQnA/ASR pipeline is not deployed")

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def audioqa_api_helper(keycloak_helper):
    """AudioQnA API helper for testing transcription API"""
    return AudioApiHelper(keycloak_helper)


@pytest.mark.smoke
@allure.testcase("IEASG-T321")
def test_asr_basic(audioqa_api_helper):
    """Basic test case for ASR functionality."""
    audio = audioqa_api_helper.generate_audio("Hello, this is a test audio.")
    response = audioqa_api_helper.transcribe_audio(audio)
    assert response.status_code == 200, f"Audio transcription failed: {response.text}"
    transcription = audioqa_api_helper.get_transcription_text(response)
    logger.debug(f"Transcription: {transcription}")
    assert_all_words_in_transcription(["hello", "this", "is", "test", "audio"], transcription)


@allure.testcase("IEASG-T323")
def test_asr_slow_speech(audioqa_api_helper):
    """Test ASR with slow speech audio at various speeds."""
    test_cases = [
        {
            "speed": 0.9,
            "expected_words": ["astronomy", "scientific", "telescope", "distant"],
            "text": "Astronomy is a scientific study of stars, planets, and distant galaxies using a telescope."
        }, {
            "speed": 0.85,
            "expected_words": ["artificial", "intelligence", "machine", "learning", "future"],
            "text": "Artificial intelligence and machine learning are changing the future of technology."
        }, {
            "speed": 0.8,
            "expected_words": ["morning", "coffee", "breakfast", "pancakes", "syrup"],
            "text": "Every morning I enjoy a hot cup of coffee with breakfast, especially pancakes and syrup."
        }, {
            "speed": 0.75,
            "expected_words": ["atmosphere", "protection", "radiation", "sun"],
            "text": "The earth's atmosphere provides essential protection from the harmful radiation of the sun."
        }, {
            "speed": 0.7,
            "expected_words": ["extraordinary", "circumstances", "require", "solutions"],
            "text": "Extraordinary circumstances usually require very creative and innovative solutions."
        }
    ]
    _run_speed_test_cases(audioqa_api_helper, test_cases)


@allure.testcase("IEASG-T322")
def test_asr_fast_speech(audioqa_api_helper):
    """Test ASR with fast speech audio at various speeds."""
    test_cases = [
        {
            "speed": 1.3,
            "expected_words": ["quick", "brown", "fox", "jumps", "london", "unpredictable"],
            "text": "The quick brown fox jumps over the lazy dog, "
                    "while the weather in London remains quite unpredictable."
        }, {
            "speed": 1.4,
            "expected_words": ["going", "realize", "forgotten", "your", "keys", "car"],
            "text": "What are you going to do when you realize that you've "
                    "forgotten your keys in the car?"
        }, {
            "speed": 1.5,
            "expected_words": ["there", "minute", "traffic", "bad", "news"],
            "text": "I'll be there in a minute if the traffic isn't as bad "
                    "as they said on the news."
        }, {
            "speed": 1.6,
            "expected_words": ["quick", "brown", "fox", "jumps", "london", "unpredictable"],
            "text": "The quick brown fox jumps over the lazy dog, "
                    "while the weather in London remains quite unpredictable."},
    ]
    _run_speed_test_cases(audioqa_api_helper, test_cases)


@allure.testcase("IEASG-T324")
def test_asr_complete_silence(audioqa_api_helper):
    """
    Test ASR with silence to ensure it doesn't hallucinate words.
    Generate silent audio and verify that the transcription is either empty or indicates silence.
    """
    audio = audioqa_api_helper.generate_audio("")
    response = audioqa_api_helper.transcribe_audio(audio)
    assert response.status_code == 200, f"Audio transcription failed: {response.text}"
    transcription = audioqa_api_helper.get_transcription_text(response).strip()
    logger.debug(f"Silence transcription output: '{transcription}'")
    assert transcription == "" or "BLANK" in transcription, f"ASR hallucinated text during silence: '{transcription}'"


@allure.testcase("IEASG-T348")
def test_asr_long_pause_between_words(audioqa_api_helper):
    """
    Use an existing mp3 file that contains a pause (silence) between words to test ASR's handling of silence.
    Verify that the transcription contains the text that is after the long pause.
    """
    audio = audioqa_api_helper.load_audio_from_file("test_asr_long_pause_between_words.mp3")
    response = audioqa_api_helper.transcribe_audio(audio)
    assert response.status_code == 200, f"Audio transcription failed: {response.text}"
    transcription = audioqa_api_helper.get_transcription_text(response).strip()
    logger.debug(f"Transcription output: '{transcription}'")
    text_from_audio = ("While many people spend their time debating completely trivial and irrelevant matters "
                  "that have no actual impact on reality it remains quite fascinating how such pointless "
                  "conversations can somehow stretch on for hours without ever reaching a single meaningful "
                  "conclusion")
    assert_all_words_in_transcription(text_from_audio.lower().split(), transcription)


@allure.testcase("IEASG-T325")
def test_asr_payload_limit_stress(audioqa_api_helper):
    """
    Stress test ASR API by increasing word counts in a loop to find the breaking point.
    This test generates audio files with increasing word counts and sends them to the ASR API.
    """
    limit_steps = [100, 400, 700, 1000]

    for word_count in limit_steps:
        text = audioqa_api_helper.generate_real_words(word_count)

        logger.info(f"Generating audio for {word_count} real words...")
        audio = audioqa_api_helper.generate_audio(text, speed=1.0)

        file_size_mb = len(audio.audio_bytes) / (1024 * 1024)
        logger.info(f"Payload size for {word_count} words: {file_size_mb:.2f} MB")

        response = audioqa_api_helper.transcribe_audio(audio)
        assert response.status_code == 200, (
            f"API failed at {word_count} words. "
            f"Size: {file_size_mb:.2f} MB, Status: {response.status_code}, Error: {response.text}"
        )

        transcription = audioqa_api_helper.get_transcription_text(response)
        assert len(transcription.split()) > 0, f"ASR returned empty result for {word_count} words"


@pytest.mark.smoke
@allure.testcase("IEASG-T326")
def test_asr_upload_wav(audioqa_api_helper, edp_helper, chatqa_api_helper):
    """Check whether user can upload *.wav audio. Ask a question related to audio content and verify the answer"""
    audio_text = "There are 2568 words in a book called 'My puppet and I' by author John Doe"
    question = "How many words are in the book 'My puppet and I' by John Doe?"
    audio_data = audioqa_api_helper.generate_audio(audio_text)
    edp_helper.upload_file_and_wait_for_ingestion(audio_data.filepath)
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}")
    assert chatqa_api_helper.words_in_response(["2568", "2,568"], response_text)


@allure.testcase("IEASG-T327")
def test_asr_upload_mp3(audioqa_api_helper, edp_helper, chatqa_api_helper):
    """Check whether user can upload *.mp3 audio. Ask a question related to audio content and verify the answer"""
    audio_text = "There are 11689 words in a book called 'Wooden Dreams' by author Anna Black"
    question = "How many words are in the book 'Wooden Dreams' by Anna Black?"
    audio_data = audioqa_api_helper.generate_audio(audio_text, format="mp3")
    edp_helper.upload_file_and_wait_for_ingestion(audio_data.filepath)
    response = chatqa_api_helper.call_chatqa(question)
    response_text = chatqa_api_helper.get_text(response)
    logger.info(f"ChatQA response: {response_text}")
    assert chatqa_api_helper.words_in_response(["11689", "11,689"], response_text)


@allure.testcase("IEASG-T352")
def test_asr_as_user(audioqa_api_helper, temporarily_remove_regular_user_required_actions):
    """Test ASR API call with user authentication to ensure that it works for authenticated users"""
    input_text = "Check whether user can access automatic speech recognition API"
    expected_words = ["check", "whether", "user", "access", "automatic", "speech", "recognition"]

    # Generate audio from text
    audio_data = audioqa_api_helper.generate_audio(input_text)

    # Call ASR API as a regular user
    logger.info("Testing ASR API as user")
    response = audioqa_api_helper.transcribe_audio(audio_data, as_user=True)
    assert response.status_code == 200, f"ASR API call as user failed: {response.text}"

    # Verify transcription
    transcription = audioqa_api_helper.get_transcription_text(response).strip()
    logger.info(f"Original text: '{input_text}' | Transcribed text: '{transcription}'")

    assert_all_words_in_transcription(expected_words, transcription)


@allure.testcase("IEASG-T354")
def test_asr_concurrent_requests(audioqa_api_helper, temporarily_remove_brute_force_detection):
    """
    Make concurrent ASR API requests. Measure min, max, avg response time.
    Check if all requests were processed successfully.
    """
    concurrent_requests = 30
    input_text = "This is a test for concurrent automatic speech recognition requests"

    # Pre-generate audio once to reuse for all requests
    audio_data = audioqa_api_helper.generate_audio(input_text)
    logger.info(f"Generated audio of size {len(audio_data.audio_bytes) / 1024:.2f} KB for concurrent ASR testing")

    def call_asr_single(audio):
        """Helper function to call ASR API and return response with timing"""
        try:
            response = audioqa_api_helper.transcribe_audio(audio)
            return response
        except Exception as e:
            logger.error(f"ASR request failed with exception: {e}")
            return None

    _run_concurrent_api_test(
        concurrent_requests=concurrent_requests,
        api_call_func=lambda: call_asr_single(audio_data),
        test_name="ASR"
    )


@allure.testcase("IEASG-T346")
def test_tts_basic(audioqa_api_helper):
    """
    Test text-to-speech API by converting text to audio and then back to text using ASR.
    Verify that the transcribed text matches the original input.
    """
    input_text = "How are you"
    expected_words = input_text.lower().split()

    audio_data = audioqa_api_helper.text_to_speech_audio(input_text, "test_tts_basic.mp3")
    transcription = audioqa_api_helper.transcribe_to_text(audio_data, original_text=input_text)
    assert_all_words_in_transcription(expected_words, transcription)


@allure.testcase("IEASG-T349")
def test_tts_empty_text(audioqa_api_helper):
    """Test TTS API with empty text input. Verify that the API handles it gracefully"""

    input_text = "                  "
    response = audioqa_api_helper.text_to_speech(input_text)
    assert response.status_code == 200, f"TTS API call failed for empty text: {response.text}"

    input_text = ""
    response = audioqa_api_helper.text_to_speech(input_text)
    assert response.status_code == 200, f"TTS API call failed for empty text: {response.text}"

    input_text = "\t\n\r"
    response = audioqa_api_helper.text_to_speech(input_text)
    assert response.status_code == 200, f"TTS API call failed for empty text: {response.text}"


@allure.testcase("IEASG-T350")
def test_tts_overload(audioqa_api_helper):
    """
    Test TTS API with a very long text input to check if it can handle large payloads without crashing.
    """
    text = audioqa_api_helper.generate_real_words(5000)
    logger.info(f"Testing TTS with very long input text of {len(text)} characters")
    tts_response = audioqa_api_helper.text_to_speech(text)
    assert tts_response.status_code != 500, f"TTS API call failed: {tts_response.text}"


@allure.testcase("IEASG-T351")
def test_tts_as_user(audioqa_api_helper, temporarily_remove_regular_user_required_actions):
    """Test TTS API call with user authentication to ensure that it works for authenticated users"""
    input_text = "Check whether user can access text-to-speech API"
    expected_words = ["check", "whether", "user", "speech"]

    audio_data = audioqa_api_helper.text_to_speech_audio(input_text, "test_tts_as_user.mp3", as_user=True)
    transcription = audioqa_api_helper.transcribe_to_text(audio_data, original_text=input_text)
    assert_all_words_in_transcription(expected_words, transcription)


@allure.testcase("IEASG-T353")
def test_tts_concurrent_requests(audioqa_api_helper, temporarily_remove_brute_force_detection):
    """
    Make concurrent TTS API requests. Measure min, max, avg response time.
    Check if all requests were processed successfully.
    """
    concurrent_requests = 30
    input_text = "This is a test for concurrent text to speech requests"

    def call_tts_single(text):
        """Helper function to call TTS API and return response with timing"""
        try:
            response = audioqa_api_helper.text_to_speech(text)
            return response
        except Exception as e:
            logger.error(f"TTS request failed with exception: {e}")
            return None

    _run_concurrent_api_test(
        concurrent_requests=concurrent_requests,
        api_call_func=lambda: call_tts_single(input_text),
        test_name="TTS"
    )


@allure.testcase("IEASG-T355")
def test_asr_all_voice_models(audioqa_api_helper):
    """
    Test ASR transcription accuracy across all available Sherpa TTS voice models.
    Generate audio using each voice model and verify that transcription matches the original text.
    """
    input_text = ("All the systems are running well today and the blue sky is very clear "
                  "while testing different voices")
    expected_words = ["systems", "running", "well", "today", "blue", "sky", "clear", "testing", "different", "voices"]

    voice_models = ["en_male_joe", "en_female", "en_male_kusal", "en_male_bryce"]

    for voice_key in voice_models:
        logger.info(f"Testing voice model: {voice_key}")

        # Generate audio with this voice
        audio_data = audioqa_api_helper.generate_audio(input_text, voice_key=voice_key, format="wav")

        # Transcribe the audio
        response = audioqa_api_helper.transcribe_audio(audio_data)
        assert response.status_code == 200, f"ASR failed for voice {voice_key}: {response.text}"

        transcription = audioqa_api_helper.get_transcription_text(response).strip()
        logger.info(f"Voice: {voice_key} | Original: '{input_text}' | Transcribed: '{transcription}'")

        # Verify transcription contains expected words
        assert_all_words_in_transcription(expected_words, transcription)


def _run_concurrent_api_test(concurrent_requests, api_call_func, test_name):
    """
    Common helper for running concurrent API tests.

    Args:
        concurrent_requests: Number of concurrent requests to make
        api_call_func: Callable that makes the API call and returns ApiResponse
        test_name: Name of the test for logging purposes
    """
    execution_times = []
    failed_requests_counter = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [executor.submit(api_call_func) for _ in range(concurrent_requests)]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is None:
                failed_requests_counter += 1
            elif result.status_code != 200:
                logger.info(f"{test_name} request failed with status code {result.status_code}. Response: {result.text}")
                failed_requests_counter += 1
            else:
                execution_times.append(result.response_time)

    mean_time = statistics.mean(execution_times)
    max_time = max(execution_times)
    min_time = min(execution_times)

    logger.info(f'Total requests: {concurrent_requests}')
    logger.info(f'Failed requests: {failed_requests_counter}')
    logger.info(f'Mean Execution Time: {mean_time:.4f} seconds')
    logger.info(f'Longest Execution Time: {max_time:.4f} seconds')
    logger.info(f'Shortest Execution Time: {min_time:.4f} seconds')
    assert failed_requests_counter == 0, f"Some of the {test_name} requests didn't return HTTP status code 200"


def _run_speed_test_cases(helper, test_cases):
    """Run ASR tests for various speech speeds and validate transcriptions"""
    for case in test_cases:
        text = case["text"]
        speed = case["speed"]
        expected_words = case["expected_words"]

        logger.info(f"Generating audio for speed {speed} and text: '{text}'")
        audio = helper.generate_audio(text, speed=speed)

        response = helper.transcribe_audio(audio)

        assert response.status_code == 200, (
            f"Audio transcription failed for speed {speed}. Status: {response.status_code}"
        )

        transcription = helper.get_transcription_text(response)
        logger.debug(f"Speed: {speed} | Transcription: {transcription}")

        assert_all_words_in_transcription(expected_words, transcription)


def assert_all_words_in_transcription(expected_words, transcription):
    missing_words = [word for word in expected_words if word.lower() not in transcription.lower()]
    if missing_words:
        raise AssertionError(f"Expected words not found in transcription: {', '.join(missing_words)}")
