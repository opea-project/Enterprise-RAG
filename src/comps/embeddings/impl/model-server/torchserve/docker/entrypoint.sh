#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

MODEL_CONFIG_FILE="/home/user/utils/model-config.yaml"

if [ -n "$TORCHSERVE_MODEL_NAME" ]; then
    ARCHIVE_NAME=$(basename "$TORCHSERVE_MODEL_NAME")
    echo $ARCHIVE_NAME
else
    ARCHIVE_NAME="default"
fi

torch-model-archiver --force \
    --model-name "$ARCHIVE_NAME" \
    --export-path /opt/ml/model \
    --version 1.0 \
    --handler /home/user/utils/embedding_handler.py \
    --config-file $MODEL_CONFIG_FILE \
    --archive-format tgz

torchserve --start --ts-config /home/user/config.properties --models ${ARCHIVE_NAME}.tar.gz

# Prevent the container from exiting
tail -f /dev/null
