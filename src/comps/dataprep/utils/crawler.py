# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import multiprocessing
import re
import requests
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class Crawler:
    def __init__(self, pool=None):
        if pool:
            assert isinstance(pool, (str, list, tuple)), "url pool should be str, list or tuple"
        self.pool = pool
        self.headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        }
        self.fetched_pool = set()

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

    def fetch(self, url, headers=None, max_times=5):
        if not headers:
            headers = self.headers
        while max_times:
            if not url.startswith("http") or not url.startswith("https"):
                url = "http://" + url
            logger.info("start fetch %s...", url)
            try:
                response = requests.get(url, headers=headers, verify=True)
                if response.status_code != 200:
                    logger.info("fail to fetch %s, response status code: %s", url, response.status_code)
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
