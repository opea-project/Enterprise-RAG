# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y nano && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

COPY ./comps/retrievers/impl/microservice/requirements.txt /tmp/retriever-requirements.txt
COPY ./comps/vectorstores/impl/requirements.txt /tmp/vectorstores-requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /tmp/retriever-requirements.txt && \
    pip install --no-cache-dir -r /tmp/vectorstores-requirements.txt

WORKDIR /home/user
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/vectorstores ./comps/vectorstores
COPY --chown=user:user ./comps/retrievers/utils ./comps/retrievers/utils
COPY --chown=user:user ./comps/retrievers/impl/microservice/.env ./comps/retrievers/impl/microservice/.env
COPY --chown=user:user ./comps/retrievers/opea_retriever_microservice.py ./comps/retrievers/opea_retriever_microservice.py

WORKDIR /home/user/comps/retrievers
CMD ["python", "opea_retriever_microservice.py"]
