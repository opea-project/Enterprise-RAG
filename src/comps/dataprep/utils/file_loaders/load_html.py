# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import nltk
from langchain_community.document_loaders import UnstructuredHTMLLoader
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadHtml(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('averaged_perceptron_tagger_eng')

    def extract_text(self):
        """Load the html file."""
        data_html = UnstructuredHTMLLoader(self.file_path).load()
        content = []
        for ins in data_html:
            content.append(ins.page_content)
        return '\n'.join(content)
