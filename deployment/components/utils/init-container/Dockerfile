# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM alpine:3.22

RUN apk add --no-cache bash curl jq && \
    curl -LO https://dl.k8s.io/release/v1.30.8/bin/linux/amd64/kubectl && \
    install -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

ENTRYPOINT ["/bin/bash"]
