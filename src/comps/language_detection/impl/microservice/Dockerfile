# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG language detection microservice
# This Dockerfile is used to build the container image for the RAG language detection microservice.

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/
ENV LANG=C.UTF-8

RUN apt-get update -y && \
    apt-get install build-essential -y && \
    apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/language_detection/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/language_detection/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/language_detection/utils /home/user/comps/language_detection/utils
COPY --chown=user:user ./comps/language_detection/impl/microservice/.env ./comps/language_detection/impl/microservice/.env
COPY --chown=user:user ./comps/language_detection/opea_language_detection_microservice.py /home/user/comps/language_detection/opea_language_detection_microservice.py

WORKDIR /home/user/comps/language_detection
CMD ["python", "opea_language_detection_microservice.py"]
