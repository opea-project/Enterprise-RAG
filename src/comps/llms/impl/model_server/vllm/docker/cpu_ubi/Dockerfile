# Multi-stage vLLM Dockerfile for Intel Xeon CPUs on UBI9.
# Stage 0: Toolchain setup for UBI9
# Stage 1: Build environment with all development tools
# Stage 2: Build vLLM wheel
# Stage 3: Minimal runtime environment with vLLM installed
#
# Build arguments:
#   PYTHON_VERSION=3.13|3.12 (default)|3.11|3.10
#   VLLM_VERSION=v0.14.1 (default)|<tag>|<branch>
#   VLLM_CPU_AVX2=false (default)|true
#   VLLM_CPU_DISABLE_AVX512=false (default)|true
#   VLLM_CPU_AVX512BF16=true (default)|false
#   VLLM_CPU_AVX512VNNI=true (default)|false
#   VLLM_CPU_AMXBF16=true (default)|false

# Global build arguments (accessible to all stages if re-declared)
ARG PYTHON_VERSION=3.12
ARG TARGETARCH=amd64
# Released on 24/01/2024
ARG VLLM_VERSION="releases/v0.14.1"
# BUILD ARGS
ARG VLLM_CPU_DISABLE_AVX512=0
ARG VLLM_CPU_AVX2=0
ARG VLLM_CPU_AVX512BF16=1
ARG VLLM_CPU_AVX512VNNI=1
ARG VLLM_CPU_AMXBF16=1

# UBI9 ships an older GCC lacking full AVX512 BF16 / AMX support, so we enable gcc-toolset-13.
###############################
# Stage 0: Toolchain Setup
###############################
# UBI9:9.7-1769417801 - released on 26.01.2026 (dd/mm/yyyy)
FROM redhat/ubi9:9.7-1769417801 AS toolchain-ubi9
RUN dnf -y update && dnf install -y gcc gcc-c++ gcc-toolset-13 && dnf clean all
ENV CC=/opt/rh/gcc-toolset-13/root/usr/bin/gcc
ENV CXX=/opt/rh/gcc-toolset-13/root/usr/bin/g++

###############################
# Stage 1: Base Image
###############################
FROM toolchain-ubi9 AS base

# Re-declare global ARGs to make them available in this stage
ARG VLLM_CPU_DISABLE_AVX512
ARG VLLM_CPU_AVX2
ARG VLLM_CPU_AVX512BF16
ARG VLLM_CPU_AVX512VNNI
ARG VLLM_CPU_AMXBF16

ARG VLLM_VERSION
ARG PYTHON_VERSION
ARG PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
ARG NUMACTL_VERSION=2.0.19
ARG MARCH="sapphirerapids"

USER 0
WORKDIR /workspace

# Set build environment variables
ENV VLLM_CPU_DISABLE_AVX512=${VLLM_CPU_DISABLE_AVX512}
ENV VLLM_CPU_AVX2=${VLLM_CPU_AVX2}
ENV VLLM_CPU_AVX512BF16=${VLLM_CPU_AVX512BF16}
ENV VLLM_CPU_AVX512VNNI=${VLLM_CPU_AVX512VNNI}
ENV VLLM_CPU_AMXBF16=${VLLM_CPU_AMXBF16}
ENV VLLM_TARGET_DEVICE=cpu

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

# Install minimal dependencies
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf -y update && \
    INSTALL_PKGS="python3 python3-devel git wget cmake make" && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    dnf clean all

# Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"


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

# Clone vLLM repository for building wheel
RUN git clone --depth 1 --branch $VLLM_VERSION https://github.com/vllm-project/vllm.git && \
    cd vllm && \
    git log --oneline -1

WORKDIR /workspace/vllm

# Install vLLM dependencies, cpu.txt has common.txt as dependency
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --upgrade pip && \
    uv pip install -r requirements/cpu.txt --no-build-isolation

###############################
# Stage 2: Build Environment
###############################
FROM base AS builder

ARG GIT_REPO_CHECK=0

WORKDIR /workspace/vllm

# Optional repository check
RUN if [ "$GIT_REPO_CHECK" != 0 ]; then bash tools/check_repo.sh ; fi

# Install build requirements
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements/cpu-build.txt

# Build vLLM wheel
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/workspace/vllm/.deps,sharing=locked \
    python3 setup.py bdist_wheel --dist-dir=dist --py-limited-api=cp38

###############################
# Stage 3: Runtime Environment
###############################
FROM redhat/ubi9:9.7-1769417801 AS runtime

# Re-declare global ARGs for use in this stage
ARG PYTHON_VERSION
ARG VLLM_VERSION
ARG VLLM_CPU_DISABLE_AVX512
ARG VLLM_CPU_AVX2
ARG VLLM_CPU_AVX512BF16
ARG VLLM_CPU_AVX512VNNI
ARG VLLM_CPU_AMXBF16
ARG TARGETARCH

