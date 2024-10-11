# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.docarray import TextDoc
from comps.cores.mega.logger import get_opea_logger
from comps.dataprep.utils.splitter import Splitter
from comps.dataprep.utils.utils import parse_files, parse_links
from typing import List

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEADataprep:
    """
    Singleton class for managing ingestion into vector stores via microservice API calls.
    """

    _instance = None

    def __new__(cls, chunk_size, chunk_overlap, process_table, table_strategy):
        if cls._instance is None:
            cls._instance = super(OPEADataprep, cls).__new__(cls)
            cls._instance._initialize(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                process_table=process_table,
                table_strategy=table_strategy
            )
        return cls._instance

    def _initialize(self, chunk_size: int, chunk_overlap: int, process_table: bool, table_strategy: str):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.process_table = process_table
        self.table_strategy = table_strategy

    async def dataprep(self, files: any, link_list: list) -> List[TextDoc]:

        if not files and not link_list:
            raise ValueError("No links and/or files passed for data preparation.")

        text_docs: List[TextDoc] = []

        splitter = Splitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            table_strategy=self.table_strategy
        )

        # Save files
        if files:
            try:
                textdocs = await parse_files(
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
                textdocs = await parse_links(
                    links=link_list,
                    splitter=splitter
                )
                text_docs.extend(textdocs)
            except Exception as e:
                logger.exception(e)
                raise ValueError(f"Failed to parse link. Exception: {e}")

        logger.info(f"Done preprocessing. Created {len(text_docs)} chunks.")
        return text_docs
