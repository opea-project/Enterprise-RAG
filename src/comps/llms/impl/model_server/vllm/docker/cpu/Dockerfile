# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04 AS dev

# Default value 1000 for Kubernetes user
# Overridable for local/testing builds to set same as host user
ARG USER_UID=1000

# install packages based on vllm/Dockerfile.cpu
RUN apt-get update -y \
    && apt-get install -y git gcc-12 g++-12 python3 python3-pip libtcmalloc-minimal4 libnuma-dev \
    && apt-get install -y ffmpeg libsm6 libxext6 libgl1 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 10 --slave /usr/bin/g++ g++ /usr/bin/g++-12

RUN useradd -u ${USER_UID} -m -s /bin/bash user        \
&& chown -R user /home/user /tmp

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"

RUN pip install --upgrade pip==25.0.1
RUN pip install intel-openmp==2025.0.1
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4:/home/user/.local/lib/libiomp5.so"
RUN echo 'ulimit -c 0' >> ~/.bashrc

WORKDIR /home/user
ENV PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"

# VLLM doesn't share any prebuilt CPU packages (https://docs.vllm.ai/en/latest/getting_started/installation/cpu.html#pre-built-wheels)
# So it is impossible to easily freeze the whole vllm environment with uv
ENV VLLM_TARGET_DEVICE="cpu"
RUN git clone --branch v0.8.5.post1 https://github.com/vllm-project/vllm.git /home/user/vllm
COPY docker/vllm_patch.patch /home/user/vllm/
RUN cd /home/user/vllm && git apply vllm_patch.patch
RUN pip install -v /home/user/vllm && rm -rf /home/user/vllm
RUN pip install intel_extension_for_pytorch==2.6.0

COPY docker/assign_cores.sh .

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
