# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import docx
import docx2txt
import shutil
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


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

        if rid2img:
            save_path = "./imgs/"
            os.makedirs(save_path, exist_ok=True)
            docx2txt.process(self.file_path, save_path)

        for paragraph in doc.paragraphs:
            if hasattr(paragraph, "text"):
                text += paragraph.text + "\n"

        if rid2img:
            shutil.rmtree(save_path)
        return text

    def convert_to_docx(self, doc_path):
        """Convert doc file to docx file."""
        docx_path = doc_path + "x"
        os.system(f"libreoffice --headless --invisible --convert-to docx --outdir {os.path.dirname(docx_path)} {doc_path}")
        self.file_path = docx_path
        self._file_type = "docx"
