# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Using Debian Bookworm (12) - smallest stable Debian with modern glibc 2.36
FROM debian:bookworm-slim

# Install required utilitiesARG HTTP_PROXY
ARG HTTPS_PROXY
ARG http_proxy
ARG https_proxy
ARG NO_PROXY
ARG no_proxy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        gnupg \
        curl \
        jq \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p -m 755 /etc/apt/keyrings && \
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | \
        gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
    chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg
RUN echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' \
        > /etc/apt/sources.list.d/kubernetes.list && \
    chmod 644 /etc/apt/sources.list.d/kubernetes.list
RUN apt-get update && \
    apt-get install -y --no-install-recommends kubectl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/bin/bash"]
