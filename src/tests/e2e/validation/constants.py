#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CHUNK_SIZE = 512
CHUNK_OVERLAPPING = 64
DATAPREP_UPLOAD_DIR = "e2e/files/dataprep_upload"
AUDIO_FILES_DIR = "e2e/files/audio"
TEST_FILES_DIR = "e2e/files"
VITE_KEYCLOAK_REALM = "EnterpriseRAG"
VITE_KEYCLOAK_CLIENT_ID = "EnterpriseRAG-oidc"
INGRESS_NGINX_CONTROLLER_NS = "ingress-nginx"
INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR = {"app.kubernetes.io/name": "ingress-nginx"}
CHATQA_NAMESPACE = "chatqa"
