# Copyright (C) 2024-2025 Intel Corporation
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

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

COPY ./comps/tts/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/tts/utils ./comps/tts/utils
COPY --chown=user:user ./comps/tts/impl/microservice/.env ./comps/tts/impl/microservice/.env
COPY --chown=user:user ./comps/tts/opea_tts_microservice.py ./comps/tts/opea_tts_microservice.py

WORKDIR /home/user/comps/tts
EXPOSE 8200
CMD ["python", "opea_tts_microservice.py"]
