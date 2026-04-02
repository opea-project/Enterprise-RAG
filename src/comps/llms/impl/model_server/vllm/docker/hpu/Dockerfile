# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Parameterize base image components
ARG DOCKER_URL=vault.habana.ai/gaudi-docker
ARG VERSION=1.23.0
ARG BASE_NAME=ubuntu24.04
ARG PT_VERSION=2.9.0
ARG REVISION=1.23.0-695
ARG REPO_TYPE=habanalabs
ARG TORCH_TYPE_SUFFIX

FROM ${DOCKER_URL}/${VERSION}/${BASE_NAME}/${REPO_TYPE}/pytorch-${TORCH_TYPE_SUFFIX}installer-${PT_VERSION}:${REVISION}

# Parameterize commit/branch for vllm-project & vllm-gaudi checkout
ARG VLLM_GAUDI_COMMIT=v0.16.0
# leave empty to use last-good-commit-for-vllm-gaudi
ARG VLLM_PROJECT_COMMIT=v0.16.0
ENV OMPI_MCA_btl_vader_single_copy_mechanism=none

# There's already a non-root user in the base image
ENV PATH="$PATH:/home/ubuntu/.local/bin"

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends gettext moreutils jq && \
    rm -f /usr/lib/python*/EXTERNALLY-MANAGED && \
    ln -sf /usr/bin/python3 /usr/bin/python
WORKDIR /root

ENV VLLM_PATH=/workspace/vllm-project
ENV VLLM_PATH2=/workspace/vllm-gaudi
ENV HABANA_VISIBLE_DEVICES=all

RUN echo "dash dash/sh boolean false" | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure dash
ENV ENV=~/.profile

# Clone the vllm-project repository and install inside the container
# --- START: COMBINED RUN COMMAND ---
RUN \
    # Clone vllm-gaudi and get the commit hash for the vllm-project/vllm
    set -e && \
    mkdir -p $VLLM_PATH2 && \
    git clone https://github.com/vllm-project/vllm-gaudi.git $VLLM_PATH2 && \
    cd $VLLM_PATH2 && \
    if [ -z "${VLLM_PROJECT_COMMIT}" ]; then \
       VLLM_PROJECT_COMMIT=$(git show "origin/vllm/last-good-commit-for-vllm-gaudi:VLLM_STABLE_COMMIT" 2>/dev/null) && \
       echo "Found vLLM commit hash: ${VLLM_PROJECT_COMMIT}"; \
    else \
       echo "Using vLLM commit : ${VLLM_PROJECT_COMMIT}"; \
    fi && \
    mkdir -p $VLLM_PATH && \
    # Clone vllm-project/vllm and use configured or last good commit hash
    git clone https://github.com/vllm-project/vllm.git $VLLM_PATH && \
    cd $VLLM_PATH && \
    git remote add upstream https://github.com/vllm-project/vllm.git && \
    git fetch upstream --tags || true && \
    git checkout ${VLLM_PROJECT_COMMIT} && \
    # Install vllm-project/vllm
    bash -c "pip install -r <(sed '/^torch/d' requirements/build.txt)" && \
    VLLM_TARGET_DEVICE=empty pip install --no-build-isolation . && \
    # Install vllm-gaudi plugin
    cd $VLLM_PATH2 && \
    git checkout ${VLLM_GAUDI_COMMIT} && \
    VLLM_TARGET_DEVICE=hpu pip install -v . --no-build-isolation
# --- END: COMBINED RUN COMMAND ---

# Fix known Python package CVEs
RUN pip install --no-cache-dir --upgrade \
    "urllib3==2.6.3" \
    "setuptools==82.0.1" \
    "wheel==0.46.2" \
    "xgrammar==0.1.32"

# Allow non-root user to list /root so pip's legacy-editable scan doesn't fail
# with PermissionError (habana base image installs leave .pth refs under /root)
RUN chmod 755 /root

USER ubuntu
WORKDIR /home/ubuntu/

# Set entrypoint script
ENTRYPOINT ["python3", "-m", "entrypoints.entrypoint_main"]
