# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update                           \
 && apt-get -y upgrade                          \
 && apt-get install -y --no-install-recommends  \
    build-essential                             \
    ca-certificates                             \
    cmake                                       \
    curl                                        \
    git                                         \
    libjemalloc-dev                             \
    google-perftools                            \
    libsm6                                      \
    libssl-dev                                  \
    libxext6                                    \
    libxrender-dev                              \
    numactl                                     \
 && apt-get autoremove -y                       \
 && rm -rf /var/lib/apt/lists/*                 \
 && apt-get clean

ENV GLIBC_TUNABLES glibc.cpu.x86_shstk=permissive

RUN apt update && apt install -y python3 python3-pip
RUN pip3 install torch==2.3.1 torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install intel-extension-for-pytorch==2.3.100 intel-openmp
RUN pip3 install transformers
RUN pip3 install llmspec mosec

COPY server-ipex.py server-ipex.py

# INTEL specific ENVs
RUN ln -s /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libjemalloc.so:/usr/local/lib/libiomp5.so:${LD_PRELOAD}"

CMD ["ipexrun", "cpu", "--nodes-list", "0", "--memory-allocator", "tcmalloc", "server-ipex.py"]
