# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pymupdf
import nltk
import time
import os
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader
from comps.dataprep.utils.file_loaders.load_image import LoadImage
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LoadPdf(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('averaged_perceptron_tagger_eng', quiet=True)

    def extract_text(self):
        """Load the pdf file."""
        doc = pymupdf.open(self.file_path)
        result = ""

        logger.info(f"[{self.file_path}] Processing {doc.page_count} pages")

        page_count = doc.page_count
        for i in range(page_count):
            start_time = time.time()

            page = doc.load_page(i)
            page.clean_contents()
            
            pagetext = page.get_text().strip()
            if pagetext:
                if pagetext.endswith("!") or pagetext.endswith("?") or pagetext.endswith("."):
                    result = result + pagetext
                else:
                    result = result + pagetext + "."

            # https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
            for link in page.links(): 
                if link.get("uri"):
                    result = result + f" {link.get('uri')}"

            # https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-table-content-from-documents
            finder = page.find_tables()
            for table in finder.tables:
                logger.info(f"[{self.file_path}] Extracting table from page {i+1}")
                table_data = table.extract()
                if len(table_data) > 0:
                    flattened_table_data = [str(item) for sublist in table_data for item in sublist]
                    result += " ".join(flattened_table_data)

            # https://pymupdf.readthedocs.io/en/latest/recipes-images.html#how-to-extract-images-pdf-documents
            images = doc.get_page_images(i, full=False)
            for img in images:
                img_data = doc.extract_image(img[0])
                img_path = ""
                try:
                    img_path = self.save_image(img_data)
                    logger.debug(f"[{self.file_path}] Extracted {img_path} for processing")
                    img_loader = LoadImage(img_path)
                    result += img_loader.extract_text()
                    logger.info(f"[{self.file_path}] Processed image {img_path}")
                except Exception as e:
                    logger.error(f"[{self.file_path}] Error parsing image {img_path}: {e}. Ignoring...")
                finally:
                    if img_path and img_path != "" and os.path.exists(img_path) and not os.path.isdir(img_path):
                        logger.debug(f"[{self.file_path}] Removed {img_path} after processing")
                        os.remove(img_path)

            end_time = time.time()
            logger.info(f"[{self.file_path}] Page {i+1}/{page_count} processed in {end_time - start_time:.2f} seconds")
        return result

    def save_image(self, data, save_path="/tmp/opea_upload"):
        """Save image data to a file."""
        import uuid
        image_ext = data["ext"]
        image_filename = os.path.join(save_path, f"{uuid.uuid4()}.{image_ext}")
        with open(image_filename, "wb") as f:
            f.write(data["image"])
        return image_filename
