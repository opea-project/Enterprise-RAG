# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import cairosvg
import nltk
import os
import pytesseract
import regex
from langchain_community.document_loaders import UnstructuredImageLoader
from PIL import Image, ImageOps

from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


class LoadImage(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('averaged_perceptron_tagger_eng', quiet=True)

    def extract_text(self):
        """Run OCR on the image. Try Unstructured first, fall back to pytesseract."""
        if self.file_type == "svg":
            self.convert_to_png(self.file_path)

        # Try Unstructured OCR
        try:
            docs = UnstructuredImageLoader(self.file_path, strategy="ocr_only", language=["eng", "pol"]).load()
            if docs and (text := docs[0].page_content.strip()):
                return self._clean_ocr_text(text)
        except Exception as e:
            logger.debug(f"OCR (unstructured) failed, falling back to pytesseract: {e}")

        # Fallback to pytesseract
        try:
            with Image.open(self.file_path) as img:
                text = pytesseract.image_to_string(ImageOps.autocontrast(img.convert("RGB")), 
                                                    lang="eng+pol", config="--psm 6")
                return self._clean_ocr_text(text)
        except Exception as e:
            logger.error(f"OCR failed for {self.file_path}: {e}")
            return ""

    def convert_to_png(self, image_path):
        """Convert image file to png file."""
        png_path = image_path.split(".")[0] + ".png"
        cairosvg.svg2png(url=image_path, write_to=png_path)
        self.file_path = png_path
        self.file_type = "png"

    def _clean_ocr_text(self, text: str) -> str:
        """Normalize OCR noise: whitespace, punctuation, leading/trailing junk."""
        if not text:
            return ""
        text = text.strip().replace("—", "-").replace("_", " ")
        text = regex.sub(r"\s+", " ", text)
        return text.strip()

