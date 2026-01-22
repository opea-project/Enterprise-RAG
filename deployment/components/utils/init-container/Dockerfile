# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Using Debian Bookworm (12) - smallest stable Debian with modern glibc 2.36
FROM debian:bookworm-slim

# Install required utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        curl \
        jq \
        ca-certificates && \
    curl -LO https://dl.k8s.io/release/v1.30.8/bin/linux/amd64/kubectl && \
    install -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash"]
