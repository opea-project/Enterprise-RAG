# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/
ENV LANG=C.UTF-8

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev && \
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
COPY ./comps/query_rewrite/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/query_rewrite/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/query_rewrite/utils ./comps/query_rewrite/utils
COPY --chown=user:user ./comps/query_rewrite/__init__.py ./comps/query_rewrite/__init__.py
COPY --chown=user:user ./comps/query_rewrite/impl/microservice/.env ./comps/query_rewrite/impl/microservice/.env
COPY --chown=user:user ./comps/query_rewrite/opea_query_rewrite_microservice.py ./comps/query_rewrite/opea_query_rewrite_microservice.py

WORKDIR /home/user/comps/query_rewrite
CMD ["python", "opea_query_rewrite_microservice.py"]
