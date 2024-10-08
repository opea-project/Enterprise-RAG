# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Common base
FROM python:3.11-slim AS base

ENV LANG=C.UTF-8

RUN apt-get update -y
RUN apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

COPY ./comps/embeddings/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/embeddings/utils ./comps/embeddings/utils
COPY --chown=user:user ./comps/embeddings/impl/microservice/.env ./comps/embeddings/impl/microservice/.env
COPY --chown=user:user ./comps/embeddings/opea_embedding_microservice.py ./comps/embeddings/opea_embedding_microservice.py

WORKDIR /home/user/comps/embeddings
CMD ["python", "opea_embedding_microservice.py"]

# llama_index
FROM base AS llama_index

WORKDIR /home/user
COPY ./comps/embeddings/impl/microservice/requirements/llama_index.txt /tmp/llama-requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/llama-requirements.txt

WORKDIR /home/user/comps/embeddings

# langchain
FROM base AS langchain

ARG ARCH="cpu"

WORKDIR /home/user
COPY ./comps/embeddings/impl/microservice/requirements/langchain.txt /tmp/langchain-requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /tmp/langchain-requirements.txt

WORKDIR /home/user/comps/embeddings
