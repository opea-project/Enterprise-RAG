# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM vault.habana.ai/gaudi-docker/1.17.1/ubuntu22.04/habanalabs/pytorch-installer-2.3.1:latest

ENV LANG=en_US.UTF-8

WORKDIR /root
RUN pip install --upgrade-strategy eager optimum[habana]
RUN pip install git+https://github.com/HabanaAI/DeepSpeed.git@1.17.0

RUN git clone https://github.com/huggingface/optimum-habana && cd optimum-habana && git checkout v1.13.2

WORKDIR /root/optimum-habana/examples/text-generation
RUN pip install -r requirements.txt
RUN pip install -r requirements_lm_eval.txt
RUN pip install datasets==v2.14.6
