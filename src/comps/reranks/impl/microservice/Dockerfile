# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG reranking microservice
# This Dockerfile is used to build the container image for the RAG reranking microservice.

FROM python:3.11-slim
ENV LANG=C.UTF-8

ARG ARCH="cpu"

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONPATH="/home/user"

COPY comps/reranks/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install torch --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/reranks/utils /home/user/comps/reranks/utils
COPY --chown=user:user ./comps/reranks/impl/microservice/.env ./comps/reranks/impl/microservice/.env
COPY --chown=user:user ./comps/reranks/opea_reranking_microservice.py /home/user/comps/reranks/opea_reranking_microservice.py

WORKDIR /home/user/comps/reranks
CMD ["python", "opea_reranking_microservice.py"]
