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
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

WORKDIR /home/user/

COPY comps/cores /home/user/comps/cores
COPY comps/__init__.py  /home/user/comps/__init__.py
COPY comps/embeddings/utils /home/user/comps/embeddings/utils
COPY comps/embeddings/opea_embedding_microservice.py /home/user/comps/embeddings/opea_embedding_microservice.py

ENV PYTHONPATH=/home/user
ENV PATH=/home/user/.local/bin:${PATH}

WORKDIR /home/user/comps/embeddings
RUN touch __init__.py

USER user

# llama_index
FROM base AS llama_index

COPY comps/embeddings/impl/microservice/requirements/llama_index.txt /home/user/comps/embeddings/requirements/llama_index.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/llama_index.txt

ENTRYPOINT ["python", "opea_embedding_microservice.py"]

# langchain
FROM base AS langchain

ARG ARCH="cpu"

COPY comps/embeddings/impl/microservice/requirements/langchain.txt /home/user/comps/embeddings/requirements/langchain.txt

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r requirements/langchain.txt

ENTRYPOINT ["python", "opea_embedding_microservice.py"]