# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV LANG=C.UTF-8
ARG python_version

ENV TEMP=/home/user/tmp
ENV MKL_THREADING_LAYER=GNU

RUN apt-get -y update                           \
 && apt-get install -y                          \
    openjdk-17-jdk                              \
    numactl                                     \
    libjemalloc-dev                             \
    google-perftools                            \
 && apt-get autoremove -y                       \
 && rm -rf /var/lib/apt/lists/*                 \
 && apt-get clean

RUN ln -s /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

ENV GLIBC_TUNABLES=glibc.cpu.x86_shstk=permissive

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

# Add ipex server
COPY --chown=user:user docker/server-ipex.py /home/user
COPY --chown=user:user docker/server-ipex.py server-ipex.py

# Intel specific environment variables
ENV KMP_SETTINGS=1
ENV KMP_AFFINITY=granularity=fine,compact,1,0
ENV KMP_BLOCKTIME=1
# jemalloc: ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libjemalloc.so:${LD_PRELOAD}"
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libtcmalloc.so"

CMD ["ipexrun", "cpu", "--nodes-list", "0", "--memory-allocator", "tcmalloc", "server-ipex.py"]
