# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG vllm_version=0.14.0

FROM public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v${vllm_version}

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apk/*

RUN useradd -u 1000 -m -s /bin/bash user
ENV PATH="$PATH:/home/user/.local/bin"
WORKDIR /home/user/

ARG vllm_version
RUN pip install --no-cache "vllm[audio]==${vllm_version}" && \
    pip cache purge

USER user
