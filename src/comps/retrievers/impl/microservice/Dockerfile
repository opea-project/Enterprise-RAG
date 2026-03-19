# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV LANG=C.UTF-8
ARG python_version

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y nano git && \
    apt-get install -y --only-upgrade \
      openssl=3.0.18-1~deb12u2 \
      libssl3=3.0.18-1~deb12u2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ARG ACCEPT_MSSQL_EULA=Y
ENV ACCEPT_EULA=${ACCEPT_MSSQL_EULA}
RUN apt-get -y update && apt-get install -y curl 
RUN curl -sSL -O https://packages.microsoft.com/config/debian/$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1)/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb
RUN apt-get -y update && apt-get install -y msodbcsql18
RUN apt-get remove -y curl  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user/comps/retrievers/impl/microservice
COPY --chown=user:user ./comps/retrievers/impl/microservice/pyproject.toml pyproject.toml
COPY --chown=user:user ./comps/retrievers/impl/microservice/uv.lock uv.lock
COPY --chown=user:user ./comps/vectorstores/impl/requirements/pyproject.toml ../../../vectorstores/impl/requirements/pyproject.toml

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache --group security-overrides
ENV PATH="/home/user/comps/retrievers/impl/microservice/.venv/bin:$PATH"

# spaCy for Polish only, need to install the model via uv from GitHub release (not a standard PyPI package)
RUN uv pip install https://github.com/explosion/spacy-models/releases/download/pl_core_news_sm-3.8.0/pl_core_news_sm-3.8.0.tar.gz

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/vectorstores ./comps/vectorstores
COPY --chown=user:user ./comps/retrievers/utils ./comps/retrievers/utils
COPY --chown=user:user ./comps/retrievers/impl/microservice/.env ./comps/retrievers/impl/microservice/.env
COPY --chown=user:user ./comps/retrievers/opea_retriever_microservice.py ./comps/retrievers/opea_retriever_microservice.py

WORKDIR /home/user/comps/retrievers/impl/microservice/.venv/lib/python3.11/site-packages

WORKDIR /home/user/comps/retrievers
CMD ["python", "opea_retriever_microservice.py"]
