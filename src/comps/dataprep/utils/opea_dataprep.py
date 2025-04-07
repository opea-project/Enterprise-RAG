# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.docarray import TextDoc
from comps.cores.mega.logger import get_opea_logger
from comps.dataprep.utils.splitter import Splitter, SemanticSplitter
from comps.dataprep.utils.utils import parse_files, parse_links
from typing import List
import os
from comps.cores.utils.utils import sanitize_env
import json

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEADataprep:
    """
    Singleton class for managing ingestion into vector stores via microservice API calls.
    """

    _instance = None

    def __new__(cls, chunk_size, chunk_overlap, process_table, table_strategy, use_semantic_chunking):
        if cls._instance is None:
            cls._instance = super(OPEADataprep, cls).__new__(cls)
            cls._instance._initialize(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                process_table=process_table,
                table_strategy=table_strategy,
                use_semantic_chunking=use_semantic_chunking
            )
        return cls._instance

    def _initialize(self, chunk_size: int, chunk_overlap: int, process_table: bool, table_strategy: str, use_semantic_chunking: bool):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.process_table = process_table
        self.table_strategy = table_strategy
        self.use_semantic_chunking = use_semantic_chunking

    def dataprep(self, files: any, link_list: list, chunk_size: int = None, chunk_overlap: int = None, process_table: bool = False, table_strategy: str = None) -> List[TextDoc]:

        if not files and not link_list:
            raise ValueError("No links and/or files passed for data preparation.")

        text_docs: List[TextDoc] = []

        # Convert semantic_chunk_params to dict
        semantic_chunk_params_str = sanitize_env(os.getenv("SEMANTIC_CHUNK_PARAMS"))
        if semantic_chunk_params_str == "{}":
            semantic_chunk_params = {}
        else:
            try:
                semantic_chunk_params = json.loads(semantic_chunk_params_str)
            except (TypeError, json.JSONDecodeError):
                semantic_chunk_params = None

        # Use SemanticSplitter if use_semantic_chunking  is set to true
        if self.use_semantic_chunking:
           splitter = SemanticSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                table_strategy=self.table_strategy,
                embedding_model_name=sanitize_env(os.getenv("EMBEDDING_MODEL_NAME")),
                embedding_model_server=sanitize_env(os.getenv("EMBEDDING_MODEL_SERVER")),
                embedding_model_server_endpoint=sanitize_env(os.getenv("EMBEDDING_MODEL_SERVER_ENDPOINT")),
                semantic_chunk_params=semantic_chunk_params
                )
        else:
            splitter = Splitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            table_strategy=self.table_strategy
            )

        # Save files
        if files:
            try:
                textdocs = parse_files(
                    files=files,
                    splitter=splitter
                )
                text_docs.extend(textdocs)
            except Exception as e:
                logger.exception(e)
                raise ValueError(f"Failed to parse file. Exception: {e}")

        # Save links
        if link_list:
            try:
                textdocs = parse_links(
                    links=link_list,
                    splitter=splitter
                )
                text_docs.extend(textdocs)
            except Exception as e:
                logger.exception(e)
                raise ValueError(f"Failed to parse link. Exception: {e}")

        logger.info(f"Done preprocessing. Created {len(text_docs)} chunks.")
        return text_docs
