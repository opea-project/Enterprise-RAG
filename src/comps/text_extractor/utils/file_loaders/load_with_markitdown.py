# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from markitdown import MarkItDown
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LoadWithMarkitdown(AbstractLoader):
    """Load and parse various document types using MarkItDown."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_dir = kwargs.get('temp_dir', None)
        self.md = MarkItDown(enable_plugins=False)

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
