# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.dataprep.utils.file_parser import FileParser
from comps.dataprep.utils.file_loaders.load_pdf import LoadPdf
from comps.cores.mega.logger import get_opea_logger
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEndpointEmbeddings

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class Splitter:
    def __init__(self, chunk_size: int = 100, chunk_overlap: int = 10, process_table: bool = False, table_strategy: str = "fast"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.process_table = process_table
        self.table_strategy = table_strategy
        self.separators = self.get_separators()
        self.text_splitter = self.get_text_splitter()

    def load_text(self, file_path: str):
        return FileParser(file_path).parse() # raises Value Error if file is not supported

    def split(self, file_path: str):
        text = self.load_text(file_path)
        chunks = self.split_text(text)

        if file_path.split('.')[-1] == 'pdf':
            table_chunks = LoadPdf(file_path).get_tables_result(self.table_strategy)
            if table_chunks is not None and len(table_chunks) > 0:
                chunks.append(table_chunks)

        return chunks

    def split_text(self, text: str):
        chunks = self.text_splitter.split_text(text)
        return chunks

    def get_text_splitter(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
            separators=self.separators
        )

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

class SemanticSplitter(Splitter):
    def __init__(self, chunk_size: int = 100, chunk_overlap: int = 10,
                 table_strategy: str = "fast",
                 embedding_model_server: str = "torchserve",
                 embedding_model_server_endpoint: str = "http://localhost:8090",
                 embedding_model_name: str = "BAAI/bge-large-en-v1.5",
                 semantic_chunk_params: dict = None):
        super().__init__(chunk_size, chunk_overlap, table_strategy)
        self.embedding_model_server = embedding_model_server
        self.embedding_model_server_endpoint = embedding_model_server_endpoint
        self.embedding_model_name = embedding_model_name
        self.semantic_chunk_params = semantic_chunk_params or {}
        logger.info(f"Initializing Semantic Chunking with model server {self.embedding_model_server} running on endpoint: {self.embedding_model_server_endpoint}")
        self.text_splitter = self.get_text_splitter_semantic()

        # Validate inputs
        if not self.embedding_model_server_endpoint:
            raise ValueError("embedding_model_server_endpoint must be provided")

    def get_text_splitter_semantic(self):
        """
        Returns a text splitter instance based on configuration settings.
        Creates a SemanticChunker with embeddings.
        """
        # Format endpoint according to torchserve requirements
        if self.embedding_model_server == "torchserve":
            self.embedding_model_server_endpoint = (
                self.embedding_model_server_endpoint.rstrip('/')
                + f"/predictions/{self.embedding_model_name.split('/')[-1]}"
            )
            embeddings = HuggingFaceEndpointEmbeddings(model=self.embedding_model_server_endpoint)
        else:
            embeddings = HuggingFaceEndpointEmbeddings(model=self.embedding_model_server_endpoint)


        return SemanticChunker(
                embeddings=embeddings,
                buffer_size=self.semantic_chunk_params.get("buffer_size", 1),
                add_start_index=self.semantic_chunk_params.get("add_start_index", False),
                breakpoint_threshold_type=self.semantic_chunk_params.get(
                    "breakpoint_threshold_type", "percentile"
                ),
                breakpoint_threshold_amount=self.semantic_chunk_params.get(
                    "breakpoint_threshold_amount", None
                ),
                number_of_chunks=self.semantic_chunk_params.get("number_of_chunks", None),
                min_chunk_size=self.semantic_chunk_params.get("min_chunk_size", None),
            )
