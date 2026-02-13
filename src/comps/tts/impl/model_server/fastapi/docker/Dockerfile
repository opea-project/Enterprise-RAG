# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

ENV LANG=C.UTF-8
ARG python_version

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y ffmpeg sox curl google-perftools && \
    apt-get install -y --only-upgrade \
      openssl=3.0.18-1~deb12u2 \
      libssl3=3.0.18-1~deb12u2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so
RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY comps/tts/impl/model_server/fastapi/docker/pyproject.toml pyproject.toml
COPY comps/tts/impl/model_server/fastapi/docker/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user comps/tts/impl/model_server/fastapi/docker/.env .env
COPY --chown=user:user comps/tts/impl/model_server/fastapi/model_handler.py model_handler.py
COPY --chown=user:user comps/tts/impl/model_server/fastapi/server.py server.py
COPY --chown=user:user comps/cores/mega/logger.py ./comps/cores/mega/logger.py
COPY --chown=user:user comps/cores/utils/utils.py ./comps/cores/utils/utils.py

ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libtcmalloc.so"
CMD ["python", "server.py"]
