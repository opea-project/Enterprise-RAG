#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

MODEL_CONFIG_FILE="/home/user/utils/model-config.yaml"

if [ -n "$TORCHSERVE_MODEL_NAME" ]; then
    ARCHIVE_NAME=$(basename "$TORCHSERVE_MODEL_NAME")
    echo $ARCHIVE_NAME
else
    ARCHIVE_NAME="default"
fi

# Ensure persistent data directories exist on the PVC
mkdir -p /data/hf_cache /data/jit_cache 2>/dev/null || true

# In preload mode: leader election and cache warming are handled in Python.
if [ -n "$TORCHSERVE_PRELOAD_MODE" ]; then
    exec /home/user/.venv/bin/python /home/user/utils/reranks_handler.py
fi

torch-model-archiver --force \
    --model-name "$ARCHIVE_NAME" \
    --export-path /opt/ml/model \
    --version 1.0 \
    --handler /home/user/utils/reranks_handler.py \
    --config-file $MODEL_CONFIG_FILE \
    --archive-format tgz

torchserve --start --ts-config /home/user/config.properties --models ${ARCHIVE_NAME}.tar.gz

# Prevent the container from exiting
tail -f /dev/null
