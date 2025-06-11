#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

domain=${ERAG_DOMAIN_NAME:-erag.com}
randname=$(openssl rand -hex 16)
</dev/null openssl s_client -connect ${domain}:443 -servername ${domain} | openssl x509 > /usr/local/share/ca-certificates/erag-cert-${randname}.crt
update-ca-certificates
