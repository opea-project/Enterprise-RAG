#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import asyncio
import concurrent
import logging
import os
import shutil
import time
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any

import aiohttp
import requests

from tests.e2e.helpers.api_request_helper import ApiRequestHelper
from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR, ERAG_DOMAIN

logger = logging.getLogger(__name__)

LINK_DELETION_TIMEOUT_S = 60
FILE_UPLOAD_TIMEOUT_S = 10800  # 3 hours
LINK_UPLOAD_TIMEOUT = 300  # 5 minutes
DATAPREP_STATUS_FLOW = ["uploaded", "processing", "text_extracting", "text_compression", "text_splitting", "embedding", "late_chunking", "ingested"]
EDP_API_PATH = f"{ERAG_DOMAIN}/api/v1/edp"


class EdpHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper, bucket_name=None):
        super().__init__(keycloak_helper=keycloak_helper)
        if bucket_name:
            # Explicit bucket provided - used outside e2e tests (e.g., accuracy evaluator scripts)
            # where cfg is not populated
            self.default_bucket = bucket_name
        else:
            # Auto-detect bucket from RAG deployment - used in e2e tests where cfg contains
            # the actual deployment configuration loaded from config.yaml
            if cfg.get("edp") is None or cfg.get("edp").get("enabled") is not True:
                self.available_buckets = []
                self.default_bucket = None
            else:
                self.available_buckets = self.list_buckets().json().get("buckets")
                # Use the first bucket that is not read-only as the default bucket
                self.default_bucket = next((bucket for bucket in self.available_buckets if "read-only" not in bucket), None)
                logger.debug(f"Setting {self.default_bucket} as a default bucket from the list of available buckets: "
                                f"{self.available_buckets}")


    def list_buckets(self, as_user=False):
        """Call /api/list_buckets endpoint"""
        response = requests.get(
            url=f"{EDP_API_PATH}/list_buckets",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def list_links(self, as_user=False):
        """Call /api/links endpoint"""
        response = requests.get(
            url=f"{EDP_API_PATH}/links",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def upload_links(self, payload, as_user=False):
        """Make post call to /api/links endpoint with the given payload"""
        logger.info(f"Attempting to upload links using the following payload: {payload}")
        response = requests.post(
            url=f"{EDP_API_PATH}/links",
            headers=self.get_headers(as_user),
            json=payload,
            verify=False
        )
        return response

    def delete_link(self, link_uuid, as_user=False):
        """Delete a link by its id"""
        logger.info(f"Deleting link with id: {link_uuid}")
        response = requests.delete(
            url=f"{EDP_API_PATH}/link/{link_uuid}",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def delete_link_by_url(self, link_url):
        """Delete a link by its URL"""
        links = self.list_links()
        for item in links.json():
            if item["uri"] == link_url:
                logger.info(f"Deleting link with id: {link_url}")
                return self.delete_link(item["id"])
        logger.warning(f"Link with URL: {link_url} not found. Nothing to delete.")

    def wait_for_link_upload(self, link_uri, desired_status, timeout=LINK_UPLOAD_TIMEOUT):
        """Wait for the link to be uploaded and have the desired status"""
        sleep_interval = 10
        start_time = time.time()
        while time.time() < start_time + timeout:
            current_links = self.list_links().json()

            link = next((item for item in current_links if item['uri'] == link_uri), None)
            if not link:
                raise UploadTimeoutException(f"Link {link_uri} not found in the list of links")

            if self._status_reached(link.get("status"), desired_status):
                logger.info(f"Link {link_uri} has status {desired_status}. "
                      f"Elapsed time: {round(time.time() - start_time, 1)}s")
                return link_uri
            else:
                logger.info(f"Waiting {sleep_interval}s for link {link_uri} to have status '{desired_status}'. "
                      f"Current status: {link.get('status')}")
                time.sleep(sleep_interval)

        raise UploadTimeoutException(
            f"Timed out after {timeout} seconds while waiting for the link to be uploaded")

    def list_files(self, as_user=False):
        """Call /api/files endpoint"""
        response = requests.get(
            url=f"{EDP_API_PATH}/files",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def generate_presigned_url(self, object_name, method="PUT", bucket=None, as_user=False):
        """Generate a presigned URL for the given object name"""
        if not bucket:
            bucket = self.default_bucket
        logger.info(f"Generating presigned URL for object: {object_name} and bucket: {bucket}")
        payload = {
            "bucket_name": bucket,
            "object_name": object_name,
            "method": method
        }
        response = requests.post(
            url=f"{EDP_API_PATH}/presignedUrl",
            headers=self.get_headers(as_user),
            json=payload,
            verify=False
        )
        return response

    async def generate_presigned_url_async(self, session, object_name, method="PUT", bucket=None) -> str:
        """generate_presigned_url() intended to use for multiple async calls."""
        logger.debug(f"Generating presigned URL for {method} object: {object_name} and bucket: {bucket}")
        payload = {
            "bucket_name": bucket,
            "object_name": object_name,
            "method": method
        }
        async with session.post(
                f"{EDP_API_PATH}/presignedUrl",
                headers=self.get_headers(),
                json=payload,
                ssl=False
        ) as response:
            if response.status >= 400:
                response_text = await response.text()
                logger.error(f"Failed to generate presigned URL for object {object_name}:\n"
                             f"{response.status} - {response_text}")
                raise UploadFailedException()

            response_url = (await response.json()).get("url")
            logger.info(f"Got presigned url for {object_name}.")
            return response_url

    async def generate_many_presigned_urls(self, objects_names: set, method="PUT", bucket=None) -> dict[str,str]:
        """Generate a presigned URL for the given objects' names

        Returns dictionary with url per object name:

        ```
        {
            obj_name0: presgined_url0,
            ...
        }
        ```
        """
        if not bucket:
            bucket = self.default_bucket

        presigned_urls = dict()
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.generate_presigned_url_async(session, object_name, method=method, bucket=bucket)
                for object_name in objects_names
            ]
            urls = await asyncio.gather(*tasks)
            presigned_urls = dict(zip(objects_names, urls))

        return presigned_urls

    def cancel_processing_task(self, file_uuid, as_user=False):
        """Cancel the processing task for the given file UUID"""
        logger.info(f"Cancelling task for file with id: {file_uuid}")
        response = requests.delete(
            url=f"{EDP_API_PATH}/file/{file_uuid}/task",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def extract_text(self, file_uuid, as_user=False):
        """Extract text for the given file UUID"""
        logger.info(f"Extracting text for file with id: {file_uuid}")
        response = requests.post(
            f"{EDP_API_PATH}/file/{file_uuid}/extract",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def _open_and_send_file(self, file_path, presigned_url):
        logger.debug(f"Attempting to upload file {file_path} using presigned URL")
        try:
            with open(file_path, 'rb') as f:
                response = requests.put(presigned_url, data=f, verify=False)
            logger.info(f"Upload {file_path} completed")
            return response
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

    def upload_file(self, file_path, presigned_url):
        """Upload a file using the presigned URL"""
        return self._open_and_send_file(file_path, presigned_url)

    def upload_files_in_parallel(self, files_dir, file_names):
        files_info = []

        presigned_urls = asyncio.run(self.generate_many_presigned_urls(set(file_names)))
        for name in file_names:
            path = os.path.join(files_dir, name)
            file_info = {"path": path, "presigned_url": presigned_urls[name]}
            files_info.append(file_info)

        results = []
        logger.debug(f"Start {len(file_names)} threads for file uploading.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(file_names)) as executor:
            futures = [executor.submit(self._open_and_send_file, file_info['path'], file_info['presigned_url']) for file_info in files_info]

            try:
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
            except Exception as e:
                msg = f"Caugh an exception in a thread during file upload: {str(e)}"
                for f in futures:
                    f.cancel()
                logger.critical(msg)
                raise RuntimeError(msg)

        return results

    def retrieve(self, payload: dict[str, Any]) -> requests.Response:
        """Make post call to /api/v1/edp/retrieve endpoint with the given payload"""
        logger.debug(f"Attempting to retrieve documents using the following payload: {payload}")
        response = requests.post(
            url=f"{EDP_API_PATH}/retrieve",
            headers=self.get_headers(),
            json=payload,
            verify=False
        )
        return response

    def wait_for_file_upload(self, filename, desired_status, timeout=FILE_UPLOAD_TIMEOUT_S):
        """Wait for the file to be uploaded and have the desired status"""
        file_status = ""
        sleep_interval = 10
        start_time = time.time()
        while time.time() < start_time + timeout:
            files = self.list_files().json()
            file_found = False
            for file in files:
                if file.get("object_name") == filename:
                    file_found = True
                    if file.get("status") == "error" and desired_status != "error":
                        last_status_message = "no previous status known."
                        if file_status:
                            last_status_message = f"last known status {file_status}."
                        raise FileStatusException(f"File {filename} has status {file.get('status')}, {last_status_message}")
                    file_status = file.get("status")
                    if self._status_reached(file_status, desired_status):
                        logger.info(f"File {filename} has status {desired_status}. "
                              f"Elapsed time: {round(time.time() - start_time, 1)}s")
                        return file
                    else:
                        logger.info(f"Waiting {sleep_interval}s for file {filename} to have status '{desired_status}'. "
                              f"Current status: {file_status}")
                        time.sleep(sleep_interval)
                        break
            if not file_found:
                logger.warning(f"File {filename} is not present in the list of files")

        raise UploadTimeoutException(
            f"Timed out after {timeout} seconds while waiting for the file to be uploaded")

    def wait_for_all_files_ingestion(self, filenames: set, timeout=FILE_UPLOAD_TIMEOUT_S) -> None:
        """Wait for all files to be uploaded and ingested.

        Uses sets logic for quick check for object readiness.
        Expressions like filenames & filenames_all == filenames are way to continue if there are old files in edp.
        """

        SLEEP_INTERVAL = 10
        MAX_RDP_REGISTER_RETRIES = 30  # How many times wait until edp pick files from bucket

        start_time = time.time()
        all_ingested = False
        filenames_ingested = set()
        fails_remaining = MAX_RDP_REGISTER_RETRIES
        while time.time() < start_time + timeout:
            edp_files = self.list_files().json()
            filenames_in_edp = set([f["object_name"] for f in edp_files])
            # all files from filenames should be present in the EDP
            if not (filenames & filenames_in_edp == filenames):
                if fails_remaining > 0:

                    fails_remaining -= 1
                    missing_files = '\n'.join(list(filenames - filenames_in_edp))
                    logger.warning(f"Not all files are present in the EDP:\n{missing_files}")
                    logger.warning(f"Will wait {SLEEP_INTERVAL}s.. Remaining checks: {fails_remaining}/{MAX_RDP_REGISTER_RETRIES}")
                    time.sleep(SLEEP_INTERVAL)
                    continue
                else:
                    missing_files = '\n'.join(list(filenames - filenames_in_edp))
                    raise RuntimeError(f"Not all files are present in the EDP:\n{missing_files}, failed {MAX_RDP_REGISTER_RETRIES} times.")

            filenames_ingested = set([f["object_name"] for f in edp_files if f["status"] == "ingested"])
            if filenames & filenames_ingested == filenames:
                logger.info(f"All files have been ingested. Elapsed time: {round(time.time() - start_time, 1)}s")
                all_ingested = True
                break
            else:
                waiting_time = time.time() - start_time
                waiting_h = int(waiting_time // 3600)
                waiting_m = int((waiting_time % 3600) // 60)
                waiting_s = int(waiting_time % 60)

                logger.debug(f"(Total: {waiting_h:02d}:{waiting_m:02d}:{waiting_s:02d}) Waiting {SLEEP_INTERVAL}s for all files to be ingested. Still processing: {', '.join(list(filenames - filenames_ingested))}")
                time.sleep(SLEEP_INTERVAL)

        if not all_ingested:
            not_ingested = filenames - filenames_ingested
            raise UploadTimeoutException(
                f"Timed out after {timeout} seconds while waiting for the files to be ingested:" + "\n- ".join(not_ingested)
            )

    def upload_file_and_wait_for_ingestion(self, file_path, bucket=None):
        response = self.generate_presigned_url(file_path, bucket=bucket)
        response = self.upload_file(file_path, response.json().get("url"))
        assert response.status_code == 200
        return self.wait_for_file_upload(file_path, "ingested", timeout=180)

    @contextmanager
    def ephemeral_upload(self, file_path, desired_status="ingested", bucket=None, timeout=180):
        """
        Upload a file, wait for desired status, yield file info, and delete the file after context exits.
        """
        filename = os.path.basename(file_path)
        response = self.generate_presigned_url(filename, bucket=bucket)
        presigned_url = response.json().get("url")
        self.upload_file(file_path, presigned_url)
        file_info = self.wait_for_file_upload(filename, desired_status, timeout=timeout)
        try:
            yield file_info
        finally:
            filename = file_info.get("object_name")
            logger.debug(f"Deleting temporary file: {filename}")
            response = self.generate_presigned_url(filename, method="DELETE", bucket=bucket)
            url = response.json().get("url")
            self.delete_file(url)

    @contextmanager
    def substitute_file(self, to_substitute, substitution):
        """Temporarily substitute file and yield. Rollback file after context manager exits."""

        file_path_to_substitute = os.path.join(DATAPREP_UPLOAD_DIR, to_substitute)
        file_path_substitution = os.path.join(DATAPREP_UPLOAD_DIR, substitution)
        backup_path = file_path_to_substitute + ".backup"
        try:
            # Rename the original file to create a backup
            os.rename(file_path_to_substitute, backup_path)

            # Copy the substitution file to the original file's path
            shutil.copy(str(file_path_substitution), str(file_path_to_substitute))

            yield

        finally:
            os.remove(file_path_to_substitute)
            shutil.copy(str(backup_path), str(file_path_to_substitute))
            os.remove(backup_path)

    def delete_file(self, presigned_url):
        """Delete a file using the presigned URL"""
        logger.info("Attempting to delete file using presigned URL")
        return requests.delete(presigned_url, verify=False)

    async def delete_many_files(self, presigned_urls: list[str]) -> None:
        """Delete files asynchronously."""
        async with aiohttp.ClientSession() as session:
            for presigned_url in presigned_urls:
                async with session.delete(presigned_url, ssl=False) as response:
                    response.raise_for_status()

    def _status_reached(self, status, desired_status):
        """
        Check if the status is at least the desired status, for example:
        _status_reached("ingested", "dataprep") -> True
        """
        if desired_status == "error":
            return status == "error"
        return DATAPREP_STATUS_FLOW.index(status) >= DATAPREP_STATUS_FLOW.index(desired_status)

    @contextmanager
    def temp_txt_file(self, size, prefix):
        """Create a temporary *.txt file of a given size"""
        logger.info(f"Creating a temporary *.txt file of size {size}MB")
        with NamedTemporaryFile(delete=True, mode='w+', prefix=prefix, suffix=".txt") as temp_file:
            size_mb = size * 1024 * 1024
            self.fill_in_file(temp_file, size_mb)
            yield temp_file

    def upload_test_file(self, size, prefix, status, timeout):
        """Create a temporary file, upload it and wait for the file to reach the desired status"""
        with self.temp_txt_file(size=size, prefix=prefix) as temp_file:
            file_basename = os.path.basename(temp_file.name)
            response = self.generate_presigned_url(file_basename)
            self.upload_file(temp_file.name, response.json().get("url"))
        return self.wait_for_file_upload(file_basename, status, timeout=timeout)

    def fill_in_file(self, temp_file, size):
        """Write data to the temp file until we reach the desired size"""
        chunk_size = 1024   # Write in chunks of 1KB
        current_size = 0
        while current_size < size:
            chunk = 'A' * chunk_size
            temp_file.write(chunk)
            current_size += chunk_size
            temp_file.flush()
        logger.info(f"Temporary file created at: {temp_file.name}")


class DeleteTimeoutException(Exception):
    pass


class FileStatusException(Exception):
    pass


class UploadTimeoutException(Exception):
    pass


class UploadFailedException(Exception):
    pass
