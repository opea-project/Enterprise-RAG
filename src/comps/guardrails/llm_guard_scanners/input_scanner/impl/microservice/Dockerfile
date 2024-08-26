# based on: https://github.com/protectai/llm-guard/blob/main/llm_guard_api/Dockerfile
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG LLM Guard input scanners microservice
# This Dockerfile is used to build the container image for the RAG LMM Guard input scanners microservice.

FROM python:3.12-slim

ARG ARCH="cpu"

# Install system packages needed for building
RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    vim \
    sudo \
    procps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user && \
mkdir -p /home/user && \
chown -R user /home/user/

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

COPY comps/cores /home/user/comps/cores
COPY comps/__init__.py  /home/user/comps/__init__.py
COPY comps/guardrails/llm_guard_scanners/input_scanner/impl/microservice/requirements.txt /home/user/requirements.txt
COPY comps/guardrails/llm_guard_scanners/input_scanner/utils /home/user/comps/guardrails/llm_guard_scanners/input_scanner/utils
COPY comps/guardrails/llm_guard_scanners/input_scanner/llm_guard_input_scanner_microservice.py /home/user/llm_guard_input_scanner_microservice.py

# Set up a working directory
WORKDIR /home/user/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "llm_guard_input_scanner_microservice.py"]

