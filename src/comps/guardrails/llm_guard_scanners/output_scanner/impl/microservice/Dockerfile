# based on: https://github.com/protectai/llm-guard/blob/main/llm_guard_api/Dockerfile
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG LLM Guard output scanners microservice
# This Dockerfile is used to build the container image for the RAG LMM Guard output scanners microservice.

FROM python:3.12-slim

ARG ARCH="cpu"

# Install system packages needed for building
RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    vim \
    sudo \
    procps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH=$PYTHONPATH:/home/user

COPY ./comps/guardrails/llm_guard_scanners/output_scanner/impl/microservice/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user/
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/__init__.py ./comps/guardrails/__init__.py
COPY --chown=user:user ./comps/__init__.py ./comps/guardrails/llm_guard_scanners/__init__.py
COPY --chown=user:user ./comps/guardrails/llm_guard_scanners/output_scanner/utils ./comps/guardrails/llm_guard_scanners/output_scanner/utils
COPY --chown=user:user ./comps/guardrails/llm_guard_scanners/output_scanner/llm_guard_output_scanner_microservice.py ./comps/guardrails/llm_guard_scanners/output_scanner/llm_guard_output_scanner_microservice.py

WORKDIR /home/user/comps/guardrails/llm_guard_scanners/output_scanner
CMD ["python", "llm_guard_output_scanner_microservice.py"]
