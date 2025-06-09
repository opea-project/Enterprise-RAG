# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM vault.habana.ai/gaudi-docker/1.21.0/ubuntu22.04/habanalabs/pytorch-installer-2.6.0:latest

ENV LANG=en_US.UTF-8

# create user and folders
RUN useradd -u 1000 -m -s /bin/bash user
ENV PATH="$PATH:/home/user/.local/bin"
WORKDIR /home/user/

ENV VLLM_TARGET_DEVICE="hpu"
# VLLM doesn't share any prebuilt HPU packages (https://docs.vllm.ai/en/latest/getting_started/installation/cpu.html#pre-built-wheels)
# So it is impossible to easily freeze the whole vllm environment with uv
RUN pip install --upgrade pip==25.0.1

RUN git clone -b v0.7.2+Gaudi-1.21.0 --single-branch https://github.com/HabanaAI/vllm-fork.git
WORKDIR /home/user/vllm-fork
RUN pip install --upgrade pip && \
    pip install -v -r requirements-hpu.txt \

# Mitigate CVE-2025-47273. Remove when use newer version of vllm
RUN pip install setuptools==80.9.0


RUN VLLM_TARGET_DEVICE=hpu python3 setup.py install

USER user
WORKDIR /home/user/

CMD ["/bin/bash"]
