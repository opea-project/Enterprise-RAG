# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from docarray import DocList
from unittest.mock import AsyncMock, MagicMock

from comps.cores.proto.docarray import TextDoc, TextCompressionTechnique
from comps.text_compression.utils.opea_text_compression import OPEATextCompressor


@pytest.fixture
def reset_singleton():
    """Reset the singleton instance before each test."""
    OPEATextCompressor._instance = None
    yield

def test_singleton_pattern(reset_singleton):
    """Test that OPEATextCompressor follows the singleton pattern."""
    compressor1 = OPEATextCompressor()
    compressor2 = OPEATextCompressor()
    assert compressor1 is compressor2

def test_initialization(reset_singleton):
    """Test that compression techniques are properly initialized."""
    compressor = OPEATextCompressor()
    assert hasattr(compressor, "initialized_techniques")
    assert len(compressor.initialized_techniques) > 0
    assert "header_footer_stripper" in compressor.initialized_techniques
    assert "ranking_aware_deduplication" in compressor.initialized_techniques

@pytest.mark.asyncio
async def test_compress_with_specific_technique(reset_singleton):
    """Test compressing text with a specific technique."""
    compressor = OPEATextCompressor()

    # Mock the specific compressor
    mock_compressor = MagicMock()
    mock_compressor.compress_text = AsyncMock(return_value="compressed text")
    compressor.initialized_techniques["header_footer_stripper"] = mock_compressor

    result = await compressor.compress("sample text", techniques=[TextCompressionTechnique(name="header_footer_stripper")])

    assert result == "compressed text"

@pytest.mark.asyncio
async def test_compress_with_no_technique(reset_singleton):
    """Test compressing text without specifying a technique."""
    compressor = OPEATextCompressor()

    # Mock all compressors
    for technique in compressor.initialized_techniques:
        mock_compressor = MagicMock()
        mock_compressor.compress_text = AsyncMock(return_value=f"compressed by {technique}")
        compressor.initialized_techniques[technique] = mock_compressor

    # The last applied technique should determine the final result
    expected_result = "sample text"

    result = await compressor.compress("sample text")

    assert result == expected_result
    for mock_comp in compressor.initialized_techniques.values():
        mock_comp.compress_text.assert_not_called()

@pytest.mark.asyncio
async def test_compress_with_params(reset_singleton):
    """Test compressing text with additional parameters."""
    compressor = OPEATextCompressor()

    # Mock the specific compressor
    mock_compressor = MagicMock()
    mock_compressor.compress_text = AsyncMock(return_value="compressed with params")
    compressor.initialized_techniques["header_footer_stripper"] = mock_compressor

    params = {"threshold": 0.5, "min_length": 10}
    result = await compressor.compress("sample text", techniques=[TextCompressionTechnique(name="header_footer_stripper", parameters=params)])

    assert result == "compressed with params"

@pytest.mark.asyncio
async def test_compress_empty_text(reset_singleton):
    """Test compressing empty text."""
    compressor = OPEATextCompressor()
    result = await compressor.compress("", techniques=[TextCompressionTechnique(name="header_footer_stripper")])
    assert result == ""

@pytest.mark.asyncio
async def test_compress_invalid_technique(reset_singleton):
    """Test compressing with invalid technique raises ValueError."""
    compressor = OPEATextCompressor()

    with pytest.raises(ValueError):
        await compressor.compress("sample text", techniques=[TextCompressionTechnique(name="invalid_technique")])

@pytest.mark.asyncio
async def test_compress_docs(reset_singleton):
    """Test compressing a list of documents."""
    compressor = OPEATextCompressor()

    # Mock the specific compressor
    mock_compressor = MagicMock()
    mock_compressor.compress_text = AsyncMock(return_value="compressed text")
    compressor.initialized_techniques["header_footer_stripper"] = mock_compressor

    # Create test documents
    docs = DocList[TextDoc]([
        TextDoc(text="doc1 text", metadata={"id": "1"}),
        TextDoc(text="doc2 text", metadata={"id": "2"}),
        TextDoc(text="", metadata={"id": "3"})
    ])

    result = await compressor.compress_docs(docs, techniques=[TextCompressionTechnique(name="header_footer_stripper")])

    assert len(result) == 3
    assert result[0].text == "compressed text"
    assert result[1].text == "compressed text"
    assert result[2].text == ""  # Empty doc should remain empty

    # Check metadata
    assert result[0].metadata["compression_technique"] == "header_footer_stripper"
    assert result[0].metadata["original_length"] == 9  # len("doc1 text")
    assert result[0].metadata["compressed_length"] == 15  # len("compressed text")
    assert result[0].metadata["compression_ratio"] == 15/9

    # Check that original metadata is preserved
    assert result[0].metadata["id"] == "1"
    assert result[1].metadata["id"] == "2"
    assert result[2].metadata["id"] == "3"

    # Empty doc should have compression metadata too
    assert "compression_technique" in result[2].metadata
    assert result[2].metadata["compression_ratio"] == 1.0

@pytest.mark.asyncio
async def test_compression_technique_error_handling(reset_singleton):
    """Test error handling when a compression technique fails."""
    compressor = OPEATextCompressor()

    # Mock the specific compressor to raise an exception
    mock_compressor = MagicMock()
    mock_compressor.compress_text.side_effect = Exception("Compression failed")
    compressor.initialized_techniques["header_footer_stripper"] = mock_compressor

    with pytest.raises(Exception) as exc_info:
        await compressor.compress("sample text", techniques=[TextCompressionTechnique(name="header_footer_stripper")])

    assert "Error applying compression technique" in str(exc_info.value)