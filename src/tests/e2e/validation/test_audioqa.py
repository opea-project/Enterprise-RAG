#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest
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


@allure.testcase("IEASG-324")
def test_asr_silence(audioqa_api_helper):
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
@allure.testcase("IEASG-326")
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


@allure.testcase("IEASG-327")
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
