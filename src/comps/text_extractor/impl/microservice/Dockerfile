# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV LANG=C.UTF-8

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y asciidoctor nano libreoffice libgl1-mesa-glx tesseract-ocr libmagic1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python3.11/site-packages/*
RUN rm -rf /usr/local/lib/python3.11/site-packages/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/text_extractor/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/text_extractor/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/text_extractor/utils ./comps/text_extractor/utils
COPY --chown=user:user ./comps/text_extractor/impl/microservice/.env ./comps/text_extractor/impl/microservice/.env
COPY --chown=user:user ./comps/text_extractor/opea_text_extractor_microservice.py ./comps/text_extractor/opea_text_extractor_microservice.py

WORKDIR /home/user/comps/text_extractor
CMD ["python", "opea_text_extractor_microservice.py"]
