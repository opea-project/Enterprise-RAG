# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import certifi
import os
import ssl

from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger("mcp_gateway")


def build_ssl_context(s3_tls_verify: bool) -> ssl.SSLContext | bool:
    """Build SSL context that trusts the mounted CA cert (if present) plus default CAs."""
    if not s3_tls_verify:
        logger.warning("S3_TLS_VERIFY=false - TLS verification disabled for S3 storage")
        return False
    ca_file = os.getenv("SSL_CERT_FILE", "")
    if ca_file and os.path.isfile(ca_file):
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(ca_file)
        ctx.load_verify_locations(certifi.where())
        return ctx
    return True
