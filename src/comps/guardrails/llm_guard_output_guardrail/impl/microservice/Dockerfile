# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Dockerfile for the RAG LLM Guard Output Guardrail microservice

ARG python_version=3.11
ARG python_image_version=${python_version}-slim-bookworm

FROM python:${python_image_version}
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

RUN apt-get update -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -f /usr/bin/dmesg /usr/bin/base64 /usr/bin/perl
RUN rm -rf /home/user/.local/lib/python${python_version}/site-packages/*
RUN rm -rf /usr/local/lib/python${python_version}/site-packages/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

WORKDIR /home/user
COPY ./comps/guardrails/llm_guard_output_guardrail/impl/microservice/pyproject.toml pyproject.toml
COPY ./comps/guardrails/llm_guard_output_guardrail/impl/microservice/uv.lock uv.lock

# --locked will fail when any changes in pyproject.toml were introduced
# Source: https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/sync.md#checking-if-the-lockfile-is-up-to-date
RUN uv sync --locked --no-cache
ENV PATH="/home/user/.venv/bin:$PATH"

# Install packages required for Sensitive Scanner
RUN python -m spacy download zh_core_web_sm
RUN python -m spacy download en_core_web_sm

COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/guardrails/__init__.py ./comps/guardrails/__init__.py
COPY --chown=user:user ./comps/guardrails/llm_guard_output_guardrail/__init__.py ./comps/guardrails/llm_guard_output_guardrail/__init__.py
COPY --chown=user:user ./comps/guardrails/llm_guard_output_guardrail/utils ./comps/guardrails/llm_guard_output_guardrail/utils
COPY --chown=user:user ./comps/guardrails/llm_guard_output_guardrail/opea_llm_guard_output_guardrail_microservice.py ./comps/guardrails/llm_guard_output_guardrail/opea_llm_guard_output_guardrail_microservice.py
COPY --chown=user:user ./comps/guardrails/llm_guard_output_guardrail/impl/microservice/.env ./comps/guardrails/llm_guard_output_guardrail/impl/microservice/.env
COPY --chown=user:user ./comps/guardrails/utils/scanners.py ./comps/guardrails/utils/scanners.py

WORKDIR /home/user/comps/guardrails/llm_guard_output_guardrail/
CMD ["python", "opea_llm_guard_output_guardrail_microservice.py"]
