# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.26 /uv /uvx /bin/

ENV LANG=C.UTF-8

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y nano && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user/comps/ingestion/impl/microservice
COPY ./comps/ingestion/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/ingestion/impl/microservice/uv.lock uv.lock
COPY ./comps/vectorstores/impl/requirements/pyproject.toml ../../../vectorstores/impl/requirements/pyproject.toml

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/comps/ingestion/impl/microservice/.venv/bin:$PATH"

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/vectorstores ./comps/vectorstores
COPY --chown=user:user ./comps/ingestion/utils ./comps/ingestion/utils
COPY --chown=user:user ./comps/ingestion/impl/microservice/.env ./comps/ingestion/impl/microservice/.env
COPY --chown=user:user ./comps/ingestion/opea_ingestion_microservice.py ./comps/ingestion/opea_ingestion_microservice.py
COPY --chown=user:user ./comps/retrievers/impl/microservice/redis-constants-override.py ./.local/lib/python3.11/site-packages/langchain_community/vectorstores/redis/constants.py

WORKDIR /home/user/comps/ingestion
CMD ["python", "opea_ingestion_microservice.py"]
