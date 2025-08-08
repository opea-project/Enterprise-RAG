#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import time

import requests

from tests.e2e.helpers.api_request_helper import (ApiRequestHelper, ApiResponse,
                                        CustomPortForward)

logger = logging.getLogger(__name__)


class ChatHistoryHelper(ApiRequestHelper):

    def __init__(self, namespace, label_selector, api_port):
        super().__init__(namespace=namespace, label_selector=label_selector, api_port=api_port)


    def save_history(self, access_token, history, history_id=""):
        """
        v1/chat_history/save API call
        """
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            header=self.default_headers
            header["authorization"] = f"Bearer {access_token}"
            data = {
                "history": history,
            }
            if (history_id != ""):
                data.update({"id": history_id})
            response = requests.post(
                f"http://127.0.0.1:{pf.local_port}/v1/chat_history/save",
                headers=header,
                json=data
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (v1/chat_history/save) call duration: {duration}")
            return ApiResponse(response, duration)


    def get_all_histories(self, access_token):
        """
        v1/chat_history/get API call
        """
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            header=self.default_headers
            header["authorization"] = f"Bearer {access_token}"
            response = requests.get(
                f"http://127.0.0.1:{pf.local_port}/v1/chat_history/get",
                headers=header,
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (/v1/chat_history/get) call duration: {duration}")
            return ApiResponse(response, duration)


    def get_history_details(self, access_token, history_id):
        """
        v1/chat_history/get?history_id=xxx API call
        """
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            header=self.default_headers
            header["authorization"] = f"Bearer {access_token}"
            response = requests.get(
                f"http://127.0.0.1:{pf.local_port}/v1/chat_history/get?history_id={history_id}",
                headers=header,
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (/v1/chat_history/get?history_id={history_id}) call duration: {duration}")
            return ApiResponse(response, duration)


    def change_history_name(self, access_token, history_id, new_history_name):
        """
        v1/chat_history/change_name API call
        """
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            header=self.default_headers
            header["authorization"] = f"Bearer {access_token}"
            data = {
                "history_name": new_history_name,
                "id": history_id
            }
            response = requests.post(
                f"http://127.0.0.1:{pf.local_port}/v1/chat_history/change_name",
                headers=header,
                json=data
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (/v1/chat_history/get) call duration: {duration}")
            return ApiResponse(response, duration)


    def delete_history_by_id(self, access_token, history_id):
        """
        v1/chat_history/delete?history_id=xxx API call
        """
        with CustomPortForward(self.api_port, self.namespace, self.label_selector) as pf:
            start_time = time.time()
            header=self.default_headers
            header["authorization"] = f"Bearer {access_token}"
            response = requests.delete(
                f"http://127.0.0.1:{pf.local_port}/v1/chat_history/delete?history_id={history_id}",
                headers=header
            )
            duration = round(time.time() - start_time, 2)
            logger.info(f"Fingerprint (/v1/chat_history/delete?history_id={history_id}) call duration: {duration}")
            return ApiResponse(response, duration)
        