# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-trixie

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV LANG=C.UTF-8
ARG python_version

RUN apt-get -y update && \
    apt-get install -y --only-upgrade openssl=3.5.6-1~deb13u2 libssl3t64=3.5.6-1~deb13u2 openssl-provider-legacy=3.5.6-1~deb13u2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY --chown=user:user ./mcp_gateway/impl/microservice/pyproject.toml pyproject.toml
COPY --chown=user:user ./mcp_gateway/impl/microservice/uv.lock uv.lock

RUN uv sync --locked --no-cache --group security-overrides
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./mcp_gateway/utils ./mcp_gateway/utils
COPY --chown=user:user ./mcp_gateway/mcp_gateway.py ./mcp_gateway/mcp_gateway.py
COPY --chown=user:user ./comps/cores/mega/logger.py ./comps/cores/mega/logger.py

WORKDIR /home/user/mcp_gateway
CMD ["python", "mcp_gateway.py"]
