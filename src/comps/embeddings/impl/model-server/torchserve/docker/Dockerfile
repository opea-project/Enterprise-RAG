# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04

# Set Env Variables for the images
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/lib"
ENV LD_LIBRARY_PATH="/opt/conda/lib:${LD_LIBRARY_PATH}"
ENV PYTHONIOENCODING=UTF-8
ENV LANG=C.UTF-8
ENV PATH=/opt/conda/bin:$PATH
ENV TEMP=/home/model-server/tmp
ENV MKL_THREADING_LAYER=GNU

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
    openjdk-17-jdk                              \
    openssl                                     \
    unzip                                       \
    vim                                         \
    wget                                        \
    libjpeg-dev                                 \
    libpng-dev                                  \
    zlib1g-dev                                  \
 && apt-get autoremove -y                       \
 && rm -rf /var/lib/apt/lists/*                 \
 && apt-get clean

# Install CondaForge miniconda
RUN curl -L -o ~/miniforge3.sh https://github.com/conda-forge/miniforge/releases/download/23.11.0-0/Miniforge3-23.11.0-0-Linux-x86_64.sh \
 && chmod +x ~/miniforge3.sh                    \
 && ~/miniforge3.sh -b -p /opt/conda            \
 && rm ~/miniforge3.sh                          \
 && /opt/conda/bin/conda install -c conda-forge \
    python=3.10.13                              \
    cython                                      \
    "mkl>=2023.2.0"                             \
    mkl-include                                 \
    parso                                       \
    scipy                                       \
    requests                                    \
    libgcc                                      \
    cmake                                       \
    packaging                                   \
    pyyaml                                      \
    packaging                                   \
 && /opt/conda/bin/conda clean -afy             \
 && rm -rf /etc/apt/sources.list.d/*

# symlink pip for OS use
RUN pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org \
 && ln -s /opt/conda/bin/pip /usr/local/bin/pip3

RUN pip install --no-cache-dir -U \
    langchain==0.2.3              \
    langchain-huggingface==0.0.3  \
    sentence_transformers

# Install Pytorch
RUN pip install --no-cache-dir -U torch==2.3.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Intel® Extension for PyTorch*
RUN pip install --no-cache-dir -U           \
    intel-openmp                            \
    intel-extension-for-pytorch==2.3.100

RUN python -m pip install oneccl_bind_pt --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/cpu/us/

RUN pip install --no-cache-dir -U   \
    transformers                    \
    diffusers                       \
    accelerate

# Install TorchServe pypi dependencies directly from their requirements.txt file
RUN pip install --no-cache-dir -U -r https://raw.githubusercontent.com/pytorch/serve/v0.11.0/requirements/common.txt \
 && pip install --no-cache-dir -U   \
    "numpy>=1.22.2,<1.23"           \
    torchserve==0.11.0              \
    torch-model-archiver==0.11.0

# create user and folders
RUN useradd -m model-server                                 \
 && mkdir -p /home/model-server/tmp /opt/ml/model           \
 && chown -R model-server /home/model-server /opt/ml/model

# add TS entrypoint
COPY torchserve-entrypoint.py /usr/local/bin/dockerd-entrypoint.py
COPY config.properties /home/model-server
COPY upload_dir/*.tar.gz /opt/ml/model
RUN chmod +x /usr/local/bin/dockerd-entrypoint.py

## Cleanup ##
RUN pip cache purge         \
 && rm -rf /tmp/tmp*        \
 && rm -iRf /root/.cache

# INTEL specific ENVs
ENV KMP_SETTINGS=1
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libjemalloc.so:/opt/conda/lib/libiomp5.so:${LD_PRELOAD}"

ENTRYPOINT ["python", "/usr/local/bin/dockerd-entrypoint.py"]
CMD ["torchserve", "--start", "--ts-config", "/home/model-server/config.properties", "--model-store", "/home/model-server/"]
