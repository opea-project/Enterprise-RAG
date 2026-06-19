# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import BinaryIO, Any
from charset_normalizer import from_bytes
from markitdown import MarkItDown
from markitdown._base_converter import DocumentConverterResult
from markitdown._stream_info import StreamInfo
from markitdown.converters._plain_text_converter import PlainTextConverter
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class RobustPlainTextConverter(PlainTextConverter):
    """
    Fixed PlainTextConverter that handles encoding detection correctly.

    Bug in markitdown <=0.1.6: charset detected from first 4KB only. If special
    characters (e.g., macramé) appear beyond 4KB, UnicodeDecodeError occurs when
    decoding with wrong charset (ASCII instead of UTF-8).

    Fix: Always fall back to full-file charset detection via charset_normalizer
    when initial encoding fails, or when no charset provided.
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        # Reject HTML files - let HTML converter handle them
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if "html" in mimetype or extension in (".html", ".htm"):
            return False

        # For other files, use parent class logic
        return super().accepts(file_stream, stream_info, **kwargs)

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        file_bytes = file_stream.read()

        if stream_info.charset:
            try:
                text_content = file_bytes.decode(stream_info.charset)
            except (UnicodeDecodeError, LookupError) as e:
                logger.warning(
                    f"Charset {stream_info.charset} (detected from first 4KB) failed: {e}. "
                    f"Falling back to full-file charset detection."
                )
                text_content = str(from_bytes(file_bytes).best())
        else:
            text_content = str(from_bytes(file_bytes).best())

        return DocumentConverterResult(markdown=text_content)

class LoadWithMarkitdown(AbstractLoader):
    """Load and parse various document types using MarkItDown."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_dir = kwargs.get('temp_dir', None)
        self.md = MarkItDown(enable_plugins=False)

        # Register robust text converter to fix encoding bug
        # Priority 0.0 ensures it runs before default PlainTextConverter (priority 10.0)
        self.md.register_converter(RobustPlainTextConverter(), priority=0.0)

    def _handle_adoc_file(self):
        """Process AsciiDoc files by converting to HTML first."""
        temp_dir = self.temp_dir or os.path.dirname(self.file_path)
        temp_html_file = os.path.join(temp_dir, f"temp_output_{os.path.basename(self.file_path)}.html")
        
        try:
            os.system(f"asciidoctor -b html5 -o {temp_html_file} {self.file_path}")
            logger.info(f"Converted adoc to html. Created temporary file: {temp_html_file}")
            
            result = self.md.convert(temp_html_file)
            return result
        except Exception as e:
            err_msg = f"Failed to parse adoc file. Exception: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e
        finally:
            if os.path.exists(temp_html_file):
                os.remove(temp_html_file)
                logger.info(f"Removed temporary file: {temp_html_file}")

    def _handle_ppt_file(self):
        """Convert ppt file to pptx file."""
        original_file_path = self.file_path
        pptx_path = self.file_path + "x"
        
        try:
            os.system(f"libreoffice --headless --invisible --convert-to pptx --outdir {os.path.dirname(pptx_path)} {self.file_path}")
            
            if not os.path.exists(pptx_path):
                err_msg = f"Failed to convert PPT file: {self.file_path} - PPTX file not created"
                logger.error(err_msg)
                raise RuntimeError(err_msg)
                
            self.file_path = pptx_path
            self.file_type = "pptx"
            logger.info(f"Converted PPT to PPTX: {self.file_path}")
        except Exception as e:
            err_msg = f"Failed to convert PPT file. Exception: {e}"
            logger.error(err_msg)
            self.file_path = original_file_path
            raise RuntimeError(err_msg) from e
    
    def extract_text(self):
        """Extract text content from document based on file type."""
        if self.file_type == "adoc":
            result = self._handle_adoc_file()
        elif self.file_type == "ppt":
            self._handle_ppt_file()
            result = self.md.convert(self.file_path)
        else:
            result = self.md.convert(self.file_path)

        return result.text_content

    def extract_metadata(self):
        """Extract metadata, delegating to LoadXls for xlsx/xls files."""
        if self.file_type in ('xlsx', 'xls'):
            from comps.text_extractor.utils.file_loaders.load_xls import LoadXls
            return LoadXls(self.file_path).extract_metadata()
        return super().extract_metadata()
