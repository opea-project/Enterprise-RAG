# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import docx
import docx2txt
import shutil
import time
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LoadDoc(AbstractLoader):
    """ Load and parse doc/docx files. """
    def extract_text(self):
        if self.file_type == "doc":
            self.convert_to_docx(self.file_path)

        text = ""
        doc = docx.Document(self.file_path)

        # Save all 'rId:filenames' relationships in an dictionary and save the images if any.
        rid2img = {}

        for r in doc.part.rels.values():
            if isinstance(r._target, docx.parts.image.ImagePart):
                rid2img[r.rId] = os.path.basename(r._target.partname)

        try:
            if rid2img:
                dir_name = os.path.dirname(self.file_path)  # Get the upload folder
                base_name = os.path.splitext(os.path.basename(self.file_path))[0]
                short_base_name = base_name[:10]
                # create a temporary folder with a unique name to save the extracted images
                doc_images_dir = os.path.join(dir_name, f"imgs-{int(time.time())}-{short_base_name}")
                logger.debug(f"LoadDoc: started extracting images to {doc_images_dir}")
                os.makedirs(doc_images_dir, exist_ok=True)
                os.chmod(doc_images_dir, 0o700)
                # extract text and images
                docx2txt.process(self.file_path, doc_images_dir)

            for paragraph in doc.paragraphs:
                if hasattr(paragraph, "text"):
                    text += paragraph.text + "\n"

        except Exception as e:
            raise e
        finally:
            if rid2img:
                # Ensure cleanup of the temporary directory
                shutil.rmtree(doc_images_dir)
                logger.debug(f"LoadDoc: removed {doc_images_dir} after processing")
        return text

    def convert_to_docx(self, doc_path):
        """Convert doc file to docx file."""
        docx_path = doc_path + "x"
        os.system(f"libreoffice --headless --invisible --convert-to docx --outdir {os.path.dirname(docx_path)} {doc_path}")
        self.file_path = docx_path
        self._file_type = "docx"
