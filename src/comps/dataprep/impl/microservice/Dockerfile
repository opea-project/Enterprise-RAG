# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

RUN apt-get -y update && \ 
    apt-get install --no-install-recommends --fix-missing -y nano libreoffice libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user/comps && \
    chown -R user /home/user/

USER user
ENV PATH="$PATH:/home/user/.local/bin"

COPY dataprep/impl/microservice/requirements.txt /tmp/dataprep-requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /tmp/dataprep-requirements.txt

WORKDIR /home/user/
COPY ./cores ./comps/cores
COPY ./dataprep ./comps/dataprep

ENV PYTHONPATH=$PYTHONPATH:/home/user
CMD ["python3", "comps/dataprep/opea_dataprep_microservice.py"]
