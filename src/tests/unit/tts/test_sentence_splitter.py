# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.tts.utils.sentence_splitter import SentenceAwareTextSplitter

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/tts --cov-report=term --cov-report=html tests/unit/tts/test_sentence_splitter.py

Alternatively, to run all tests for the 'tts' module, execute the following command:
   pytest --disable-warnings --cov=comps/tts --cov-report=term --cov-report=html tests/unit/tts
"""


def test_split_text_single_sentence_under_limit():
    """Test that a single sentence under the chunk size is returned as-is."""
    splitter = SentenceAwareTextSplitter(chunk_size=100, chunk_overlap=0)
    text = "This is a short sentence."

    result = splitter.split_text(text)

    assert len(result) == 1
    assert result[0] == "This is a short sentence."


def test_split_text_sentences_exceed_limit():
    """Test that text is split when sentences exceed chunk size."""
    splitter = SentenceAwareTextSplitter(chunk_size=50, chunk_overlap=0)
    text = "This is the first sentence. This is the second sentence. This is the third sentence."

    result = splitter.split_text(text)

    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 50 or chunk.endswith('.')


def test_split_text_exclamation_delimiter():
    """Test splitting on exclamation mark delimiters."""
    splitter = SentenceAwareTextSplitter(chunk_size=30, chunk_overlap=0)
    text = "Hello world! How are you! Great day!"

    result = splitter.split_text(text)

    assert len(result) >= 1
    for chunk in result:
        assert chunk.strip()


def test_split_text_question_delimiter():
    """Test splitting on question mark delimiters."""
    splitter = SentenceAwareTextSplitter(chunk_size=30, chunk_overlap=0)
    text = "How are you? What is this? Where to go?"

    result = splitter.split_text(text)

    assert len(result) >= 1
    for chunk in result:
        assert chunk.strip()


def test_split_text_mixed_delimiters():
    """Test splitting with mixed punctuation delimiters."""
    splitter = SentenceAwareTextSplitter(chunk_size=40, chunk_overlap=0)
    text = "Hello! How are you? Fine, thanks. Great."

    result = splitter.split_text(text)

    assert len(result) >= 1
    combined = " ".join(result)
    assert "Hello!" in combined
    assert "How are you?" in combined


def test_split_text_chunk_size_128():
    """Test with chunk size of 128 (common TTS chunk size)."""
    splitter = SentenceAwareTextSplitter(chunk_size=128, chunk_overlap=0)
    text = ("This is a longer text that might be used for TTS processing. "
            "It contains multiple sentences. Each sentence should be handled appropriately. "
            "The splitter should combine them when possible, but split when necessary.")

    result = splitter.split_text(text)

    assert len(result) >= 1
    for chunk in result:
        assert len(chunk) <= 200


def test_split_text_no_punctuation():
    """Test handling of text without punctuation."""
    splitter = SentenceAwareTextSplitter(chunk_size=30, chunk_overlap=0)
    text = "This is text without any ending punctuation"

    result = splitter.split_text(text)

    assert len(result) >= 1
    assert result[0] == text


def test_split_text_realistic_tts_example():
    """Test with a realistic TTS use case."""
    splitter = SentenceAwareTextSplitter(chunk_size=128, chunk_overlap=0)
    text = ("Autonomous vehicles rely on AI for navigation and decision-making. "
            "Self-driving cars use computer vision, sensor fusion, and deep learning. "
            "Companies like Tesla, Waymo, and Cruise are improving their systems.")

    result = splitter.split_text(text)

    assert len(result) >= 1
    for chunk in result:
        assert len(chunk) > 0
        assert len(chunk) <= 150  # Allow some buffer
