# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM intel/intel-extension-for-pytorch:2.5.0-pip-base

ENV LANG=C.UTF-8

ENV TEMP=/home/user/tmp
ENV MKL_THREADING_LAYER=GNU

RUN apt-get -y update                           \
 && apt-get install -y                          \
    openjdk-17-jdk                              \
    numactl                                     \
    libjemalloc-dev                             \
    google-perftools                            \
    ffmpeg                                      \
 && apt-get autoremove -y                       \
 && rm -rf /var/lib/apt/lists/*                 \
 && apt-get clean

RUN ln -s /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so

# create user and folders
RUN useradd -u 1000 -m -s /bin/bash user        \
 && mkdir -p /home/user/tmp /opt/ml/model       \
 && chown -R user /home/user /opt/ml/model

USER user
ENV PATH="$PATH:/home/user/.local/bin"
ENV PYTHONPATH="/home/user"
ENV HF_HOME="/home/user/tmp"

RUN pip install --no-cache-dir -U   \
    transformers==4.46              \
    accelerate==0.34.2              \
    pydub==0.25.1

# RUN python -m pip install oneccl_bind_pt==2.5.0 --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/cpu/us/

# Install TorchServe pypi dependencies directly from their requirements.txt file
RUN pip install --no-cache-dir -U -r https://raw.githubusercontent.com/pytorch/serve/v0.12.0/requirements/common.txt \
 && pip install --no-cache-dir -U   \
    torchserve==0.12.0              \
    torch-model-archiver==0.12.0

# Add TS entrypoint
COPY --chown=user:user docker/config.properties /home/user
COPY --chown=user:user docker/entrypoint.sh /home/user/entrypoint.sh
COPY --chown=user:user model/asr_handler.py /home/user/utils/asr_handler.py
COPY --chown=user:user model/model-config.yaml /home/user/utils/model-config.yaml
RUN chmod +x /home/user/entrypoint.sh

# Cleanup
RUN pip cache purge && rm -rf /tmp/tmp* && rm -iRf /home/user/.cache

WORKDIR /home/user/
# INTEL specific ENVs
ENV KMP_SETTINGS=1
ENV KMP_AFFINITY=granularity=fine,compact,1,0
ENV KMP_BLOCKTIME=1
# jemalloc: ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libjemalloc.so:${LD_PRELOAD}"
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libtcmalloc.so:${LD_PRELOAD}"

ENTRYPOINT ["/home/user/entrypoint.sh"]
