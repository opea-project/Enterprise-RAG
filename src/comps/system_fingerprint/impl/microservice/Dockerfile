# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

RUN apt-get update -y &&                                     \
    apt-get install -y --no-install-recommends --fix-missing \
        build-essential                                      \
        libgl1-mesa-glx                                      \
        libjemalloc-dev &&                                   \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user
USER user

ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

COPY ./comps/system_fingerprint/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/system_fingerprint/utils ./comps/system_fingerprint/utils
COPY --chown=user:user ./comps/system_fingerprint/opea_system_fingerprint_microservice.py ./comps/system_fingerprint/opea_system_fingerprint_microservice.py

WORKDIR /home/user/comps/system_fingerprint

ENTRYPOINT ["python", "opea_system_fingerprint_microservice.py"]
