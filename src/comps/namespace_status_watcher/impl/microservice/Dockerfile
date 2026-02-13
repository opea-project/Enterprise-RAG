# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.9.1 /uv /uvx /bin/
ENV LANG=C.UTF-8

RUN apt-get update -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apk/* && \
    rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl && \
    rm -rf /home/user/.local/lib/python${python_version}/site-packages/* && \
    rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/namespace_status_watcher/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/namespace_status_watcher/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"
RUN rm uv.lock pyproject.toml

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/namespace_status_watcher/utils ./comps/namespace_status_watcher/utils
COPY --chown=user:user ./comps/namespace_status_watcher/impl/microservice/.env ./comps/namespace_status_watcher/impl/microservice/.env
COPY --chown=user:user ./comps/namespace_status_watcher/opea_namespace_status_watcher_microservice.py ./comps/namespace_status_watcher/opea_namespace_status_watcher_microservice.py

WORKDIR /home/user/comps/namespace_status_watcher
CMD ["python", "opea_namespace_status_watcher_microservice.py"]
