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
        self.header_patterns = [
            r'^[^\n]*confidential[^\n]*\n',
            r'^[^\n]*proprietary[^\n]*\n',
            r'^[^\n]*copyright[^\n]*\n',
            r'^[^\n]*all rights reserved[^\n]*\n',
        ]

        self.footer_patterns = [
            r'\n[^\n]*confidential[^\n]*$',
            r'\n[^\n]*proprietary[^\n]*$',
            r'\n[^\n]*copyright[^\n]*$',
            r'\n[^\n]*all rights reserved[^\n]*$',
            r'\n+\s*Sent from my.*?$',
            r'\.{5,}',  # Remove long dot runs
            r'\n+--\s*\n.*$',  # Email signature separator
        ]

    async def compress_text(self, text: str,
                            file_info: str = None,
                            header_patterns: Optional[List[str]] = None,
                            footer_patterns: Optional[List[str]] = None) -> str:
        """
        Compress text by removing headers and footers.

        Args:
            text (str): The text to compress.
            custom_header_patterns: Additional header patterns to remove.
            custom_footer_patterns: Additional footer patterns to remove.

        Returns:
            str: The compressed text.
        """

        # Process headers first
        patterns = self.header_patterns.copy()
        if header_patterns:
            patterns.extend(header_patterns)

        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = text.lstrip()

        # Then process footers
        patterns = self.footer_patterns.copy()
        if footer_patterns:
            patterns.extend(footer_patterns)

        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = text.rstrip()

        return text

    def __str__(self):
        return "HeaderFooterStripper Compressor"
