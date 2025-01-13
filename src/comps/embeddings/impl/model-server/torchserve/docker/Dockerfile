# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM intel/intel-extension-for-pytorch:2.4.0-pip-base

ENV LANG=C.UTF-8

ENV TEMP=/home/model-server/tmp
ENV MKL_THREADING_LAYER=GNU

RUN apt-get -y update                           \
 && apt-get install -y                          \
    openjdk-17-jdk                              \
    numactl                                     \
    libjemalloc-dev                             \
    google-perftools                            \
 && apt-get autoremove -y                       \
 && rm -rf /var/lib/apt/lists/*                 \
 && apt-get clean

RUN pip install --no-cache-dir -U   \
    sentence_transformers==3.1.1    \
    transformers==4.45              \
    diffusers==0.30.3               \
    accelerate==0.34.2

RUN python -m pip install oneccl_bind_pt --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/cpu/us/

# Install TorchServe pypi dependencies directly from their requirements.txt file
RUN pip install --no-cache-dir -U -r https://raw.githubusercontent.com/pytorch/serve/v0.11.0/requirements/common.txt \
 && pip install --no-cache-dir -U   \
    torchserve==0.11.0              \
    torch-model-archiver==0.11.0

# create user and folders
RUN useradd -m model-server                                 \
 && mkdir -p /home/model-server/tmp /opt/ml/model           \
 && chown -R model-server /home/model-server /opt/ml/model

# Add TS entrypoint
COPY docker/config.properties /home/model-server
COPY docker/entrypoint.sh /home/model-server/entrypoint.sh
COPY model/embedding_handler.py /home/model-server/utils/embedding_handler.py
COPY model/model-config.yaml /home/model-server/utils/model-config.yaml
RUN chmod +x /home/model-server/entrypoint.sh

# Cleanup
RUN pip cache purge && rm -rf /tmp/tmp* && rm -iRf /root/.cache

# INTEL specific ENVs
ENV KMP_SETTINGS=1
ENV KMP_AFFINITY=granularity=fine,compact,1,0
ENV KMP_BLOCKTIME=1
# jemalloc: ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libjemalloc.so:${LD_PRELOAD}"
RUN ln -s /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libtcmalloc.so:${LD_PRELOAD}"

ENTRYPOINT ["/home/model-server/entrypoint.sh"]
