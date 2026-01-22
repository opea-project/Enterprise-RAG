# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.9.1 /uv /uvx /bin/
ENV LANG=C.UTF-8

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apk/* && \
    rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl && \
    rm -rf /home/user/.local/lib/python${python_version}/site-packages/* && \
    rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/docsum/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/docsum/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache && \
    find .venv -name "*.pyc" -delete && \
    find .venv -name "__pycache__" -type d -exec rm -rf {} + || true && \
    rm uv.lock pyproject.toml

ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/docsum/utils ./comps/docsum/utils
COPY --chown=user:user ./comps/docsum/impl/microservice/.env ./comps/docsum/impl/microservice/.env
COPY --chown=user:user ./comps/docsum/opea_docsum_microservice.py ./comps/docsum/opea_docsum_microservice.py

WORKDIR /home/user/comps/docsum
CMD ["python", "opea_docsum_microservice.py"]
