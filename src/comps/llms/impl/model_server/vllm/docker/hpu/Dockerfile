# Copyright (C) 2025 Habana Labs, Ltd. an Intel Company
# SPDX-License-Identifier: Apache-2.0

# ------------------------------
# Base image parameters
# ------------------------------
ARG DOCKER_URL=vault.habana.ai/gaudi-docker
ARG VERSION=1.22.2
ARG BASE_NAME=ubuntu24.04
ARG PT_VERSION=2.7.1
ARG REVISION=latest
ARG REPO_TYPE=habanalabs
ARG TORCH_TYPE_SUFFIX

FROM ${DOCKER_URL}/${VERSION}/${BASE_NAME}/${REPO_TYPE}/pytorch-${TORCH_TYPE_SUFFIX}installer-${PT_VERSION}:${REVISION}

# Use bash and strict mode in RUN
SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# ------------------------------
# General environment
# ------------------------------
ENV OMPI_MCA_btl_vader_single_copy_mechanism=none
ENV HABANA_VISIBLE_DEVICES=all
ENV LANG=en_US.UTF-8

# Ensure `python` resolves to Python 3
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Optional: avoid dash for /bin/sh scripts
RUN echo "dash dash/sh boolean false" | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure dash

# Build-time system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git gettext moreutils jq ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------
# Create non-root user for runtime
# ------------------------------
ARG APP_USER=appuser
ENV HOME=/home/${APP_USER}
ENV PATH="${HOME}/.local/bin:${PATH}"

# ------------------------------
# Prepare directories inside the image
# ------------------------------
# /opt/vllm-project and /opt/vllm-gaudi hold cloned sources.
# /opt/app/scripts will host app-level scripts copied from vllm-gaudi/.cd
RUN mkdir -p /opt/vllm-project /opt/vllm-gaudi /opt/app/scripts

# ------------------------------
# vLLM + vllm-gaudi clone & install
# ------------------------------
ENV VLLM_PATH=/opt/vllm-project
ENV VLLM_PATH2=/opt/vllm-gaudi
ARG VLLM_GAUDI_COMMIT=v0.11.2
# Leave empty to auto-resolve from vllm-gaudi marker
ARG VLLM_PROJECT_COMMIT=v0.11.2

RUN \
  # Clone vllm-gaudi
  git clone https://github.com/vllm-project/vllm-gaudi.git "${VLLM_PATH2}" && \
  cd "${VLLM_PATH2}" && \
  git checkout "${VLLM_GAUDI_COMMIT}" && \
  # Fetch marker branch that contains last-good commit file
  git fetch origin "vllm/last-good-commit-for-vllm-gaudi" || true && \
  # Resolve vLLM commit (explicit or last-good) and trim whitespace
  if [[ -z "${VLLM_PROJECT_COMMIT}" ]]; then \
    VLLM_PROJECT_COMMIT="$(git show 'origin/vllm/last-good-commit-for-vllm-gaudi:VLLM_STABLE_COMMIT' 2>/dev/null | tr -d ' \t\r\n')"; \
    echo "Using last-good vLLM commit: ${VLLM_PROJECT_COMMIT}"; \
  else \
    echo "Using explicit vLLM commit: ${VLLM_PROJECT_COMMIT}"; \
  fi && \
  [[ -n "${VLLM_PROJECT_COMMIT}" ]] || (echo "ERROR: could not resolve VLLM_PROJECT_COMMIT" && exit 1) && \
  # Clone vllm
  git clone https://github.com/vllm-project/vllm.git "${VLLM_PATH}" && \
  cd "${VLLM_PATH}" && \
  git fetch origin --tags || true && \
  git checkout "${VLLM_PROJECT_COMMIT}" && \
  # Install vLLM build dependencies excluding torch
  pip install --no-cache-dir -r <(sed '/^torch/d' requirements/build.txt) && \
  # Install vLLM itself (empty target to avoid device-specific builds)
  VLLM_TARGET_DEVICE=empty pip install --no-cache-dir --no-build-isolation . && \
  # Install vllm-gaudi plugin for HPU
  cd "${VLLM_PATH2}" && \
  VLLM_TARGET_DEVICE=hpu pip install -v --no-cache-dir . --no-build-isolation

# ------------------------------
# Copy app-like assets from vllm-gaudi/.cd (inside the image)
# We DON'T use Docker COPY here, because these folders come from the repo we cloned during build.
# ------------------------------
RUN \
  # Create target subfolders
  mkdir -p /opt/app/scripts/templates \
           /opt/app/scripts/entrypoints \
           /opt/app/scripts/server \
           /opt/app/scripts/benchmark && \
  # Copy from vllm-gaudi's internal .cd folder into our app path
  cp -r "${VLLM_PATH2}/.cd/templates/"   /opt/app/scripts/templates/ && \
  cp -r "${VLLM_PATH2}/.cd/entrypoints/" /opt/app/scripts/entrypoints/ && \
  cp -r "${VLLM_PATH2}/.cd/server/"      /opt/app/scripts/server/ && \
  cp -r "${VLLM_PATH2}/.cd/benchmark/"   /opt/app/scripts/benchmark/

# Make scripts importable
ENV PYTHONPATH=/opt/app/scripts:${PYTHONPATH}
WORKDIR /opt/app/scripts

# ------------------------------
# Optional: install extra Python packages you need
# ------------------------------
RUN pip install --no-cache-dir datasets pandas

# ------------------------------
# Switch to non-root user for runtime
# ------------------------------
USER ${APP_USER}
ENV PYTHONDONTWRITEBYTECODE=1

# ------------------------------
# Entrypoint
# If you have a specific server module in /opt/app/scripts (from .cd),
# adjust this to what you actually want to run. Otherwise, keep a shell.
# ------------------------------
# ENTRYPOINT ["python3", "-m", "entrypoints.entrypoint_main"]
CMD ["/bin/bash"]
