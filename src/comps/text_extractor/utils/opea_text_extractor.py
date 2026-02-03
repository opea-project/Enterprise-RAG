# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import nltk
import os
import re
import time
from pathlib import Path
from typing import List
from fastapi import UploadFile
from requests.exceptions import HTTPError, ConnectionError, ProxyError

from comps.cores.proto.docarray import TextDoc
from comps.text_extractor.utils.crawler import Crawler
from comps.text_extractor.utils.file_parser import FileParser
from comps.cores.mega.logger import get_opea_logger
from comps.cores.utils.utils import sanitize_env

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEATextExtractor:
    """
    Singleton class for managing ingestion into vector stores via microservice API calls.
    """

    _instance = None

    def __new__(cls, asr_endpoint=None):
        if cls._instance is None:
            cls._instance = super(OPEATextExtractor, cls).__new__(cls)
            cls._instance.asr_endpoint = asr_endpoint

            # Download NLTK data once at instance creation to avoid slower performance on first call
            nltk.download('punkt_tab', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('averaged_perceptron_tagger_eng', quiet=True)

        return cls._instance

    def load_data(self, files: any, link_list: list, texts: list) -> List[TextDoc]:

        if not files and not link_list and not texts:
            raise ValueError("No links and/or files and/or texts passed for data preparation.")

        loaded_docs: List[TextDoc] = []

        # Save files
        if files:
            try:
                textdocs = self._load_files(files=files)
                loaded_docs.extend(textdocs)
            except Exception as e:
                logger.error(e)
                raise ValueError(f"Failed to load file. Exception: {e}")

        # Save links
        if link_list:
            try:
                textdocs = self._load_links(links=link_list)
                loaded_docs.extend(textdocs)
            except (HTTPError, ConnectionError, ProxyError) as e:
                logger.error(e)
                raise
            except Exception as e:
                logger.error(e)
                raise ValueError(f"Failed to load link. Exception: {e}")

        # Save texts
        if texts:
            try:
                for text in texts:
                    if text.strip() == "":
                        logger.warning("Empty text found, skipping...")
                        continue

                    metadata = {
                        'timestamp': time.time()
                    }
                    loaded_docs.append(TextDoc(text=text, metadata=metadata))
            except Exception as e:
                logger.error(e)
                raise ValueError(f"Failed to load text. Exception: {e}")

        logger.info(f"Done preprocessing. Loaded {len(loaded_docs)} documents.")
        return loaded_docs

    def _load_files(self, files: List[UploadFile]) -> List[TextDoc]:
        loaded_docs: List[TextDoc] = []

        for file in files:
            saved_path = ""
            # if files have to be persisted internally
            try:
                path = self._save_file_to_local_disk(file)
                saved_path = str(path.resolve())
                logger.info(f"Saved file {file.filename} to {saved_path}")

                metadata = {
                    'filename': file.filename,
                    'timestamp': time.time()
                }

                loaded_docs.append(TextDoc(text=self._load_text(saved_path), metadata=metadata))
            except Exception as e:
                logger.error(e)
                raise e
            finally:
                if saved_path != "" and os.path.exists(saved_path) and not os.path.isdir(saved_path):
                    logger.info(f"Removed {saved_path} after processing")
                    os.remove(saved_path)

        return loaded_docs


    def _load_links(self, links: List[str]) -> List[TextDoc]:
        loaded_docs: List[TextDoc] = []

        for link in links:
            saved_path = ""
            if not re.match(r"^https?:/{2}\w.+$", link):
                logger.info(f"The given link/str {link} cannot be parsed.")
                raise ValueError(f"The given link/str {link} cannot be parsed.")

            try:
                # { url, filename, file_path, content_type }
                parsed_link = self._save_link_to_local_disk(link)
                saved_path = parsed_link['file_path']

                metadata = {
                    'url': parsed_link['url'],
                    'filename': parsed_link['filename'],
                    'timestamp': time.time()
                }

                # User parser if file type is html
                if 'html' in parsed_link['content_type']:
                    logger.info(f"Parsing {parsed_link['file_path']} as HTML")
                    content = self._load_html_data(parsed_link['file_path'])
                    with open(parsed_link['file_path'], "w", encoding="utf-8") as f:
                        f.write(content)

                loaded_docs.append(TextDoc(text=self._load_text(parsed_link['file_path']), metadata=metadata))
            except Exception as e:
                logger.error(e)
                raise e
            finally:
                if saved_path != "" and os.path.exists(saved_path) and not os.path.isdir(saved_path):
                    logger.info(f"Removed {saved_path} after processing")
                    os.remove(saved_path)

        return loaded_docs

    def _save_file_to_local_disk(self, file: UploadFile) -> str:
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
                fout.close
            except Exception as e:
                logger.exception(f"Write file failed when presisting files. Exception: {e}")
                raise

        return save_path


    def _save_link_to_local_disk(self, url: str) -> dict:
        upload_folder = sanitize_env(os.getenv('UPLOAD_PATH', '/tmp/opea_upload'))
        if not os.path.exists(upload_folder):
            Path(upload_folder).mkdir(parents=True, exist_ok=True)
            # Set the directory permission to 700 (owner: rwx)
            os.chmod(upload_folder, 0o700)
        crawler = Crawler()
        return crawler.download_file(url, upload_folder)


    def _load_text(self, file_path: str):
        return FileParser(file_path, self.asr_endpoint).parse() # raises Value Error if file is not supported

    def _load_html_data(self, file):
        content = ""
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        crawler = Crawler()
        soup = crawler.parse(content)
        all_text = crawler.clean_text(soup.select_one("body").text)
        main_content = ""
        for element_name in ["main", "container"]:
            main_block = None
            if soup.select(f".{element_name}"):
                main_block = soup.select(f".{element_name}")
            elif soup.select(f"#{element_name}"):
                main_block = soup.select(f"#{element_name}")
            if main_block:
                for element in main_block:
                    text = crawler.clean_text(element.text)
                    if text not in main_content:
                        main_content += f"\n{text}"
                main_content = crawler.clean_text(main_content)
        main_content = all_text if main_content == "" else main_content
        main_content = main_content.replace("\n", "")
        main_content = main_content.replace("\n\n", "")
        main_content = re.sub(r"\s+", " ", main_content)
        return main_content
