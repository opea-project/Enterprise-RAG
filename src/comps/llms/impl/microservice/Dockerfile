# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG LLM microservice
# This Dockerfile is used to build the container image for the RAG LLM microservice.

FROM python:3.11-slim
ENV LANG=C.UTF-8

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
mkdir -p /home/user && \
chown -R user /home/user/

USER user
ENV PATH="/home/user/.local/bin:${PATH}"

COPY comps/llms/impl/microservice/requirements/requirements.txt /home/user/comps/llms/impl/microservice/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/llms/impl/microservice/requirements.txt

ENV PYTHONPATH=/home/user

COPY comps/cores /home/user/comps/cores
COPY comps/__init__.py  /home/user/comps/__init__.py
COPY comps/llms/utils/opea_llm.py comps/llms/utils/opea_llm.py
COPY comps/llms/utils/connectors/ comps/llms/utils/connectors
COPY comps/llms/utils /home/user/comps/llms/utils
COPY comps/llms/config.ini /home/user/comps/llms/config.ini
COPY comps/llms/opea_llm_microservice.py /home/user/comps/llms/opea_llm_microservice.py

WORKDIR /home/user/comps/llms

ENTRYPOINT ["python", "opea_llm_microservice.py"]
