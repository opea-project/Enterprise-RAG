# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-trixie

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV LANG=C.UTF-8

ENV TEMP=/home/user/tmp
ENV MKL_THREADING_LAYER=GNU

RUN apt-get -y update                           \
 && apt-get install -y                          \
    openjdk-21-jdk                              \
    numactl                                     \
    libjemalloc-dev                             \
    google-perftools                            \
 && apt-get autoremove -y                       \
 && rm -rf /var/lib/apt/lists/*                 \
 && apt-get clean

RUN ln -s /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

# Create user and folders
RUN useradd -u 1000 -m -s /bin/bash user        \
 && mkdir -p /home/user/tmp /opt/ml/model       \
 && chown -R user /home/user /opt/ml/model

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"
ENV HF_HOME="/home/user/tmp"

# Install UV requirements
WORKDIR /home/user/
COPY ./docker/pyproject.toml pyproject.toml
COPY ./docker/uv.lock uv.lock
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

# Add TS entrypoint
COPY --chown=user:user docker/config.properties /home/user
COPY --chown=user:user docker/entrypoint.sh /home/user/entrypoint.sh
COPY --chown=user:user model/reranks_handler.py /home/user/utils/reranks_handler.py
COPY --chown=user:user model/model-config.yaml /home/user/utils/model-config.yaml
RUN chmod +x /home/user/entrypoint.sh

# jemalloc: ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libjemalloc.so:${LD_PRELOAD}"
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libtcmalloc.so:${LD_PRELOAD}"

ENTRYPOINT ["/home/user/entrypoint.sh"]
