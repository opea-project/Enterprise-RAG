#!/bin/bash

# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# List of models that require --trust-remote-code for proper functionality.
TRUSTED_MODELS=(
    "jinaai/jina-embeddings-v3"
    "nomic-ai/nomic-embed-text-v1"
    # Add more trusted models here as needed
)

# Extract the model name from the command arguments
MODEL_NAME=""
ARGS=("$@")
for i in "${!ARGS[@]}"; do
    if [[ "${ARGS[$i]}" == "--model" ]]; then
        MODEL_NAME="${ARGS[$((i + 1))]}"
        break
    fi
done

# Check if the model is in the trusted list
TRUST_FLAG=""
for trusted_model in "${TRUSTED_MODELS[@]}"; do
    if [[ "${MODEL_NAME,,}" == "${trusted_model}" ]]; then
        echo "Model '${MODEL_NAME}' is in trusted list. Adding --trust-remote-code flag."
        TRUST_FLAG="--trust-remote-code"
        break
    fi
done

exec vllm serve "$@" ${TRUST_FLAG}
