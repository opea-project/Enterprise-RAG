# Multi-stage vLLM Dockerfile for Intel Xeon CPUs on UBI9.
# Stage 1: Build environment with all development tools
# Stage 2: Build vLLM wheel
# Stage 3: Minimal runtime environment with vLLM installed
#
# Build arguments:
#   PYTHON_VERSION=3.13|3.12 (default)|3.11|3.10
#   VLLM_CPU_X86=true (default)|false (for cross-compilation)
#   VLLM_CPU_ARM_BF16=false (default)|true (for cross-compilation)

# Global build arguments (accessible to all stages if re-declared)
ARG TARGETARCH=amd64
ARG PYTHON_VERSION=3.12
ARG VLLM_CPU_X86=1
ARG VLLM_CPU_ARM_BF16=0
ARG VLLM_VERSION="releases/v0.18.0" # Released on 20/03/2026

# UBI9 ships an older GCC lacking full AVX512 BF16 / AMX support, so we enable gcc-toolset-13.
###############################
# Stage 1 Base Setup
###############################
# UBI9:9.7-1769417801 - released on 26.01.2026 (dd/mm/yyyy)
FROM redhat/ubi9:9.7-1769417801 AS base

USER 0
WORKDIR /workspace

ARG PYTHON_VERSION
ARG PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
ARG VLLM_VERSION
ARG NUMACTL_VERSION=2.0.19

# Install minimal dependencies, Python, and uv
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf -y update && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    dnf install -y --setopt=tsflags=nodocs \
        gcc gcc-c++ gcc-toolset-13 python3.12 python3.12-devel git wget cmake make \
        libSM libXext mesa-libGL libxcb jq lsof ccache ca-certificates openssl && \
    dnf clean all && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"
ENV UV_PYTHON_INSTALL_DIR="/opt/uv/python"

# Create virtual environment
RUN uv venv --python ${PYTHON_VERSION} --seed ${VIRTUAL_ENV}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ENV UV_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ENV UV_INDEX_STRATEGY="unsafe-best-match"
ENV UV_LINK_MODE="copy"
ENV UV_HTTP_TIMEOUT=500

ENV CC=/opt/rh/gcc-toolset-13/root/usr/bin/gcc
ENV CXX=/opt/rh/gcc-toolset-13/root/usr/bin/g++
ENV LD_LIBRARY_PATH="/usr/local/lib:"

# Set system-wide core dump limits
RUN echo "* soft core 0" >> /etc/security/limits.conf && \
    echo "* hard core 0" >> /etc/security/limits.conf

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
ARG TARGETARCH

ARG VLLM_CPU_X86=1
ENV VLLM_CPU_X86=${VLLM_CPU_X86}

ARG VLLM_CPU_ARM_BF16=0
ENV VLLM_CPU_ARM_BF16=${VLLM_CPU_ARM_BF16}

WORKDIR /workspace/vllm

# Validate build arguments - prevent mixing incompatible ISA flags
RUN if [ "$TARGETARCH" = "arm64" ] && [ "$VLLM_CPU_X86" != "0" ]; then \
        echo "ERROR: Cannot use x86-specific ISA flags (AVX2, AVX512, etc.) when building for ARM64 (--platform=linux/arm64)"; \
        exit 1; \
    fi && \
    if [ "$TARGETARCH" = "amd64" ] && [ "$VLLM_CPU_ARM_BF16" != "0" ]; then \
        echo "ERROR: Cannot use ARM-specific ISA flags (ARM_BF16) when building for x86_64 (--platform=linux/amd64)"; \
        exit 1; \
    fi

# Install build requirements
RUN --mount=type=cache,target=/root/.cache/uv \
uv pip install -r requirements/cpu-build.txt

# Optional repository check
RUN if [ "$GIT_REPO_CHECK" != 0 ]; then bash tools/check_repo.sh ; fi

# Build vLLM wheel
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/ccache \
    --mount=type=cache,target=/workspace/vllm/.deps,sharing=locked \
    VLLM_TARGET_DEVICE=cpu python3 setup.py bdist_wheel --dist-dir=dist --py-limited-api=cp38

