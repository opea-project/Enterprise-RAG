# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import io
import json
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from comps.cores.proto.docarray import DataPrepInput, TextDoc
from fastapi import HTTPException, UploadFile
from typing import List
from comps.dataprep.utils.utils import document_loader, get_separators, get_split_headers, get_tables_result, parse_files, parse_links
import logging
import base64

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

    async def dataprep(self, input: DataPrepInput) -> List[TextDoc]:

        files = input.files
        link_list = input.links

        logging.info(f"Dataprep files: {files}")
        logging.info(f"Dataprep link list: {link_list}")

        if not files and not link_list:
            raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")

        saved_files: List[TextDoc] = []

        # Save files
        if files:
            try:
                decoded_files = []
                for f in files:
                    file_data = base64.b64decode(f.data64)
                    binary_file = io.BytesIO(file_data)
                    decoded_file = UploadFile(filename=f.filename, file=binary_file)
                    decoded_files.append(decoded_file)

                f = await parse_files(files=decoded_files)
                saved_files += (f)
            except Exception as e:
                logging.exception(e)
                raise HTTPException(status_code=500, detail=f"Write file failed. Exception: {e}")

        # Save links
        if link_list:
            try:
                if not isinstance(link_list, list):
                    raise HTTPException(status_code=400, detail="link_list should be a list.")
                try:
                    f = await parse_links(links=link_list)
                    saved_files += (f)
                except Exception as e:
                    logging.exception(e)
                    raise HTTPException(status_code=500, detail=f"Write link failed. Exception: {e}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

        text_splits = []
        for doc in saved_files:
            text_splitter = None
            path = doc.metadata['path']
            if path.endswith(".html"):
                text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=get_split_headers())
            else:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    add_start_index=True,
                    separators=get_separators()
                )
            chunks = text_splitter.split_text(document_loader(path))
            if path.endswith(".pdf") and self.process_table:
                table_chunks = get_tables_result(path, self.table_strategy)
                chunks = chunks + table_chunks

            for chunk in chunks:
                text_splits.append(TextDoc(text=chunk, metadata=doc.metadata))

            logging.info("Done preprocessing. Created ", len(text_splits), " chunks of the original file ", doc.metadata)
        return text_splits
