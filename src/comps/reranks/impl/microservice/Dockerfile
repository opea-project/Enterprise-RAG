
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
    vim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"

# copy only necessary files and directories to the container
COPY comps/cores /home/user/comps/cores
COPY comps/__init__.py  /home/user/comps/__init__.py
COPY comps/reranks/impl/microservice/requirements.txt /home/user/comps/reranks/impl/microservice/requirements.txt
COPY comps/reranks/config.ini /home/user/comps/reranks/config.ini
COPY comps/reranks/utils /home/user/comps/reranks/utils
COPY comps/reranks/opea_reranking_microservice.py /home/user/comps/reranks/opea_reranking_microservice.py

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install torch --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/user/comps/reranks/impl/microservice/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/reranks

ENTRYPOINT ["python", "opea_reranking_microservice.py"]

