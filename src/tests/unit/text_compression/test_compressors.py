# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
import re

from unittest.mock import patch

from comps.text_compression.utils.compressors.header_footer_stripper_compressor import HeaderFooterStripper
from comps.text_compression.utils.compressors.ranking_aware_deduplication import RankedDeduplicator

# Test for header_footer_stripper_compressor.py

def test_header_footer_stripper_initialization():
    """Test initialization of HeaderFooterStripper."""
    compressor = HeaderFooterStripper()
    assert isinstance(compressor, HeaderFooterStripper)

@pytest.mark.asyncio
async def test_header_footer_stripper_strip_header():
    """Test that the header is correctly stripped."""
    text = """Header line 1
Header line 2
---
Main content line 1
Main content line 2"""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text, custom_patterns=["---"])

    assert "Header line 1" in compressed_text
    assert "Header line 2" in compressed_text
    assert "---" not in compressed_text
    assert "Main content line 1" in compressed_text
    assert "Main content line 2" in compressed_text

@pytest.mark.asyncio
async def test_header_footer_stripper_strip_header_and_footer():
    """Test that both header and footer are correctly stripped."""
    text = """Header line 1
Header line 2
---START---
Main content line 1
Main content line 2
---END---
Footer line 1
Footer line 2"""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text, custom_patterns=["---START---", "---END---"])

    assert "Header line" in compressed_text
    assert "---START---" not in compressed_text
    assert "Main content line" in compressed_text
    assert "---END---" not in compressed_text
    assert "Footer line" in compressed_text

@pytest.mark.asyncio
async def test_header_footer_stripper_no_delimiters_found():
    """Test behavior when delimiters aren't found in the text."""
    text = """This is some text
with no delimiters
so it should remain unchanged."""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text, custom_patterns=["---START---", "---END---"])

    assert compressed_text == text

@pytest.mark.asyncio
async def test_header_footer_stripper_copyright_pattern():
    """Test that copyright patterns are stripped correctly."""
    text = """This is some text.\ninternal use only Copyright: © 2024-2025 Intel Corporation\nSPDX-License-Identifier: Apache-2.0\nThis is the main content.\n"""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text)

    assert "This is some text." in compressed_text
    assert "Copyright: © 2024-2025" not in compressed_text
    assert "SPDX-License-Identifier: Apache-2.0" in compressed_text
    assert "This is the main content." in compressed_text

@pytest.mark.asyncio
async def test_header_footer_stripper_copyright_pattern_without_new_lines():
    """Test that copyright patterns are stripped correctly."""
    text = """This is some text. Copyright (C) 2024-2025 Intel Corporation SPDX-License-Identifier: Apache-2.0 This is the main content.\n"""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text)

    assert "This is some text." in compressed_text
    assert "Copyright: © 2024-2025" not in compressed_text
    assert "SPDX-License-Identifier: Apache-2.0" in compressed_text
    assert "This is the main content." in compressed_text

@pytest.mark.asyncio
async def test_header_footer_stripper_all_rights_reserved_pattern():
    """Test that copyright patterns are stripped correctly."""
    text= """This is some text.\nAll rights reserved. 2024-2025 Intel Corporation\nSPDX-License-Identifier: Apache-2.0\nThis is the main content.\n"""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text)

    assert "This is some text." in compressed_text
    assert "All rights reserved" not in compressed_text
    assert "SPDX-License-Identifier: Apache-2.0" in compressed_text
    assert "This is the main content." in compressed_text

@pytest.mark.asyncio
async def test_header_footer_stripper_all_rights_reserved_pattern_without_new_lines():
    """Test that copyright patterns are stripped correctly."""
    text = """This is some text. All rights reserved 2024-2025 Intel Corporation SPDX-License-Identifier: Apache-2.0 This is the main content.\n"""

    compressor = HeaderFooterStripper()
    compressed_text = await compressor.compress_text(text)

    assert compressed_text == text

# Test for ranking_aware_deduplication.py

@pytest.fixture
def deduplicator():
    # This will return the singleton instance
    return RankedDeduplicator()

@pytest.mark.asyncio
@patch('nltk.sent_tokenize')
async def test_ranking_aware_deduplication_compress_text_sentences(mock_sent_tokenize, deduplicator):
    """Test compress_text with sentence segmentation."""
    mock_sent_tokenize.return_value = [
        "This is the first sentence.",
        "This is a duplicate sentence.",
        "This is a duplicate sentence.",
        "This is the final sentence."
    ]

    text = "This is the first sentence. This is a duplicate sentence. " \
            "This is a duplicate sentence. This is the final sentence."

    result = await deduplicator.compress_text(text, segment_type="sentence")

    # Should contain 3 sentences (deduplicated)
    mock_sent_tokenize.assert_called_once_with(text)
    assert "This is a duplicate sentence." in result
    assert result.count("This is a duplicate sentence.") == 1

@pytest.mark.asyncio
async def test_ranking_aware_deduplication_compress_text_paragraphs(deduplicator):
    """Test compress_text with paragraph segmentation."""
    text = "First paragraph.\n\nDuplicate paragraph.\n\n" \
            "Duplicate paragraph.\n\nLast paragraph."

    result = await deduplicator.compress_text(text, segment_type="paragraph")

    # Should contain 3 paragraphs (deduplicated)
    assert "First paragraph." in result
    assert "Duplicate paragraph." in result
    assert "Last paragraph." in result
    assert result.count("Duplicate paragraph.") == 1

@pytest.mark.asyncio
@patch('comps.text_compression.utils.compressors.ranking_aware_deduplication.logger')
async def test_ranking_aware_deduplication_compress_text_invalid_segment_type(mock_logger_instance, deduplicator):
    """Test compress_text with invalid segment type."""
    text = "Some text."

    await deduplicator.compress_text(text, segment_type="invalid")

    # Verify warning was logged
    mock_logger_instance.warning.assert_called_with(
        "Unknown segment_type: invalid. Using paragraph."
    )

@pytest.mark.asyncio
async def test_ranking_aware_deduplication_compress_text_integration(deduplicator):
    """Integration test for compress_text."""
    text = "First paragraph with important content.\n\n" \
            "Second paragraph has duplicate content.\n\n" \
            "This paragraph has duplicate content.\n\n" \
            "Last paragraph with unique information."

    result = await deduplicator.compress_text(
        text,
        segment_type="paragraph",
        overlap_threshold=0.3
    )

    # Should retain first, second (or third), and last paragraphs
    assert "First paragraph" in result
    assert "Last paragraph" in result
    # Either second or third paragraph should be kept, not both
    assert ("Second paragraph" in result) != ("This paragraph has duplicate" in result)
    # Should have 3 paragraphs total
    assert len(re.split(r'\n\s*\n', result)) == 3
