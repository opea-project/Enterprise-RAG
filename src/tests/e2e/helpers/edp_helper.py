#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import requests
import time
from api_request_helper import ApiRequestHelper, CustomPortForward
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

LINK_DELETION_TIMEOUT_S = 60
FILE_UPLOAD_TIMEOUT_S = 10800  # 3 hours
LINK_UPLOAD_TIMEOUT = 300  # 5 minutes
DATAPREP_STATUS_FLOW = ["processing", "dataprep", "embedding", "ingested"]


class EdpHelper(ApiRequestHelper):

    def __init__(self):
        super().__init__(namespace="edp", label_selector={"app.kubernetes.io/name": "edp-backend"}, api_port=5000)
        self.default_headers = {
            "Content-Type": "application/json"
        }
        self.ingress_nginx_controller_ns = "ingress-nginx"
        self.ingress_nginx_controller_pod_label_selector = {"app.kubernetes.io/name": "ingress-nginx"}
        self.remote_port_fw = 443
        self.local_port_fw = 443

    def list_links(self):
        """Call /api/links endpoint"""
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.get(
                f"http://localhost:{pf.local_port}/api/links",
                headers=self.default_headers
            )
        return response

    def upload_links(self, payload):
        """Make post call to /api/links endpoint with the given payload"""
        print(f"Attempting to upload links using the following payload: {payload}")
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.post(
                f"http://localhost:{pf.local_port}/api/links",
                headers=self.default_headers,
                json=payload
            )
        return response

    def delete_link(self, link_uuid):
        """Delete a link by its id"""
        print(f"Deleting link with id: {link_uuid}")
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.delete(
                f"http://localhost:{pf.local_port}/api/link/{link_uuid}",
                headers=self.default_headers
            )
        return response

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
                print(f"Link {link_uri} has status {desired_status}. "
                      f"Elapsed time: {round(time.time() - start_time, 1)}s")
                return link_uri
            else:
                print(f"Waiting {sleep_interval}s for link {link_uri} to have status '{desired_status}'. "
                      f"Current status: {link.get('status')}")
                time.sleep(sleep_interval)

        raise UploadTimeoutException(
            f"Timed out after {timeout} seconds while waiting for the link to be uploaded")

    def list_files(self):
        """Call /api/files endpoint"""
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.get(
                f"http://localhost:{pf.local_port}/api/files",
                headers=self.default_headers
            )
        return response

    def generate_presigned_url(self, object_name, method="PUT"):
        """Generate a presigned URL for the given object name"""
        print(f"Generating presigned URL for object: {object_name}")
        payload = {
            "bucket_name": "default",
            "object_name": object_name,
            "method": method
        }
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.post(
                f"http://localhost:{pf.local_port}/api/presignedUrl",
                headers=self.default_headers,
                json=payload
            )
        return response

    def cancel_processing_task(self, file_uuid):
        """Cancel the processing task for the given file UUID"""
        print(f"Cancelling task for file with id: {file_uuid}")
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            response = requests.delete(
                f"http://localhost:{pf.local_port}/api/file/{file_uuid}/task",
                headers=self.default_headers
            )
        return response

    def upload_to_minio(self, file_path, presigned_url):
        """Upload a file to MinIO using the presigned URL"""
        with CustomPortForward(self.remote_port_fw, self.ingress_nginx_controller_ns,
                               self.ingress_nginx_controller_pod_label_selector, self.local_port_fw):
            print(f"Attempting to upload file {file_path} to MinIO using presigned URL: {presigned_url}")
            with open(file_path, 'rb') as f:
                response = requests.put(presigned_url, data=f, verify=False)
            return response

    def wait_for_file_upload(self, filename, desired_status, timeout=FILE_UPLOAD_TIMEOUT_S):
        """Wait for the file to be uploaded and have the desired status"""
        sleep_interval = 10
        start_time = time.time()
        while time.time() < start_time + timeout:
            files = self.list_files().json()
            file_found = False
            for file in files:
                if file.get("object_name") == filename:
                    file_found = True
                    file_status = file.get("status")
                    if self._status_reached(file_status, desired_status):
                        print(f"File {filename} has status {desired_status}. "
                              f"Elapsed time: {round(time.time() - start_time, 1)}s")
                        return file
                    else:
                        print(f"Waiting {sleep_interval}s for file {filename} to have status '{desired_status}'. "
                              f"Current status: {file_status}")
                        time.sleep(sleep_interval)
                        break
            if not file_found:
                print(f"File {filename} is not present in the list of files")

        raise UploadTimeoutException(
            f"Timed out after {timeout} seconds while waiting for the file to be uploaded")

    def delete_from_minio(self, presigned_url):
        """Delete a file from MinIO using the presigned URL"""
        with CustomPortForward(self.remote_port_fw, self.ingress_nginx_controller_ns,
                               self.ingress_nginx_controller_pod_label_selector, self.local_port_fw):
            print(f"Attempting to delete file from MinIO using presigned URL: {presigned_url}")
            return requests.delete(presigned_url, verify=False)

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
        print(f"Creating a temporary *.txt file of size {size}MB")
        with NamedTemporaryFile(delete=True, mode='w+', prefix=prefix, suffix=".txt") as temp_file:
            size_mb = size * 1024 * 1024
            self.fill_in_file(temp_file, size_mb)
            yield temp_file

    def upload_test_file(self, size, prefix, status, timeout):
        """Create a temporary file, upload it and wait for the file to reach the desired status"""
        with self.temp_txt_file(size=size, prefix=prefix) as temp_file:
            file_basename = os.path.basename(temp_file.name)
            response = self.generate_presigned_url(file_basename)
            self.upload_to_minio(temp_file.name, response.json().get("url"))
        return self.wait_for_file_upload(file_basename, status, timeout=timeout)


class DeleteTimeoutException(Exception):
    pass


class UploadTimeoutException(Exception):
    pass
