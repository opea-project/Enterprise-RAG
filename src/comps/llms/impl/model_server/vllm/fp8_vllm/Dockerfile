# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM vault.habana.ai/gaudi-docker/1.20.0/ubuntu22.04/habanalabs/pytorch-installer-2.6.0:latest

ENV LANG=en_US.UTF-8
ENV VLLM_TARGET_DEVICE="hpu"
ENV PATH="$PATH:/home/user/.local/bin"


WORKDIR /root
RUN pip install --upgrade-strategy eager optimum[habana]

RUN git clone https://github.com/huggingface/optimum-habana && cd optimum-habana && git checkout v1.13.2
RUN pip install -v git+https://github.com/HabanaAI/vllm-fork.git@v0.6.6.post1+Gaudi-1.20.0 --extra-index-url https://download.pytorch.org/whl/cpu

RUN git clone https://github.com/HabanaAI/vllm-hpu-extension
WORKDIR /root/vllm-hpu-extension/calibration
