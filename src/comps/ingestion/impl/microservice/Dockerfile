# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

RUN apt-get -y update && \ 
    apt-get install --no-install-recommends --fix-missing -y nano && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user/comps && \
    chown -R user /home/user/

USER user
ENV PATH="$PATH:/home/user/.local/bin"

COPY ingestion/impl/microservice/requirements.txt /tmp/ingestion-requirements.txt
COPY vectorstores/impl/requirements.txt /tmp/vectorstores-requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /tmp/ingestion-requirements.txt && \
    pip install --no-cache-dir -r /tmp/vectorstores-requirements.txt

WORKDIR /home/user
COPY ./cores ./comps/cores
COPY ./ingestion ./comps/ingestion
COPY ./vectorstores ./comps/vectorstores

ENV PYTHONPATH=$PYTHONPATH:/home/user
CMD ["python3", "comps/ingestion/opea_ingestion_microservice.py"]
