# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
import uuid
from fastapi import UploadFile
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms import VLLMOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from comps.cores.proto.docarray import TextDoc
from comps.cores.mega.logger import get_opea_logger
from comps.cores.utils.utils import sanitize_env

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class HierarchicalIndexer:
    """
    Class for creating summary and chunk text documents based on the Hierarchical Indexing algorithm.
    """

    def __init__(self, chunk_size: int, chunk_overlap: int, vllm_endpoint: str, summary_model: str, max_new_tokens: int):
        self.vllm_endpoint = vllm_endpoint
        self.summary_model = summary_model
        self.max_new_tokens = max_new_tokens
        
        self.summary_prompt = """
        Write a concise summary of the following text in less than {max_new_tokens} words:
        TEXT: {text} \
        CONCISE SUMMARY:
        """

        self.doc_loader = PyPDFLoader
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def _save_file_to_local_disk(self, file: UploadFile) -> Tuple[str, str]:
        upload_folder = sanitize_env(os.getenv('UPLOAD_PATH', '/tmp/opea_upload'))

        if not os.path.exists(upload_folder):
            Path(upload_folder).mkdir(parents=True, exist_ok=True)
            # Set the directory permission to 700 (owner: rwx)
            os.chmod(upload_folder, 0o700)

        save_path = Path(os.path.join(upload_folder, file.filename))
        with save_path.open("wb") as fout:
            try:
                content = file.file.read()
                fout.write(content)
                fout.close()
            except Exception as e:
                logger.exception(f"Write file failed when persisting files. Exception: {e}")
                raise

        # Assign a unique doc_id to the file
        doc_id = str(uuid.uuid4())
        logger.info(f"File saved to {save_path} with doc_id: {doc_id}")
        return save_path, doc_id
    
    def _generate_summary(self, text: str) -> str:
        try:
            llm = VLLMOpenAI(
                openai_api_key="EMPTY",
                openai_api_base=f"{self.vllm_endpoint}/v1",
                max_tokens=self.max_new_tokens,
                model_name=self.summary_model,
            )

            response = llm.invoke(self.summary_prompt.format(text=text, max_new_tokens=self.max_new_tokens))
        except Exception as e:
            error_message = f"Failed to invoke VLLM. Check if the endpoint '{self.vllm_endpoint}' is correct and the VLLM service is running."
            logger.error(error_message)
            raise Exception(f"{error_message}: {e}")

        return response

    def parse_files(self, files: List[UploadFile]) -> Tuple[List[TextDoc], List[TextDoc]]:
        parsed_summaries : List[TextDoc] = []
        parsed_chunks :  List[TextDoc] = []
        
        for file in files:
            saved_path = ""

            try:
                saved_path, doc_id = self._save_file_to_local_disk(file)
                doc_pages = self.doc_loader(saved_path).load()
                
                # Generate summaries via VLLM
                for page in doc_pages:
                    page_text = page.page_content
                    summary = self._generate_summary(page_text)
                    metadata = {"doc_id": doc_id, "page": page.metadata["page"], "summary": 1}
                    parsed_summaries.append(TextDoc(text=summary, metadata=metadata))
                
                # Split page into chunks
                doc_chunks = self.text_splitter.split_documents(doc_pages)
                for chunk in doc_chunks:
                    chunk_text = chunk.page_content
                    metadata = {"doc_id": doc_id, "page": chunk.metadata["page"], "summary": 0}
                    parsed_chunks.append(TextDoc(text=chunk_text, metadata=metadata))
            except Exception as e:
                logger.exception(e)
                raise e
            finally:
                if os.path.exists(saved_path):
                    logger.info(f"removed {saved_path} after processing")
                    os.remove(saved_path)
        
        return parsed_summaries, parsed_chunks
