# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG language detection microservice
# This Dockerfile is used to build the container image for the RAG language detection microservice.

FROM python:3.11-slim
ENV LANG=C.UTF-8

RUN apt-get update -y && \
    apt-get install build-essential -y && \
    apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONPATH="/home/user"

COPY comps/language_detection/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/language_detection/utils /home/user/comps/language_detection/utils
COPY --chown=user:user ./comps/language_detection/impl/microservice/.env ./comps/language_detection/impl/microservice/.env
COPY --chown=user:user ./comps/language_detection/opea_language_detection_microservice.py /home/user/comps/language_detection/opea_language_detection_microservice.py

WORKDIR /home/user/comps/language_detection
CMD ["python", "opea_language_detection_microservice.py"]
