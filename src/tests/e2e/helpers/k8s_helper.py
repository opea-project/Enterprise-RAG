#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import logging

import kr8s

logger = logging.getLogger(__name__)


class K8sHelper:

    def retrieve_admin_password(self, secret_name, namespace):
        """Retrieve the admin password from the keycloak secret"""
        logger.debug(f"Retrieving the admin password from the '{secret_name}' secret")
        secrets = kr8s.get("secrets", namespace=namespace)
        for secret in secrets:
            if secret.name == secret_name:
                # Extract and decode the base64-encoded password
                encoded_password = secret.data.get("admin-password")
                return base64.b64decode(encoded_password).decode().strip()
