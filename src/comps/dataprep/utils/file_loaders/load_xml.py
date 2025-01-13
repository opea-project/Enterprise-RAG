# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import nltk
from langchain_community.document_loaders import UnstructuredXMLLoader
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadXml(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('averaged_perceptron_tagger_eng')

    def extract_text(self):
        """Load xml file."""
        loader = UnstructuredXMLLoader(self.file_path)
        text = loader.load()[0].page_content
        return text
