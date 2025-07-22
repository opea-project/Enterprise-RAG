#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CHUNK_SIZE = 512
CHUNK_OVERLAPPING = 64
TEST_FILES_DIR = "e2e/files/dataprep_upload"
ERAG_DOMAIN = "https://erag.com"
ERAG_AUTH_DOMAIN = "https://auth.erag.com"
VITE_KEYCLOAK_REALM = "EnterpriseRAG"
VITE_KEYCLOAK_CLIENT_ID = "EnterpriseRAG-oidc"
INGRESS_NGINX_CONTROLLER_NS = "ingress-nginx"
INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR = {"app.kubernetes.io/name": "ingress-nginx"}
