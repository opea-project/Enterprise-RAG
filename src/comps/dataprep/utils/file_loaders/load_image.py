# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import cairosvg
import nltk
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader
from langchain_community.document_loaders import UnstructuredImageLoader


class LoadImage(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('averaged_perceptron_tagger_eng')

    def extract_text(self):
        """Load the image file."""
        if self.file_type == "svg":
            self.convert_to_png(self.file_path)

        loader = UnstructuredImageLoader(self.file_path)
        text = loader.load()[0].page_content
        return text.strip()

    def convert_to_png(self, image_path):
        """Convert image file to png file."""
        png_path = image_path.split(".")[0] + ".png"
        cairosvg.svg2png(url=image_path, write_to=png_path)
        self.file_path = png_path
        self.file_type = "png"
