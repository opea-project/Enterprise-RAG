# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import List
import uuid
from comps.cores.mega.logger import get_opea_logger
from comps.cores.utils.utils import sanitize_env
from comps.dataprep.utils.splitter import Splitter
from fastapi import UploadFile
from comps.cores.proto.docarray import TextDoc
from comps.dataprep.utils.crawler import Crawler

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class TimeoutError(Exception):
    pass


async def save_file_to_local_disk(file: UploadFile) -> str:
    upload_folder = sanitize_env(os.getenv('UPLOAD_PATH', '/tmp/opea_upload'))

    if not os.path.exists(upload_folder):
        Path(upload_folder).mkdir(parents=True, exist_ok=True)

    save_path = Path(os.path.join(upload_folder, file.filename))
    with save_path.open("wb") as fout:
        try:
            content = await file.read()
            fout.write(content)
            fout.close
        except Exception as e:
            logger.exception(f"Write file failed when presisting files. Exception: {e}")
            raise

    return save_path


async def save_link_to_local_disk(link_list: List[str]) -> List[str]:
    upload_folder = sanitize_env(os.getenv('UPLOAD_PATH', '/tmp/opea_upload'))
    if not os.path.exists(upload_folder):
        Path(upload_folder).mkdir(parents=True, exist_ok=True)

    data_collection = parse_html(link_list)  # crawl through the page

    save_paths = []
    for data, meta in data_collection:
        doc_id = str(uuid.uuid4()) + ".txt"
        save_path = Path(os.path.join(upload_folder, doc_id))
        with save_path.open("w") as fout:
            try:
                fout.write(data)
                fout.close
                save_paths.append(save_path)
            except Exception as e:
                logger.exception(f"Write file failed while presisting links. Exception: {e}")
                raise
    return save_paths


async def parse_files(files: List[UploadFile], splitter: Splitter) -> List[TextDoc]:
    parsed_texts: List[TextDoc] = []

    for file in files:
        # if files have to be persisted internally
        try:
            path = await save_file_to_local_disk(file)
            saved_path = str(path.resolve())
            logger.info(f"saved file {file.filename} to {saved_path}")

            metadata = {
                'path': saved_path,
                'timestamp': time.time()
            }

            chunks = splitter.split(saved_path)
            for chunk in chunks:
                parsed_texts.append(TextDoc(text=chunk, metadata=metadata))

        except Exception as e:
            logger.exception(e)
            raise e

    return parsed_texts


async def parse_links(links: List[str], splitter: Splitter) -> List[TextDoc]:
    parsed_texts: List[TextDoc] = []

    for link in links:
        try:
            paths = await save_link_to_local_disk([link])
            for path in paths:
                saved_path = str(path.resolve())
                logger.info(f"saved link {link} to {saved_path}")

                metadata = {
                    'path': saved_path,
                    'url': link,
                    'timestamp': time.time()
                }

                chunks = splitter.split(saved_path)
                for chunk in chunks:
                    parsed_texts.append(TextDoc(text=chunk, metadata=metadata))

        except Exception as e:
            logger.exception(e)
            raise e

    return parsed_texts


def uni_pro(text):
    """Check if the character is ASCII or falls in the category of non-spacing marks."""
    normalized_text = unicodedata.normalize("NFKD", text)
    filtered_text = ""
    for char in normalized_text:
        if ord(char) < 128 or unicodedata.category(char) == "Mn":
            filtered_text += char
    return filtered_text


def load_html_data(url):
    crawler = Crawler()
    res = crawler.fetch(url)
    if res is None:
        return None
    soup = crawler.parse(res.text)
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
    main_content = uni_pro(main_content)
    main_content = re.sub(r"\s+", " ", main_content)
    return main_content


def parse_html(input):
    """Parse the uploaded file."""
    chunks = []
    for link in input:
        if re.match(r"^https?:/{2}\w.+$", link):
            content = load_html_data(link)
            if content is None:
                continue
            chunk = [content.strip(), link]
            chunks.append(chunk)
        else:
            logger.info("The given link/str {} cannot be parsed.".format(link))

    return chunks
