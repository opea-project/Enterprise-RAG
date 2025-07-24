import re

from typing import List, Optional

from comps.text_compression.utils.compressors.compressor import Compressor
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class HeaderFooterStripper(Compressor):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HeaderFooterStripper, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the header and footer stripper."""
        # Common patterns for headers and footers
        self.patterns = [
            r'^\s*confidential\s*$',
            r'^\s*proprietary\s*$',
            r'(?i)\b(copyright|©|\(c\))\b.{0,100}?(?:19\d{2}|20\d{2})(?:\s*[-–—]\s*(?:19\d{2}|20\d{2}))?', # matches copyright statements only with years/year ranges
            r'(?i)^\s*all rights reserved\b\s*', # matches "All rights reserved" only at the start of a line
            r'\n+\s*Sent from my.*?$',
            r'\.{5,}',  # Remove long dot runs
            r'\n+--\s*\n.*$',  # Email signature separator
        ]

    async def compress_text(self, text: str,
                            file_info: str = None,
                            custom_patterns: Optional[List[str]] = None) -> str:
        """
        Compress text by removing headers and footers.

        Args:
            text (str): The text to compress.
            custom_patterns: Additional patterns to remove.

        Returns:
            str: The compressed text.
        """

        patterns = self.patterns.copy()
        if custom_patterns:
            patterns.extend(custom_patterns)

        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

        return text

    def __str__(self):
        return "HeaderFooterStripper Compressor"
