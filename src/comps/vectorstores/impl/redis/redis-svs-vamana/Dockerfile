# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Redis 8.2.2 with Intel SVS-VAMANA optimizations (LeanVec + LVQ)
#
# Standard Redis 8.2.2 ships with SVS-VAMANA support but only basic 8-bit
# quantization. This Dockerfile compiles Redis from source with
# BUILD_INTEL_SVS_OPT=yes to unlock LeanVec and LVQ compression types.
#
# Build:
#   cd src/comps/vectorstores/impl/redis/redis-svs-vamana
#   docker build -t <registry>/erag/redis:8.2.2-svs .
#   docker push <registry>/erag/redis:8.2.2-svs
#
# Then configure in deployment/inventory/<env>/config.yaml:
#   vector_databases:
#     redis-cluster:
#       image:
#         repository: <registry>/erag/redis
#         tag: "8.2.2-svs"

ARG REDIS_VERSION=8.2.2

FROM ubuntu:24.04 AS builder

ARG REDIS_VERSION

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget dpkg-dev gcc g++ libc6-dev libssl-dev make git cmake \
    python3 python3-pip python3-venv python3-dev unzip rsync clang automake \
    autoconf libtool curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src
RUN git clone --branch ${REDIS_VERSION} --recurse-submodules --depth 1 \
    https://github.com/redis/redis.git redis

WORKDIR /usr/src/redis
RUN export BUILD_TLS=yes BUILD_WITH_MODULES=yes INSTALL_RUST_TOOLCHAIN=yes \
    DISABLE_WERRORS=yes BUILD_INTEL_SVS_OPT=yes && \
    make -j "$(nproc)" all

# Runtime stage
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3t64 ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -r redis || true && \
    useradd -r -g redis -d /data -s /sbin/nologin redis || true && \
    mkdir -p /data && chown redis:redis /data

COPY --from=builder /usr/src/redis/src/redis-server /usr/local/bin/
COPY --from=builder /usr/src/redis/src/redis-cli /usr/local/bin/
COPY --from=builder /usr/src/redis/src/redis-check-aof /usr/local/bin/
COPY --from=builder /usr/src/redis/src/redis-benchmark /usr/local/bin/

# Copy modules with Intel SVS-VAMANA optimizations
RUN mkdir -p /usr/local/lib/redis/modules
COPY --from=builder /usr/src/redis/modules/redisearch/redisearch.so /usr/local/lib/redis/modules/
COPY --from=builder /usr/src/redis/modules/redisjson/rejson.so /usr/local/lib/redis/modules/
COPY --from=builder /usr/src/redis/modules/redisbloom/redisbloom.so /usr/local/lib/redis/modules/
COPY --from=builder /usr/src/redis/modules/redistimeseries/redistimeseries.so /usr/local/lib/redis/modules/

VOLUME /data
WORKDIR /data

EXPOSE 6379

USER redis
ENTRYPOINT ["redis-server"]
