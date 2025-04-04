# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.docarray import TextDoc
from comps.cores.mega.logger import get_opea_logger
from comps.hierarchical_dataprep.utils.hierarchical_indexer import HierarchicalIndexer
from typing import List

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEAHierarchicalDataPrep:
    """
    Singleton class for managing ingestion into vector store with Hierarchical Indices via microservice API calls.
    """

    _instance = None

    def __new__(cls, chunk_size, chunk_overlap, vllm_endpoint, summary_model, max_new_tokens):
        if cls._instance is None:
            cls._instance = super(OPEAHierarchicalDataPrep, cls).__new__(cls)
            cls._instance._initialize(chunk_size, chunk_overlap, vllm_endpoint, summary_model, max_new_tokens)
        return cls._instance

    def _initialize(self, chunk_size: int, chunk_overlap: int, vllm_endpoint: str, summary_model: str, max_new_tokens: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vllm_endpoint = vllm_endpoint
        self.summary_model = summary_model
        self.max_new_tokens = max_new_tokens

    def hierarchical_dataprep(self, files: any, chunk_size: int = None, chunk_overlap: int = None, vllm_endpoint: str = None, summary_model: str = None, max_new_tokens: int = None):
        if not files:
            raise ValueError("No files passed for hierarchical data preparation.")

        if chunk_size is None:
            chunk_size = self.chunk_size
        if chunk_overlap is None:
            chunk_overlap = self.chunk_overlap
        if vllm_endpoint is None:
            vllm_endpoint = self.vllm_endpoint
        if summary_model is None:
            summary_model = self.summary_model
        if max_new_tokens is None:
            max_new_tokens = self.max_new_tokens

        summary_docs : List[TextDoc] = []
        chunk_docs : List[TextDoc] = []
        text_docs : List[TextDoc] = []

        indexer = HierarchicalIndexer(chunk_size, chunk_overlap, vllm_endpoint, summary_model, max_new_tokens)

        # Save and parse files
        if files:
            try:
                summarydocs, chunkdocs = indexer.parse_files(files=files)
                summary_docs.extend(summarydocs)
                chunk_docs.extend(chunkdocs)
            except Exception as e:
                logger.exception(e)
                raise ValueError(f"Failed to parse file: Exception {e}")
        
        text_docs.extend(summary_docs)
        text_docs.extend(chunk_docs)
        logger.info(f"Done processing. Created {len(summary_docs)} summary docs and {len(chunk_docs)} chunk docs.")
        return text_docs