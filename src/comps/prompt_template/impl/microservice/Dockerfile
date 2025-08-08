# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG reranking microservice
# This Dockerfile is used to build the container image for the RAG reranking microservice.

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/
ENV LANG=C.UTF-8

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends --fix-missing \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
RUN rm -rf /home/user/.local/lib/python3.11/site-packages/*
RUN rm -rf /usr/local/lib/python3.11/site-packages/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/prompt_template/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/prompt_template/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/prompt_template/utils /home/user/comps/prompt_template/utils
COPY --chown=user:user ./comps/prompt_template/impl/microservice/.env ./comps/prompt_template/impl/microservice/.env
COPY --chown=user:user ./comps/prompt_template/opea_prompt_template_microservice.py /home/user/comps/prompt_template/opea_prompt_template_microservice.py

WORKDIR /home/user/comps/prompt_template
CMD ["python", "opea_prompt_template_microservice.py"]