# Runtime environment variables
# https://docs.vllm.ai/en/stable/getting_started/installation/cpu.html#related-runtime-environment-variables
# - VLLM_CPU_KVCACHE_SPACE
#   - Larger space can support more concurrent requests, longer context length.
# - VLLM_CPU_NUM_OF_RESERVED_CPU
#   - Note, it is recommended to manually reserve 1 CPU for vLLM front-end process when world_size == 1.
#   - Unset VLLM_CPU_NUM_OF_RESERVED_CPU for world size > 1
# - VLLM_CPU_MOE_PREPACK
#   - Requires AMX CPU flag (SPR and onwards).
# - VLLM_CPU_SGL_KERNEL
#   - The kernels require AMX instruction set, BFloat16 weight type and weight shapes divisible by 32. 
#   - Set to 1 to enable if your CPU supports it.
# - TORCHINDUCTOR_COMPILE_THREADS
#   - Controls the number of threads used by PyTorch's TorchInductor compiler for optimization.
# - VLLM_ALLOW_LONG_MAX_MODEL_LEN
#   - Bypasses vLLM's safety check that enforces the model's maximum sequence length limit.
ARG VLLM_CPU_KVCACHE_SPACE=40
ARG VLLM_CPU_OMP_THREADS_BIND=auto
ARG VLLM_CPU_NUM_OF_RESERVED_CPU=1
ARG CPU_VISIBLE_MEMORY_NODES
ARG VLLM_CPU_MOE_PREPACK=1
ARG VLLM_CPU_SGL_KERNEL=1
ARG TORCHINDUCTOR_COMPILE_THREADS=1
ARG VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
ARG VLLM_ENGINE_ITERATION_TIMEOUT_S=600
ARG GPERFTOOLS_VERSION=2.18

ENV VLLM_CPU_KVCACHE_SPACE=${VLLM_CPU_KVCACHE_SPACE}
ENV VLLM_CPU_OMP_THREADS_BIND=${VLLM_CPU_OMP_THREADS_BIND}
ENV VLLM_CPU_NUM_OF_RESERVED_CPU=${VLLM_CPU_NUM_OF_RESERVED_CPU}
ENV CPU_VISIBLE_MEMORY_NODES=${CPU_VISIBLE_MEMORY_NODES}
ENV VLLM_CPU_MOE_PREPACK=${VLLM_CPU_MOE_PREPACK}
ENV VLLM_CPU_SGL_KERNEL=${VLLM_CPU_SGL_KERNEL}
ENV TORCHINDUCTOR_COMPILE_THREADS=${TORCHINDUCTOR_COMPILE_THREADS}
ENV VLLM_ALLOW_LONG_MAX_MODEL_LEN=${VLLM_ALLOW_LONG_MAX_MODEL_LEN}
ENV VLLM_ENGINE_ITERATION_TIMEOUT_S=${VLLM_ENGINE_ITERATION_TIMEOUT_S}
ENV GPERFTOOLS_VERSION=${GPERFTOOLS_VERSION}

USER 0
WORKDIR /workspace

# Install Python 3.12 specifically and minimal runtime dependencies
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf -y update && \
    dnf install -y --setopt=tsflags=nodocs --skip-broken wget python3.12 python3.12-devel python3.12-pip openssl gcc-c++ libsm6 libxext6 libgl1 libxcb && \
    dnf clean all && \
    rm -rf /var/cache/dnf/* && \
    ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3.12 /usr/bin/pip3

# Copy artifacts from previous stages
COPY --from=base /usr/local/lib/libnuma* /usr/local/lib/
COPY --from=base /usr/local/bin/numa* /usr/local/bin/
COPY --from=builder /workspace/vllm /workspace/vllm

# Build and install gperftools from source
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

# Add labels to document build configuration
LABEL org.opencontainers.image.title="vLLM CPU based on UBI9 dedicated for Intel Xeon CPUs"
LABEL org.opencontainers.image.description="vLLM inference engine for SPR and later Intel Xeon CPUs"w
LABEL org.opencontainers.image.base.name="docker.io/redhat/ubi9:9.7-1769417801"
LABEL org.opencontainers.image.version="${VLLM_VERSION}"

# Build configuration labels
LABEL ai.vllm.build.target-arch="${TARGETARCH}"
LABEL ai.vllm.build.cpu-disable-avx512="${VLLM_CPU_DISABLE_AVX512:-false}"
LABEL ai.vllm.build.cpu-avx2="${VLLM_CPU_AVX2:-false}"
LABEL ai.vllm.build.cpu-avx512bf16="${VLLM_CPU_AVX512BF16:-true}"
LABEL ai.vllm.build.cpu-avx512vnni="${VLLM_CPU_AVX512VNNI:-true}"
LABEL ai.vllm.build.cpu-amxbf16="${VLLM_CPU_AMXBF16:-true}"
LABEL ai.vllm.build.python-version="${PYTHON_VERSION:-3.12}"

# Start vLLM server using Python 3.12
ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]