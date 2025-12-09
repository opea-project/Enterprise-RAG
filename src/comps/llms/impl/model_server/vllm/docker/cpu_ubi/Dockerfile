# Multi-stage vLLM Dockerfile for Intel Xeon CPUs on UBI9.
# Stage 0: Toolchain setup for UBI9
# Stage 1: Build environment with all development tools
# Stage 2: Build vLLM wheel
# Stage 3: Minimal runtime environment with vLLM installed
#
# Build arguments:
#   PYTHON_VERSION=3.13|3.12 (default)|3.11|3.10
#   VLLM_VERSION=v0.12.0 (default)|<tag>|<branch>
#   VLLM_CPU_DISABLE_AVX512=false (default)|true
#   VLLM_CPU_AVX512BF16=true (default)|false
#   VLLM_CPU_AVX512VNNI=true (default)|false
#   VLLM_CPU_AMXBF16=true (default)|false

# UBI9 ships an older GCC lacking full AVX512 BF16 / AMX support, so we enable gcc-toolset-13.
###############################
# Stage 0: Toolchain Setup
###############################
# UBI9:9.7-1764794285 - released on 04.12.2025 (dd/mm/yyyy)
FROM redhat/ubi9:9.7-1764794285 AS toolchain-ubi9
RUN dnf -y update && dnf install -y gcc gcc-c++ gcc-toolset-13 && dnf clean all
ENV CC=/opt/rh/gcc-toolset-13/root/usr/bin/gcc
ENV CXX=/opt/rh/gcc-toolset-13/root/usr/bin/g++

###############################
# Stage 1: Base Image
###############################
FROM toolchain-ubi9 AS base

ARG PYTHON_VERSION=3.12
ARG PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
# Last commit of v0.12.0 release: 4fd9d6a85c00ac0186aa9abbeff73fc2ac6c721e, 03.12.2025 (dd/mm/yyyy)
ARG VLLM_VERSION="releases/v0.12.0"
ARG NUMACTL_VERSION=2.0.19
ARG MARCH="sapphirerapids"

USER 0

WORKDIR /workspace

RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf -y update && \
    INSTALL_PKGS="python3 python3-devel git wget cmake make" && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    dnf clean all

# Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Set build environment variables
# Redundant for -march=sapphirerapids and onwards (https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html):
# -mavx2 -mf16c -mavx512f -mavx512vnni -mavx512bf16 -mamx-tile -mamx-int8 -mamx-bf16
ENV CFLAGS="-march=${MARCH} -O3 -fopenmp"
ENV CXXFLAGS="${CFLAGS}"
ENV CMAKE_ARGS="-DCMAKE_BUILD_TYPE=Release"
ENV LD_LIBRARY_PATH="/usr/local/lib:"
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ENV UV_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ENV UV_PYTHON_INSTALL_DIR="/opt/uv/python"
ENV UV_INDEX_STRATEGY="unsafe-best-match"
ENV UV_LINK_MODE="copy"
ENV UV_HTTP_TIMEOUT=500

# Create virtual environment
RUN uv venv --python ${PYTHON_VERSION} --seed ${VIRTUAL_ENV}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Build numactl from source to get headers and libraries
RUN --mount=type=cache,target=/tmp/numactl-build \
    cd /tmp/numactl-build && \
    wget -O numactl-${NUMACTL_VERSION}.tar.gz \
    "https://github.com/numactl/numactl/releases/download/v${NUMACTL_VERSION}/numactl-${NUMACTL_VERSION}.tar.gz" && \
    tar xf numactl-${NUMACTL_VERSION}.tar.gz && \
    cd numactl-${NUMACTL_VERSION} && \
    ./configure --prefix=/usr/local && \
    make -j$(nproc) && \
    make install && \
    ldconfig

RUN git clone --depth 1 --branch $VLLM_VERSION https://github.com/vllm-project/vllm.git && \
    cd vllm && \
    git log --oneline -1

WORKDIR /workspace/vllm

# Install vLLM build and runtime dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --upgrade pip && \
    uv pip install -r requirements/cpu.txt --no-build-isolation

###############################
# Stage 2: Build Environment
###############################
FROM base AS builder

ARG GIT_REPO_CHECK=0
# Support for building with non-AVX512 vLLM: docker build --build-arg VLLM_CPU_DISABLE_AVX512="true" ...
ARG VLLM_CPU_DISABLE_AVX512=false
ARG VLLM_CPU_AVX512BF16=true
ARG VLLM_CPU_AVX512VNNI=true
# Support for building with AMXBF16 ISA
ARG VLLM_CPU_AMXBF16=true

ENV VLLM_CPU_DISABLE_AVX512=${VLLM_CPU_DISABLE_AVX512}
ENV VLLM_CPU_AVX512BF16=${VLLM_CPU_AVX512BF16}
ENV VLLM_CPU_AVX512VNNI=${VLLM_CPU_AVX512VNNI}
ENV VLLM_CPU_AMXBF16=${VLLM_CPU_AMXBF16}
ENV VLLM_TARGET_DEVICE=cpu

WORKDIR /workspace/vllm

# Optional repository check
RUN if [ "$GIT_REPO_CHECK" != 0 ]; then bash tools/check_repo.sh ; fi

