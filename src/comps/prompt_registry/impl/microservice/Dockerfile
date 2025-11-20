# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV LANG=C.UTF-8

RUN apt-get update -y &&                                     \
    apt-get install -y --no-install-recommends --fix-missing \
        build-essential                                      \
        libgl1-mesa-glx                                      \
        libjemalloc-dev &&                                   \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user
USER user

ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/prompt_registry/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/prompt_registry/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/prompt_registry/utils ./comps/prompt_registry/utils
COPY --chown=user:user ./comps/prompt_registry/opea_prompt_registry_microservice.py ./comps/prompt_registry/opea_prompt_registry_microservice.py

WORKDIR /home/user/comps/prompt_registry

ENTRYPOINT ["python", "opea_prompt_registry_microservice.py"]
