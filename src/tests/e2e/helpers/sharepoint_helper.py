#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import logging
import os
import requests
import time
from urllib.parse import urlparse

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'
MSFT_LOGIN_PAGE = 'https://login.microsoftonline.com'


class SharepointHelper():

    def __init__(self):
        self._graph_token_cache = {}
        self.tenant_id = cfg.get("keycloak", {}).get("oidc", {}).get("tenant_id")
        self.client_id = cfg.get("keycloak", {}).get("oidc", {}).get("client_id")
        self.client_secret = cfg.get("keycloak", {}).get("oidc", {}).get("client_secret")

    def get_graph_client_token(self) -> str:
        """Acquire an application-level client-credentials token"""
        now = time.time()
        if self._graph_token_cache.get('access_token') and self._graph_token_cache.get('expires_at', 0) > now + 60:
            return self._graph_token_cache['access_token']

        token_url = f"{MSFT_LOGIN_PAGE}/{self.tenant_id}/oauth2/v2.0/token"

        resp = requests.post(
            token_url,
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
            },
            timeout=60,
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Failed to acquire token: {resp.status_code} - {resp.text}")

        data = resp.json()
        access_token = data.get('access_token')
        self._graph_token_cache['access_token'] = access_token
        self._graph_token_cache['expires_at'] = now + data.get('expires_in', 3600)
        return access_token

    @property
    def _default_headers(self) -> dict:
        """Return default authorization headers using the current Graph API token."""
        return {"Authorization": f"Bearer {self.get_graph_client_token()}"}

    def _get_site_id(self, site_url: str) -> str:
        """
        Resolve a SharePoint site URL to its Graph API site ID.
        :param site_url: The full URL of the site (e.g., 'https://intel.sharepoint.com/sites/my-site')
        :return: The site ID string from Microsoft Graph
        """
        # Extract hostname and site path from the full URL
        parsed = urlparse(site_url)
        hostname = parsed.hostname
        site_path = parsed.path  # e.g. /sites/my-site
        site_graph_url = f"{GRAPH_API_BASE}/sites/{hostname}:{site_path}"
        site_resp = requests.get(site_graph_url, headers=self._default_headers, timeout=30)

        if site_resp.status_code != 200:
            logger.error(f"Failed to resolve site {site_url}: {site_resp.text}")
            site_resp.raise_for_status()

        return site_resp.json().get('id')

    def list_site_files(self, site_name: str, folder_path: str = None) -> list:
        """
        List all items in the root drive (or a subfolder) of a given SharePoint site.
        :param site_name: The full URL of the site (e.g., 'https://intel.sharepoint.com/sites/my-site')
        :param folder_path: Optional subfolder path (e.g., 'myFolder' or 'a/b/c')
        :return: List of items (dictionaries) from Microsoft Graph
        """
        site_id = self._get_site_id(site_name)

        if folder_path:
            files_url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/root:/{folder_path}:/children"
        else:
            files_url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/root/children"
        files_resp = requests.get(files_url, headers=self._default_headers, timeout=30)

        if files_resp.status_code != 200:
            logger.error(f"Failed to list files for site ID {site_id}: {files_resp.text}")
            files_resp.raise_for_status()

        return files_resp.json().get('value', [])

    def upload_file_to_site(self, site_name: str, file_path: str, remote_path: str = None) -> dict:
        """
        Upload a file to the root drive of a given SharePoint site.
        :param site_name: The full URL of the site (e.g., 'https://intel.sharepoint.com/sites/my-site')
        :param file_path: The local path of the file to upload
        :param remote_path: Optional remote path including subdirectories (e.g., 'subfolder/file.txt').
                           If not provided, the file is uploaded to the root with its basename.
        :return: The created/updated item metadata (dictionary) from Microsoft Graph
        """
        site_id = self._get_site_id(site_name)

        destination = remote_path if remote_path else os.path.basename(file_path)
        upload_url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/root:/{destination}:/content"

        with open(file_path, 'rb') as f:
            upload_headers = {**self._default_headers, "Content-Type": "application/octet-stream"}
            upload_resp = requests.put(upload_url, headers=upload_headers, data=f, timeout=60)

        if upload_resp.status_code not in (200, 201):
            logger.error(f"Failed to upload file {destination} to site {site_name}: {upload_resp.text}")
            upload_resp.raise_for_status()

        logger.info(f"File {destination} uploaded successfully to site {site_name}")
        return upload_resp.json()

    def upload_files_in_parallel(
        self, site_name: str, file_paths: list[str], max_workers: int = 10
    ) -> list[str]:
        """
        Upload multiple files in parallel directly to SharePoint via Graph API.
        Resolves site_id once, then uploads all files concurrently.
        Returns list of successfully uploaded file names.
        """
        site_id = self._get_site_id(site_name)

        def _upload_one(file_path: str) -> str:
            file_name = os.path.basename(file_path)
            url = (
                f"{GRAPH_API_BASE}/sites/{site_id}"
                f"/drive/root:/{file_name}:/content"
            )
            with open(file_path, "rb") as f:
                headers = {
                    **self._default_headers,
                    "Content-Type": "application/octet-stream",
                }
                resp = requests.put(
                    url, headers=headers, data=f, timeout=60
                )
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"Upload failed for {file_name}: "
                    f"{resp.status_code} - {resp.text[:200]}"
                )
            return file_name

        uploaded = []
        logger.info(
            f"Uploading {len(file_paths)} files to SharePoint "
            f"with {max_workers} workers"
        )
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:
            futures = {
                executor.submit(_upload_one, fp): fp
                for fp in file_paths
            }
            for future in concurrent.futures.as_completed(futures):
                uploaded.append(future.result())

        logger.info(f"All {len(uploaded)} files uploaded to SharePoint")
        return uploaded

    def delete_file_from_site(self, site_name: str, file_name: str) -> None:
        """
        Delete a file from the root drive of a given SharePoint site.
        :param site_name: The full URL of the site (e.g., 'https://intel.sharepoint.com/sites/my-site')
        :param file_name: The name of the file to delete (e.g., 'test.txt')
        """
        site_id = self._get_site_id(site_name)

        # Delete file from the root drive by path
        delete_url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/root:/{file_name}"
        delete_resp = requests.delete(delete_url, headers=self._default_headers, timeout=30)

        if delete_resp.status_code not in (200, 204):
            logger.error(f"Failed to delete file {file_name} from site {site_name}: {delete_resp.text}")
            delete_resp.raise_for_status()

        logger.info(f"File {file_name} deleted successfully from site {site_name}")
