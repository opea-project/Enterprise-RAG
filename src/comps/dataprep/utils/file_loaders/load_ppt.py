# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pptx
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader
from comps.dataprep.utils.file_loaders.load_image import LoadImage
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LoadPpt(AbstractLoader):
    """ Load and parse ppt/pptx files. """
    def extract_text(self):
        if self.file_type == "ppt":
            self.convert_to_pptx(self.file_path)

        text = ""
        prs = pptx.Presentation(self.file_path)
        logger.info(f"[{self.file_path}] Processing {len(prs.slides)} slides")

        for slide in prs.slides:
            for shape in sorted(slide.shapes, key=lambda shape: (shape.top, shape.left)):
                if shape.has_text_frame:
                    if shape.text:
                        text += shape.text + "\n"
                if shape.has_table:
                    table_contents = "\n".join(
                        [
                            "\t".join([(cell.text if hasattr(cell, "text") else "") for cell in row.cells])
                            for row in shape.table.rows
                            if hasattr(row, "cells")
                        ]
                    )
                    if table_contents:
                        text += table_contents + "\n"
                if shape.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE:
                    img_path = ""
                    try:
                        img_path = self.save_image(shape.image, os.getenv("UPLOAD_PATH", "/tmp/opea_upload"))
                        logger.debug(f"[{self.file_path}] Extracted {img_path} for processing")
                        img_loader = LoadImage(img_path)
                        text += img_loader.extract_text()
                        logger.info(f"[{self.file_path}] Processed image {img_path}")
                    except Exception as e:
                        logger.error(f"[{self.file_path}] Error parsing image: {e}. Ignoring...")
                    finally:
                        if img_path and img_path != "" and os.path.exists(img_path) and not os.path.isdir(img_path):
                            logger.debug(f"[{self.file_path}] Removed {img_path} after processing")
                            os.remove(img_path)
        return text

    def save_image(self, image, save_path="/tmp/opea_upload"):
        import uuid
        import os
        if image:
            image_filename = os.path.join(save_path, f"{uuid.uuid4()}.{image.ext}")
            with open(image_filename, 'wb') as f:
                f.write(image.blob)
            return image_filename
        return None

    def convert_to_pptx(self, ppt_path):
        """Convert ppt file to pptx file."""
        pptx_path = ppt_path + "x"
        os.system(f"libreoffice --headless --invisible --convert-to pptx --outdir {os.path.dirname(pptx_path)} {ppt_path}")
        self.file_path = pptx_path
        self.file_type = "pptx"
