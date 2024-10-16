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

COPY ./comps/prompt_registry/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/prompt_registry/utils ./comps/prompt_registry/utils
COPY --chown=user:user ./comps/prompt_registry/opea_prompt_registry_microservice.py ./comps/prompt_registry/opea_prompt_registry_microservice.py

WORKDIR /home/user/comps/prompt_registry

ENTRYPOINT ["python", "opea_prompt_registry_microservice.py"]
