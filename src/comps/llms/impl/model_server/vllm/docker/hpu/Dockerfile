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
ARG VLLM_GAUDI_COMMIT=v0.21.0
ARG VLLM_PROJECT_COMMIT=v0.21.0
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
    git fetch --tags && \
    if [ -z "${VLLM_PROJECT_COMMIT}" ]; then \
       _VLLM_COMMIT=$(git show "${VLLM_GAUDI_COMMIT}:VLLM_STABLE_COMMIT" 2>/dev/null || \
                      git show "origin/vllm/last-good-commit-for-vllm-gaudi:VLLM_STABLE_COMMIT" 2>/dev/null) && \
       echo "Found vLLM commit hash: $_VLLM_COMMIT"; \
    else \
       _VLLM_COMMIT="${VLLM_PROJECT_COMMIT}" && \
       echo "Using vLLM commit : $_VLLM_COMMIT"; \
    fi && \
    mkdir -p $VLLM_PATH && \
    # Clone vllm-project/vllm and use configured or last good commit hash
    git clone https://github.com/vllm-project/vllm.git $VLLM_PATH && \
    cd $VLLM_PATH && \
    git remote add upstream https://github.com/vllm-project/vllm.git && \
    git fetch upstream --tags || true && \
    git checkout $_VLLM_COMMIT && \
    # Install vllm-project/vllm build dependencies
    if [ -f requirements/build.txt ]; then \
       bash -c "pip install -r <(sed '/^torch/d' requirements/build.txt)"; \
    elif [ -f requirements-build.txt ]; then \
       bash -c "pip install -r <(sed '/^torch/d' requirements-build.txt)"; \
    fi && \
    pip install --no-cache-dir setuptools_rust setuptools_scm && \
    pip install --no-cache-dir $(python -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); deps=[x for x in d.get('build-system',{}).get('requires',[]) if 'torch' not in x.lower()]; print(' '.join(deps))" 2>/dev/null || echo "setuptools wheel") && \
    VLLM_TARGET_DEVICE=empty pip install --no-build-isolation . && \
    # Install vllm-gaudi plugin
    cd $VLLM_PATH2 && \
    git checkout ${VLLM_GAUDI_COMMIT} && \
    VLLM_TARGET_DEVICE=hpu pip install -v . --no-build-isolation
# --- END: COMBINED RUN COMMAND ---

# Fix known Python package CVEs
RUN pip install --no-cache-dir --upgrade \
    "urllib3==2.7.0" \
    "setuptools==82.0.1" \
    "wheel==0.46.2" \
    "xgrammar==0.1.32"

RUN pip install --no-cache-dir \
    "fastapi<0.137"

# Allow non-root user to list /root so pip's legacy-editable scan doesn't fail
# with PermissionError (habana base image installs leave .pth refs under /root)
RUN chmod 755 /root

USER ubuntu
WORKDIR /home/ubuntu/

# Set entrypoint script
ENTRYPOINT ["python3", "-m", "entrypoints.entrypoint_main"]
