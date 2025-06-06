# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.26 /uv /uvx /bin/

ENV LANG=C.UTF-8

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y nano && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python3.11/site-packages/*
RUN rm -rf /usr/local/lib/python3.11/site-packages/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user/comps/retrievers/impl/microservice
COPY ./comps/retrievers/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/retrievers/impl/microservice/uv.lock uv.lock
COPY ./comps/vectorstores/impl/requirements/pyproject.toml ../../../vectorstores/impl/requirements/pyproject.toml

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/comps/retrievers/impl/microservice/.venv/bin:$PATH"

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/vectorstores ./comps/vectorstores
COPY --chown=user:user ./comps/retrievers/utils ./comps/retrievers/utils
COPY --chown=user:user ./comps/retrievers/impl/microservice/.env ./comps/retrievers/impl/microservice/.env
COPY --chown=user:user ./comps/retrievers/opea_retriever_microservice.py ./comps/retrievers/opea_retriever_microservice.py

WORKDIR /home/user/comps/retrievers
CMD ["python", "opea_retriever_microservice.py"]
