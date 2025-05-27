# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import re
import time
from pathlib import Path
from typing import List
from comps.cores.mega.logger import get_opea_logger
from comps.cores.utils.utils import sanitize_env
from comps.dataprep.utils.splitter import Splitter
from fastapi import UploadFile
from comps.cores.proto.docarray import TextDoc
from comps.dataprep.utils.crawler import Crawler

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class TimeoutError(Exception):
    pass


def save_file_to_local_disk(file: UploadFile) -> str:
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


def save_link_to_local_disk(url: str) -> dict:
    upload_folder = sanitize_env(os.getenv('UPLOAD_PATH', '/tmp/opea_upload'))
    if not os.path.exists(upload_folder):
        Path(upload_folder).mkdir(parents=True, exist_ok=True)
        # Set the directory permission to 700 (owner: rwx)
        os.chmod(upload_folder, 0o700)
    crawler = Crawler()
    return crawler.download_file(url, upload_folder) 


def parse_files(files: List[UploadFile], splitter: Splitter) -> List[TextDoc]:
    parsed_texts: List[TextDoc] = []

    for file in files:
        saved_path = ""
        # if files have to be persisted internally
        try:
            path = save_file_to_local_disk(file)
            saved_path = str(path.resolve())
            logger.info(f"saved file {file.filename} to {saved_path}")

            metadata = {
                'filename': file.filename,
                'timestamp': time.time()
            }

            chunks = splitter.split(saved_path)
            for chunk in chunks:
                parsed_texts.append(TextDoc(text=chunk, metadata=metadata))
        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            if saved_path != "" and os.path.exists(saved_path) and not os.path.isdir(saved_path):
                logger.info(f"Removed {saved_path} after processing")
                os.remove(saved_path)

    return parsed_texts


def parse_links(links: List[str], splitter: Splitter) -> List[TextDoc]:
    parsed_texts: List[TextDoc] = []

    for link in links:
        saved_path = ""
        if not re.match(r"^https?:/{2}\w.+$", link):
            logger.info(f"The given link/str {link} cannot be parsed.")
            raise ValueError(f"The given link/str {link} cannot be parsed.")

        try:
            # { url, filename, file_path, content_type }
            parsed_link = save_link_to_local_disk(link)
            saved_path = parsed_link['file_path']

            metadata = {
                'url': parsed_link['url'],
                'filename': parsed_link['filename'],
                'timestamp': time.time()
            }

             # User parser if file type is html
            if 'html' in parsed_link['content_type']:
                logger.info(f"Parsing {parsed_link['file_path']} as HTML")
                content = load_html_data(parsed_link['file_path'])
                with open(parsed_link['file_path'], "w", encoding="utf-8") as f:
                    f.write(content)

            chunks = splitter.split(saved_path)
            for chunk in chunks:
                parsed_texts.append(TextDoc(text=chunk, metadata=metadata))

        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            if saved_path != "" and os.path.exists(saved_path) and not os.path.isdir(saved_path):
                logger.info(f"Removed {saved_path} after processing")
                os.remove(saved_path)

    return parsed_texts

def load_html_data(file):
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
