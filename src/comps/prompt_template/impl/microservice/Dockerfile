# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG reranking microservice
# This Dockerfile is used to build the container image for the RAG reranking microservice.

FROM python:3.11-slim
ENV LANG=C.UTF-8

    
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends --fix-missing \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONPATH="/home/user"

COPY comps/prompt_template/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/prompt_template/utils /home/user/comps/prompt_template/utils
COPY --chown=user:user ./comps/prompt_template/impl/microservice/.env ./comps/prompt_template/impl/microservice/.env
COPY --chown=user:user ./comps/prompt_template/opea_prompt_template_microservice.py /home/user/comps/prompt_template/opea_prompt_template_microservice.py

WORKDIR /home/user/comps/prompt_template
CMD ["python", "opea_prompt_template_microservice.py"]
