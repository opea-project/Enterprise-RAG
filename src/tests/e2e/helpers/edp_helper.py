#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
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
from tests.e2e.validation.constants import DATAPREP_UPLOAD_DIR

logger = logging.getLogger(__name__)

LINK_DELETION_TIMEOUT_S = 60
FILE_UPLOAD_TIMEOUT_S = 300  # 5 minutes
FILE_DELETION_TIMEOUT_S = 120  # 2 minutes
LINK_UPLOAD_TIMEOUT = 300  # 5 minutes
DATAPREP_STATUS_FLOW = ["uploaded", "processing", "text_extracting", "text_compression", "text_splitting", "embedding", "late_chunking", "ingested"]


class EdpHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper, bucket_name=None):
        super().__init__(keycloak_helper=keycloak_helper)
        self.edp_api_path = f"https://{cfg.get('FQDN')}/api/v1/edp"
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
            url=f"{self.edp_api_path}/list_buckets",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def list_sites(self):
        """Call api/v1/edp/sharepoint/sites"""
        response = requests.get(
            url=f"{self.edp_api_path}/sharepoint/sites",
            headers=self.get_headers(),
            verify=False
        )
        return response

    @staticmethod
    def _extract_site_name(site_url_or_name):
        """Extract the short site name from a full SharePoint URL.
        E.g. 'https://intel.sharepoint.com/sites/test-site' -> 'test-site'
        If the input is already a short name (no '/'), return it as-is.
        """
        if "/" in site_url_or_name:
            return site_url_or_name.rstrip("/").rsplit("/", 1)[-1]
        return site_url_or_name

    def get_site_id_by_name(self, site_name):
        """Get site ID by site name or URL. Return None if site with the given name is not found."""
        short_name = self._extract_site_name(site_name)
        sites = self.list_sites()
        site_id = next((site["id"] for site in sites.json().get("sites", []) if site["name"] == short_name), None)
        if not site_id:
            logger.warning(f"Site with name {short_name} not found.")
        return site_id

    def connect_site(self, site_url):
        """Connect the site with the given URL or name.
        If a short name is provided (e.g. from restore logic), it is not sent as a URL.
        """
        logger.info(f"Connecting site: {site_url}")
        payload = {"site_url": site_url}
        response = requests.post(
            url=f"{self.edp_api_path}/sharepoint/sites",
            headers=self.get_headers(),
            json=payload,
            verify=False
        )
        return response

    def disconnect_site(self, site_name, site_id=None):
        """Disconnect the site with the given name. If there is no connected site with such name, return 404 response"""
        if not site_id:
            site_id = self.get_site_id_by_name(site_name)
        if not site_id:
            logger.warning(f"Site with name {site_name} not found. Returning 404.")
            response = requests.Response()
            response.status_code = 404
            return response
        logger.info(f"Disconnecting site with id: {site_id} and name: {site_name}")

        response = requests.delete(
            url=f"{self.edp_api_path}/sharepoint/sites/{site_id}",
            headers=self.get_headers(),
            verify=False
        )

        return response

    def sync_sharepoint(self, as_user=False) -> requests.Response:
        """
        Trigger a SharePoint sync via the EDP API.
        POST /api/v1/edp/sharepoint/sync
        """
        url = f"{self.edp_api_path}/sharepoint/sync"
        response = requests.post(
            url,
            headers=self.get_headers(as_user),
            verify=False
        )
        logger.info(f"SharePoint sync triggered. Status: {response.status_code}")
        return response

    def upload_to_sharepoint(self, site_name, file_path, site_id=None, as_user=False) -> requests.Response:
        """
        Upload a file to a connected SharePoint site via the EDP API.
        POST /api/v1/edp/sharepoint/files
        """
        url = f"{self.edp_api_path}/sharepoint/files"
        if not site_id:
            site_id = self.get_site_id_by_name(site_name)
        params = {"site_id": site_id}
        headers = self.get_headers(as_user)
        headers.pop('Content-Type', None)

        with open(file_path, 'rb') as f:
            file_name = os.path.basename(file_path)
            files = {'file': (file_name, f, 'text/plain')}
            response = requests.post(
                url,
                params=params,
                headers=headers,
                files=files,
                verify=False
            )
        logger.info(f"File {file_name} upload to SharePoint site {site_name} (site_id: {site_id}) attempted. Status: {response.status_code}")
        return response

    def remove_from_sharepoint(self, site_name, object_name) -> requests.Response:
        """
        Delete a file from a connected SharePoint site via the EDP API.
        DELETE /api/v1/edp/sharepoint/files
        """
        url = f"{self.edp_api_path}/sharepoint/files"
        payload = {
            "site_name": self._extract_site_name(site_name),
            "object_name": object_name
        }
        response = requests.delete(
            url,
            headers=self.get_headers(),
            json=payload,
            verify=False
        )
        logger.info(f"File {object_name} removal from SharePoint site {site_name} attempted. Status: {response.status_code}")
        return response

    def get_file_url(self, site_name, object_name) -> requests.Response:
        """
        Fetch a URL used to download an uploaded file from a SharePoint site via the EDP API.
        POST /api/v1/edp/sharepoint/file-url
        """
        url = f"{self.edp_api_path}/sharepoint/file-url"
        payload = {
            "site_name": self._extract_site_name(site_name),
            "object_name": object_name
        }
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload,
            verify=False
        )
        logger.info(f"File URL request for {object_name} on site {site_name}. Status: {response.status_code}")
        return response

    def list_links(self, as_user=False):
        """Call /api/links endpoint"""
        response = requests.get(
            url=f"{self.edp_api_path}/links",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def upload_links(self, payload, as_user=False):
        """Make post call to /api/links endpoint with the given payload"""
        logger.info(f"Attempting to upload links using the following payload: {payload}")
        response = requests.post(
            url=f"{self.edp_api_path}/links",
            headers=self.get_headers(as_user),
            json=payload,
            verify=False
        )
        return response

    def delete_link(self, link_uuid, as_user=False):
        """Delete a link by its id"""
        logger.info(f"Deleting link with id: {link_uuid}")
        response = requests.delete(
            url=f"{self.edp_api_path}/link/{link_uuid}",
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
            url=f"{self.edp_api_path}/files",
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
            url=f"{self.edp_api_path}/presignedUrl",
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
                f"{self.edp_api_path}/presignedUrl",
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
            url=f"{self.edp_api_path}/file/{file_uuid}/task",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def extract_text(self, file_uuid, as_user=False):
        """Extract text for the given file UUID"""
        logger.info(f"Extracting text for file with id: {file_uuid}")
        response = requests.post(
            f"{self.edp_api_path}/file/{file_uuid}/extract",
            headers=self.get_headers(as_user),
            verify=False
        )
        return response

    def _open_and_send_file(self, file_path, presigned_url, as_user=False):
        logger.debug(f"Attempting to upload file {file_path} using presigned URL")
        try:
            headers = {}
            if (cfg.get("edp", {}).get("storageType") == "seaweedfs"
                    and cfg.get("edp", {}).get("rbac", {}).get("enabled", False)):
                if "authorization" in self.get_headers(as_user):
                    headers["authorization"] = self.get_headers(as_user)["authorization"]

            with open(file_path, 'rb') as f:
                response = requests.put(presigned_url, data=f, verify=False, headers=headers)
            logger.info(f"Upload {file_path} completed")
            return response
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

    def upload_file(self, file_path, presigned_url, as_user=False):
        """Upload a file using the presigned URL"""
        return self._open_and_send_file(file_path, presigned_url, as_user=as_user)

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
            url=f"{self.edp_api_path}/retrieve",
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
                obj_name = file.get("object_name", "")
                if filename == obj_name or obj_name.endswith("/" + filename):
                    if file.get("status") == "deleting":
                        continue
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
                time.sleep(1)

        raise UploadTimeoutException(
            f"Timed out after {timeout} seconds while waiting for the file to be uploaded")

    def wait_for_file_deletion(self, filename, timeout=FILE_DELETION_TIMEOUT_S):
        """Wait for the file to be deleted and no longer present in the list of files"""
        sleep_interval = 5
        start_time = time.time()
        while time.time() < start_time + timeout:
            files = self.list_files().json()
            file_found = any(
                file.get("object_name") == filename or file.get("object_name", "").endswith("/" + filename)
                for file in files
            )

            if not file_found:
                logger.info(f"File {filename} has been deleted. "
                      f"Elapsed time: {round(time.time() - start_time, 1)}s")
                return True
            else:
                logger.info(f"Waiting {sleep_interval}s for file {filename} to be deleted. ")
                time.sleep(sleep_interval)

        raise DeleteTimeoutException(
            f"Timed out after {timeout} seconds while waiting for the file to be deleted")

    def wait_for_all_files_ingestion(
        self, filenames: set, timeout=FILE_UPLOAD_TIMEOUT_S
    ) -> None:
        """Wait for all files to be uploaded and ingested.

        Matches files by basename so it works both for direct uploads
        (object_name = "file.txt") and SharePoint files
        (object_name = "Documents/file.txt").
        """
        SLEEP_INTERVAL = 10
        MAX_REGISTER_RETRIES = 30

        start_time = time.time()
        ingested = set()
        fails_remaining = MAX_REGISTER_RETRIES

        def _basename(obj_name):
            return obj_name.rsplit("/", 1)[-1] if "/" in obj_name else obj_name

        while time.time() < start_time + timeout:
            edp_files = self.list_files().json()
            edp_basenames = {_basename(f["object_name"]) for f in edp_files}

            if not (filenames <= edp_basenames):
                if fails_remaining > 0:
                    fails_remaining -= 1
                    missing = filenames - edp_basenames
                    logger.warning(
                        "Not all files are present in the EDP:\n"
                        + "\n".join(list(missing))
                    )
                    logger.warning(
                        f"Will wait {SLEEP_INTERVAL}s.. "
                        f"Remaining checks: "
                        f"{fails_remaining}/{MAX_REGISTER_RETRIES}"
                    )
                    time.sleep(SLEEP_INTERVAL)
                    continue
                else:
                    missing = filenames - edp_basenames
                    raise RuntimeError(
                        "Not all files are present in the EDP:\n"
                        + "\n".join(list(missing))
                        + f"\nFailed {MAX_REGISTER_RETRIES} times."
                    )

            errored = {
                _basename(f["object_name"])
                for f in edp_files
                if _basename(f["object_name"]) in filenames
                and f["status"] == "error"
            }
            if errored:
                raise FileStatusException(
                    f"{len(errored)} file(s) failed with error "
                    f"status: {', '.join(list(errored)[:10])}"
                )

            ingested = {
                _basename(f["object_name"])
                for f in edp_files
                if _basename(f["object_name"]) in filenames
                and f["status"] == "ingested"
            }
            if filenames == ingested:
                elapsed = round(time.time() - start_time, 1)
                logger.info(
                    f"All files have been ingested. "
                    f"Elapsed time: {elapsed}s"
                )
                return
            else:
                waiting_time = time.time() - start_time
                waiting_h = int(waiting_time // 3600)
                waiting_m = int((waiting_time % 3600) // 60)
                waiting_s = int(waiting_time % 60)
                remaining = filenames - ingested
                logger.debug(
                    f"(Total: {waiting_h:02d}:{waiting_m:02d}:"
                    f"{waiting_s:02d}) Waiting {SLEEP_INTERVAL}s "
                    f"for all files to be ingested. "
                    f"Still processing: "
                    f"{', '.join(list(remaining)[:20])}"
                )
                time.sleep(SLEEP_INTERVAL)

        not_ingested = filenames - ingested
        raise UploadTimeoutException(
            f"Timed out after {timeout} seconds while waiting "
            f"for the files to be ingested:\n- "
            + "\n- ".join(not_ingested)
        )

    def upload_file_and_wait_for_ingestion(self, file_path, bucket=None):
        file_name = os.path.basename(file_path)
        response = self.generate_presigned_url(file_name, bucket=bucket)
        presigned_url = response.json().get("url")
        response = self.upload_file(file_path, presigned_url)
        assert response.status_code == 200
        return self.wait_for_file_upload(file_name, "ingested", timeout=180)

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

        headers = {}
        if (cfg.get("edp", {}).get("storageType") == "seaweedfs"
                and cfg.get("edp", {}).get("rbac", {}).get("enabled", False)):
            if "authorization" in self.get_headers():
                headers["authorization"] = self.get_headers()["authorization"]

        return requests.delete(presigned_url, verify=False, headers=headers)

    async def delete_many_files(self, presigned_urls: list[str]) -> None:
        """Delete files asynchronously."""

        headers = {}
        if (cfg.get("edp", {}).get("storageType") == "seaweedfs"
                and cfg.get("edp", {}).get("rbac", {}).get("enabled", False)):
            if "authorization" in self.get_headers():
                headers["authorization"] = self.get_headers()["authorization"]

        async with aiohttp.ClientSession() as session:
            for presigned_url in presigned_urls:
                async with session.delete(presigned_url, ssl=False, headers=headers) as response:
                    response.raise_for_status()

    def cleanup_all_files_and_links(self, file_ids_to_keep=None):
        """Cancel in-progress tasks and delete all files and links not in file_ids_to_keep."""
        in_progress = {"uploaded", "processing", "text_extracting", "text_compression",
                       "text_splitting", "late_chunking", "embedding"}
        file_ids_to_keep = file_ids_to_keep or set()

        files = self.list_files()
        if files.status_code != 200:
            logger.warning(f"EDP cleanup: failed to list files (status {files.status_code})")
            return
        for file in files.json():
            if file["id"] in file_ids_to_keep:
                continue
            file_name = file["object_name"]
            if file["status"] in in_progress:
                logger.info(f"EDP cleanup: canceling in-progress task: {file_name}")
                self.cancel_processing_task(file["id"])
            elif file["status"] in ("ingested", "error", "canceled"):
                logger.info(f"EDP cleanup: removing file: {file_name}")
                response = self.generate_presigned_url(file["object_name"], "DELETE", file.get("bucket_name"))
                self.delete_file(response.json().get("url"))

        links = self.list_links()
        if links.status_code != 200:
            logger.warning(f"EDP cleanup: failed to list links (status {links.status_code})")
            return
        for link in links.json():
            logger.info(f"EDP cleanup: removing link: {link['uri']}")
            self.delete_link(link["id"])

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
            presigned_url = response.json().get("url")
            self.upload_file(temp_file.name, presigned_url)
        return self.wait_for_file_upload(file_basename, status, timeout=timeout)

    def fill_in_file(self, temp_file, size):
        """Write data to the temp file until we reach the desired size"""
        chunk_size = 1024   # Write in chunks of 1KB
        current_size = 0
        line = "The quick brown fox jumps over the lazy dog. " * 23 + "\n"  # ~1035 chars
        while current_size < size:
            chunk = line[:chunk_size]
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
