# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.dataprep.utils.file_parser import FileParser
from comps.dataprep.utils.file_loaders.load_pdf import LoadPdf
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter


class Splitter:
    def __init__(self, chunk_size: int = 100, chunk_overlap: int = 10, table_strategy: str = "fast"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.table_strategy = table_strategy
        self.separators = self.get_separators()
        self.split_headers = self.get_split_headers()
        self.text_splitter = self.get_text_splitter()
        self.html_splitter = self.get_html_splitter()

    def load_text(self, file_path: str):
        return FileParser(file_path).parse()  # raises Value Error if file is not supportet

    def split(self, file_path: str):
        text = self.load_text(file_path)

        chunks = []
        if file_path.split('.')[-1] == 'html':
            chunks = self.split_html(text)
        else:
            chunks = self.split_text(text)

        if file_path.split('.')[-1] == 'pdf':
            table_chunks = LoadPdf(file_path).get_tables_result(self.table_strategy)
            if table_chunks is not None and len(table_chunks) > 0:
                chunks.append(table_chunks)

        return chunks

    def split_text(self, text: str):
        chunks = self.text_splitter.split_text(text)
        return chunks

    def split_html(self, html: str):
        chunks = self.html_splitter.split_text(html)
        return [chunk.page_content for chunk in chunks]

    def get_text_splitter(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
            separators=self.separators
        )

    def get_html_splitter(self):
        return HTMLHeaderTextSplitter(
            headers_to_split_on=self.split_headers
        )

    def get_split_headers(self):
        return [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]

    def get_separators(self):
        separators = [
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ]
        return separators
