#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import time

import requests

from tests.e2e.helpers.api_request_helper import ApiRequestHelper, ApiResponse
from tests.e2e.validation.constants import ERAG_DOMAIN

logger = logging.getLogger(__name__)

HISTORY_API_PATH = f"{ERAG_DOMAIN}/v1/chat_history"


class ChatHistoryHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper)

    def save_history(self, history, history_id=""):
        """
        v1/chat_history/save API call
        """
        start_time = time.time()
        data = {
            "history": history,
        }
        if (history_id != ""):
            data.update({"id": history_id})
        response = requests.post(
            f"{HISTORY_API_PATH}/save",
            headers=self.get_headers(),
            json=data,
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (v1/chat_history/save) call duration: {duration}")
        return ApiResponse(response, duration)

    def get_all_histories(self):
        """
        v1/chat_history/get API call
        """

        start_time = time.time()
        response = requests.get(
            f"{HISTORY_API_PATH}/get",
            headers=self.get_headers(),
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (/v1/chat_history/get) call duration: {duration}")
        return ApiResponse(response, duration)

    def get_history_details(self, history_id):
        """
        v1/chat_history/get?history_id=xxx API call
        """
        start_time = time.time()
        response = requests.get(
            f"{HISTORY_API_PATH}/get?history_id={history_id}",
            headers=self.get_headers(),
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (/v1/chat_history/get?history_id={history_id}) call duration: {duration}")
        return ApiResponse(response, duration)

    def change_history_name(self, history_id, new_history_name):
        """
        v1/chat_history/change_name API call
        """
        start_time = time.time()
        data = {
            "history_name": new_history_name,
            "id": history_id
        }
        response = requests.post(
            f"{HISTORY_API_PATH}/change_name",
            headers=self.get_headers(),
            json=data,
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (/v1/chat_history/get) call duration: {duration}")
        return ApiResponse(response, duration)

    def delete_history_by_id(self, history_id):
        """
        v1/chat_history/delete?history_id=xxx API call
        """
        start_time = time.time()
        response = requests.delete(
            f"{HISTORY_API_PATH}/delete?history_id={history_id}",
            headers=self.get_headers(),
            verify=False
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"Fingerprint (/v1/chat_history/delete?history_id={history_id}) call duration: {duration}")
        return ApiResponse(response, duration)