###############################
# Stage 3: Runtime Environment
###############################
FROM base AS runtime

# Re-declare global ARGs for use in this stage
ARG PYTHON_VERSION
ARG VLLM_VERSION
ARG TARGETARCH

# Runtime environment variables
# https://docs.vllm.ai/en/stable/getting_started/installation/cpu.html#related-runtime-environment-variables
# - VLLM_CPU_KVCACHE_SPACE
#   - Larger space can support more concurrent requests, longer context length.
# - VLLM_CPU_NUM_OF_RESERVED_CPU
#   - Note, it is recommended to manually reserve 1 CPU for vLLM front-end process when world_size == 1.
#   - Unset VLLM_CPU_NUM_OF_RESERVED_CPU for world size > 1
# - TORCHINDUCTOR_COMPILE_THREADS
#   - Controls the number of threads used by PyTorch's TorchInductor compiler for optimization.
# - VLLM_ALLOW_LONG_MAX_MODEL_LEN
#   - Bypasses vLLM's safety check that enforces the model's maximum sequence length limit.
ARG VLLM_CPU_KVCACHE_SPACE=10
ARG VLLM_CPU_OMP_THREADS_BIND=auto
ARG VLLM_CPU_NUM_OF_RESERVED_CPU=1
ARG CPU_VISIBLE_MEMORY_NODES
ARG TORCHINDUCTOR_COMPILE_THREADS=1
ARG VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
ARG VLLM_ENGINE_ITERATION_TIMEOUT_S=600
ARG GPERFTOOLS_VERSION=2.18

ENV VLLM_CPU_KVCACHE_SPACE=${VLLM_CPU_KVCACHE_SPACE}
ENV VLLM_CPU_OMP_THREADS_BIND=${VLLM_CPU_OMP_THREADS_BIND}
ENV VLLM_CPU_NUM_OF_RESERVED_CPU=${VLLM_CPU_NUM_OF_RESERVED_CPU}
ENV CPU_VISIBLE_MEMORY_NODES=${CPU_VISIBLE_MEMORY_NODES}
ENV TORCHINDUCTOR_COMPILE_THREADS=${TORCHINDUCTOR_COMPILE_THREADS}
ENV VLLM_ALLOW_LONG_MAX_MODEL_LEN=${VLLM_ALLOW_LONG_MAX_MODEL_LEN}
ENV VLLM_ENGINE_ITERATION_TIMEOUT_S=${VLLM_ENGINE_ITERATION_TIMEOUT_S}
ENV GPERFTOOLS_VERSION=${GPERFTOOLS_VERSION}

USER 0
WORKDIR /workspace

# Copy artifacts from previous stages
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

# Install vLLM wheel
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/ccache \
    --mount=type=bind,from=builder,src=/workspace/vllm/dist,target=dist \
    uv pip install dist/*.whl && \
    ln -sf $(find /opt/venv -name 'libiomp5.so' | head -1) /usr/local/lib/libiomp5.so && \
    ldconfig

ENV LD_PRELOAD="/usr/local/lib/libtcmalloc_minimal.so.4:/usr/local/lib/libiomp5.so"

# Create user
RUN useradd -m -u 1001 -g root -s /bin/bash vllm

USER 1001

# Add labels to document build configuration
LABEL org.opencontainers.image.title="vLLM CPU based on UBI9"
LABEL org.opencontainers.image.description="vLLM inference engine for CPU platforms"
LABEL org.opencontainers.image.base.name="docker.io/redhat/ubi9:9.7-1769417801"
LABEL org.opencontainers.image.version="${VLLM_VERSION}"

# Build configuration labels
LABEL ai.vllm.build.target-arch="${TARGETARCH}"
LABEL ai.vllm.build.cpu-x86="${VLLM_CPU_X86:-false}"
LABEL ai.vllm.build.cpu-arm-bf16="${VLLM_CPU_ARM_BF16:-false}"
LABEL ai.vllm.build.python-version="${PYTHON_VERSION:-3.12}"

# Start vLLM server using Python 3.12
ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
