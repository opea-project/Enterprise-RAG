# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.docarray import TextDoc
from comps.cores.mega.logger import get_opea_logger
from comps.text_splitter.utils.splitter import Splitter, SemanticSplitter
from typing import List
import os
from comps.cores.utils.utils import sanitize_env

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEATextSplitter:
    """
    Singleton class for managing data splitting into chunks.
    """

    _instance = None

    def __new__(cls, chunk_size, chunk_overlap, use_semantic_chunking):
        if cls._instance is None:
            cls._instance = super(OPEATextSplitter, cls).__new__(cls)
            cls._instance._initialize(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                use_semantic_chunking=use_semantic_chunking
            )
        return cls._instance

    def _initialize(self, chunk_size: int, chunk_overlap: int, use_semantic_chunking: bool):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_semantic_chunking = use_semantic_chunking

    def split_docs(self, loaded_docs: List[TextDoc], chunk_size: int = None, chunk_overlap: int = None, use_semantic_chunking: bool = None) -> List[TextDoc]:
        cur_chunk_size = chunk_size if chunk_size is not None else self.chunk_size
        cur_chunk_overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap
        cur_use_semantic_chunking = use_semantic_chunking if use_semantic_chunking is not None else self.use_semantic_chunking

        all_empty_docs = all(doc.text.strip() == "" for doc in loaded_docs)
        if len(loaded_docs) == 0 or all_empty_docs:
            raise ValueError("No documents passed for data preparation.")

        text_docs: List[TextDoc] = []

        # Use SemanticSplitter if use_semantic_chunking  is set to true
        if cur_use_semantic_chunking:
            if chunk_size is not None or chunk_overlap is not None:
                logger.warning(
                    "Semantic chunking does not use 'chunk_size' or 'chunk_overlap' parameters. "
                    "These values will be ignored."
                )

            try:
                splitter = SemanticSplitter(
                    embedding_service_endpoint=sanitize_env(os.getenv("EMBEDDING_SERVICE_ENDPOINT")),
                    semantic_chunk_params_str=sanitize_env(os.getenv("SEMANTIC_CHUNK_PARAMS"))
                    )

            except Exception as e:
                logger.exception(f"An unexpected error occurred while initializing the splitter_semantic module: {e}")
                raise
 
        else:
            try:
                splitter = Splitter(
                    chunk_size=cur_chunk_size,
                    chunk_overlap=cur_chunk_overlap,
                )
            except Exception as e:
                logger.exception(f"An unexpected error occurred while initializing the splitter_recursive module: {e}")
                raise

        for doc in loaded_docs:
            chunks = splitter.split_text(doc.text)
            for chunk in chunks:
                text_docs.append(TextDoc(text=chunk, metadata=doc.metadata))

        logger.info(f"Done preprocessing. Created {len(text_docs)} chunks.")
        return text_docs
