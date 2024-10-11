# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"

RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y nano libreoffice libgl1-mesa-glx tesseract-ocr libmagic1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

COPY ./comps/dataprep/impl/microservice/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/user/
COPY --chown=user:user ./comps/__init__.py ./comps/__init__.py
COPY --chown=user:user ./comps/cores ./comps/cores
COPY --chown=user:user ./comps/dataprep/utils ./comps/dataprep/utils
COPY --chown=user:user ./comps/dataprep/impl/microservice/.env ./comps/dataprep/impl/microservice/.env
COPY --chown=user:user ./comps/dataprep/opea_dataprep_microservice.py ./comps/dataprep/opea_dataprep_microservice.py

WORKDIR /home/user/comps/dataprep
CMD ["python", "opea_dataprep_microservice.py"]