# install build requirements
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements/cpu-build.txt

# Build vLLM wheel
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/workspace/vllm/.deps,sharing=locked \
    python3 setup.py bdist_wheel --dist-dir=dist

###############################
# Stage 3: Runtime Environment
###############################
FROM redhat/ubi9:9.7-1764794285 AS runtime

ARG PYTHON_VERSION=3.12
ARG GPERFTOOLS_VERSION=2.17.2

# Runtime environment variables
# https://docs.vllm.ai/en/stable/getting_started/installation/cpu.html#related-runtime-environment-variables
# Larger space can support more concurrent requests, longer context length.
ARG VLLM_CPU_KVCACHE_SPACE=40
ARG VLLM_CPU_OMP_THREADS_BIND=auto
# - Note, it is recommended to manually reserve 1 CPU for vLLM front-end process when world_size == 1.
#   - Unset VLLM_CPU_NUM_OF_RESERVED_CPU for world size > 1
ARG VLLM_CPU_NUM_OF_RESERVED_CPU=1
ARG CPU_VISIBLE_MEMORY_NODES
# Requires AMX CPU flag (SPR and onwards).
ARG VLLM_CPU_MOE_PREPACK=1
# The kernels require AMX instruction set, BFloat16 weight type and weight shapes divisible by 32. 
# Set to 1 to enable if your CPU supports it.
ARG VLLM_CPU_SGL_KERNEL=1
# Controls the number of threads used by PyTorch's TorchInductor compiler for optimization.
ARG TORCHINDUCTOR_COMPILE_THREADS=1
# Bypasses vLLM's safety check that enforces the model's maximum sequence length limit.
ARG VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
ARG VLLM_ENGINE_ITERATION_TIMEOUT_S=600

ENV GPERFTOOLS_VERSION=${GPERFTOOLS_VERSION}
ENV VLLM_CPU_KVCACHE_SPACE=${VLLM_CPU_KVCACHE_SPACE}
ENV VLLM_CPU_OMP_THREADS_BIND=${VLLM_CPU_OMP_THREADS_BIND}
ENV VLLM_CPU_NUM_OF_RESERVED_CPU=${VLLM_CPU_NUM_OF_RESERVED_CPU}
ENV CPU_VISIBLE_MEMORY_NODES=${CPU_VISIBLE_MEMORY_NODES}
ENV VLLM_CPU_MOE_PREPACK=${VLLM_CPU_MOE_PREPACK}
ENV VLLM_CPU_SGL_KERNEL=${VLLM_CPU_SGL_KERNEL}
ENV TORCHINDUCTOR_COMPILE_THREADS=${TORCHINDUCTOR_COMPILE_THREADS}
ENV VLLM_ALLOW_LONG_MAX_MODEL_LEN=${VLLM_ALLOW_LONG_MAX_MODEL_LEN}
ENV VLLM_ENGINE_ITERATION_TIMEOUT_S=${VLLM_ENGINE_ITERATION_TIMEOUT_S}

USER 0
WORKDIR /workspace

# Install Python 3.12 specifically and minimal runtime dependencies
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf -y update && \
    dnf install -y --setopt=tsflags=nodocs --skip-broken wget python3.12 python3.12-devel python3.12-pip openssl gcc-c++ && \
    dnf clean all && \
    rm -rf /var/cache/dnf/* && \
    ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3.12 /usr/bin/pip3

# Copy artifacts from previous stages
COPY --from=base /usr/local/lib/libnuma* /usr/local/lib/
COPY --from=base /usr/local/bin/numa* /usr/local/bin/
COPY --from=builder /workspace/vllm /workspace/vllm

RUN --mount=type=cache,target=/tmp/gperftools-build \
cd /tmp/gperftools-build && \
    wget -O gperftools-${GPERFTOOLS_VERSION}.tar.gz \
      "https://github.com/gperftools/gperftools/releases/download/gperftools-${GPERFTOOLS_VERSION}/gperftools-${GPERFTOOLS_VERSION}.tar.gz" && \
    tar xf gperftools-${GPERFTOOLS_VERSION}.tar.gz && \
    cd gperftools-${GPERFTOOLS_VERSION} && \
    ./configure --prefix=/usr/local --enable-minimal && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Install vLLM wheel using Python 3.12 (no UV needed in runtime)
ARG PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
RUN --mount=type=bind,from=builder,src=/workspace/vllm/dist,target=dist \
    echo "Python version:" && python3 --version && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install dist/*.whl && \
    ldconfig

# Set up environment
ENV LD_LIBRARY_PATH="/usr/local/lib:"
ENV LD_PRELOAD="/usr/local/lib/libtcmalloc_minimal.so.4:/usr/local/lib/libiomp5.so"

# Set system-wide core dump limits
RUN echo "* soft core 0" >> /etc/security/limits.conf && \
    echo "* hard core 0" >> /etc/security/limits.conf

# Create user
RUN useradd -m -u 1001 -g root -s /bin/bash vllm

# Verify installation with Python 3.12
RUN python3 -c "import sys; print(f'Python version: {sys.version}')" && \
    python3 -c "import vllm; print(f'vLLM {vllm.__version__} ready for runtime')"

USER 1001

# Start vLLM server using Python 3.12
ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]