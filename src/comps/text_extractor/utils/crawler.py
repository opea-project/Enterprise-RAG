# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import multiprocessing
import re
import requests
import os
import json
import uuid
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from comps.cores.mega.logger import get_opea_logger
from pathvalidate import FileNameSanitizer

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class Crawler:
    def __init__(self, pool=None):
        if pool:
            assert isinstance(pool, (str, list, tuple)), "url pool should be str, list or tuple"
        self.pool = pool
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i"
        }
        self.fetched_pool = set()
        self.max_times = int(os.getenv("CRAWLER_MAX_RETRIES", "1"))
        self.timeout = int(os.getenv("CRAWLER_HTTP_TIMEOUT", "60"))
        self.max_file_size = int(os.getenv("CRAWLER_MAX_FILE_SIZE_MB", "128")) * 1024 * 1024  # X MB in bytes
        env_headers =  os.getenv("CRAWLER_HEADERS")
        if env_headers:
            try:
                self.headers = json.loads(env_headers)
            except (TypeError, json.JSONDecodeError):
                self.headers = None
        else:
            self.headers = default_headers
        
    def download_file(self, url, upload_folder):
        max_times = self.max_times
        while max_times:
            url = urlparse(url)
            if url.scheme == "":
                url = url._replace(scheme="http")

            logger.info("start fetch %s...", urlunparse(url))
            try:
                response = requests.get(
                    urlunparse(url),
                    headers=self.headers,
                    verify=True,
                    allow_redirects=True,
                    stream=True,
                    timeout=(10, self.timeout) # Tuple timeout: (connect, read)
                )
                logger.debug("--------------------------------")
                logger.debug(f"Request Headers for {urlunparse(url)}:")
                for key, value in response.request.headers.items():
                    logger.debug(f"{key}: {value}")
                logger.debug("--------------------------------")
                logger.debug(f"Response Headers for {urlunparse(url)}:")
                for key, value in response.headers.items():
                    logger.debug(f"{key}: {value}")
                logger.debug("--------------------------------")
                logger.debug(f"Response Status Code for {urlunparse(url)}: {response.status_code}")
                logger.debug("--------------------------------")
                logger.debug(f"Response Content for {urlunparse(url)}: {response.text}")

                if response.status_code != 200:
                    logger.error("fail to fetch %s, response status code: %s", urlunparse(url), response.status_code)
                    response.raise_for_status()
                else:  # Save file
                    filename = ""
                    if "Content-Disposition" in response.headers.keys():
                        match = re.findall("filename=(.+)", response.headers["Content-Disposition"])
                        if len(match) > 0:
                            filename = match[0]

                    if filename == "":
                        if url.path == "":
                            filename = "index.html"
                        else:
                            filename = url.path.split("/")[-1] or 'index.html' # safe default

                    # Sanitize filename
                    filename = filename.replace('"', "")
                    filename = filename.replace("'", "")
                    filename = filename.replace("..", "")
                    filename = FileNameSanitizer().sanitize(filename)

                    extension = filename.split(".")[-1] if "." in filename else "html"
                    temp_filename = f"{str(uuid.uuid4())}.{extension}"
                    file_path = Path(os.path.join(upload_folder, temp_filename))
                    content_type = re.findall("([a-z]+/[a-z]+)", response.headers.get("Content-Type"))
                    content_type = content_type[0] if len(content_type) > 0 else ""
                    logger.info(f"Downloaded Content-Type(s): {content_type}")

                    downloaded_size = 0
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                downloaded_size += len(chunk)
                                if downloaded_size > self.max_file_size:
                                    f.close()
                                    file_path.unlink()
                                    raise ValueError(f"Downloaded file exceeds the maximum allowed size of {self.max_file_size / (1024 * 1024):.0f} MB: {urlunparse(url)}")
                                f.write(chunk)

                    logger.info(f"Saved file {temp_filename} from {urlunparse(url)}")

                    return {
                        "url": urlunparse(url),
                        "filename": filename,
                        "file_path": str(file_path.resolve()),
                        "content_type": content_type
                    }
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.ProxyError) as e:
                logger.error(f"HTTP error while fetching {urlunparse(url)}: {e}")
                raise
            except Exception as e:
                logger.exception(f"Failed to fetch {urlunparse(url)}, caused by {e}")
                raise Exception(e)
            max_times -= 1

    def get_sublinks(self, soup):
        sublinks = []
        for links in soup.find_all("a"):
            sublinks.append(str(links.get("href")))
        return sublinks

    def get_hyperlink(self, soup, base_url):
        sublinks = []
        for links in soup.find_all("a"):
            link = str(links.get("href"))
            if link.startswith("#") or link is None or link == "None":
                continue
            suffix = link.split("/")[-1]
            if "." in suffix and suffix.split(".")[-1] not in ["html", "htmld"]:
                continue
            link_parse = urlparse(link)
            base_url_parse = urlparse(base_url)
            if link_parse.path == "":
                continue
            if link_parse.netloc != "":
                # keep crawler works in the same domain
                if link_parse.netloc != base_url_parse.netloc:
                    continue
                sublinks.append(link)
            else:
                sublinks.append(
                    urlunparse(
                        (
                            base_url_parse.scheme,
                            base_url_parse.netloc,
                            link_parse.path,
                            link_parse.params,
                            link_parse.query,
                            link_parse.fragment,
                        )
                    )
                )
        return sublinks

    def fetch(self, url, headers=None):
        max_times = self.max_times
        if not headers:
            headers = self.headers
        while max_times:
            if not url.startswith("http") or not url.startswith("https"):
                url = "http://" + url
            logger.info("start fetch %s...", url)
            try:
                response = requests.get(url, headers=headers, verify=True, timeout=(10, self.timeout))  # Tuple timeout: (connect, read)
                if response.status_code != 200:
                    logger.error("fail to fetch %s, response status code: %s", url, response.status_code)
                else:
                    return response
            except Exception as e:
                logger.exception("fail to fetch %s, caused by %s", url, e)
                raise Exception(e)
            max_times -= 1
        # TODO: decide whether the dataprep should continue if one url fails
        logger.error(f"fail to fetch {url}, max times reached, response status code: {response.status_code}")
        raise Exception(f"fail to fetch {url}, max times reached, response status code: {response.status_code}")

    def process_work(self, sub_url, work):
        response = self.fetch(sub_url)
        if response is None:
            return []
        self.fetched_pool.add(sub_url)
        soup = self.parse(response.text)
        base_url = self.get_base_url(sub_url)
        sublinks = self.get_hyperlink(soup, base_url)
        if work:
            work(sub_url, soup)
        return sublinks

    def crawl(self, pool, work=None, max_depth=10, workers=10):
        url_pool = set()
        for url in pool:
            base_url = self.get_base_url(url)
            response = self.fetch(url)
            soup = self.parse(response.text)
            sublinks = self.get_hyperlink(soup, base_url)
            self.fetched_pool.add(url)
            url_pool.update(sublinks)
            depth = 0
            while len(url_pool) > 0 and depth < max_depth:
                logger.info("current depth %s...", depth)
                mp = multiprocessing.Pool(processes=workers)
                results = []
                for sub_url in url_pool:
                    if sub_url not in self.fetched_pool:
                        results.append(mp.apply_async(self.process_work, (sub_url, work)))
                mp.close()
                mp.join()
                url_pool = set()
                for result in results:
                    sublinks = result.get()
                    url_pool.update(sublinks)
                depth += 1

    def parse(self, html_doc):
        soup = BeautifulSoup(html_doc, "lxml")
        return soup

    def download(self, url, file_name):
        logger.info("download %s into %s...", url, file_name)
        try:
            r = requests.get(url, stream=True, headers=self.headers, verify=True)
            f = open(file_name, "wb")
            for chunk in r.iter_content(chunk_size=512):
                if chunk:
                    f.write(chunk)
        except Exception as e:
            logger.exception("fail to download %s, caused by %s", url, e)

    def get_base_url(self, url):
        result = urlparse(url)
        return urlunparse((result.scheme, result.netloc, "", "", "", ""))

    def clean_text(self, text):
        text = text.strip().replace("\r", "\n")
        text = re.sub(" +", " ", text)
        text = re.sub("\n+", "\n", text)
        text = text.split("\n")
        return "\n".join([i for i in text if i and i != " "])
