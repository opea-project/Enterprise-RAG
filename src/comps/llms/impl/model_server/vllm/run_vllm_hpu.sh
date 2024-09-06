#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo $SCRIPT_DIR
# Source the .env file

# Check if the .env file exists
if [ -f ./docker/.env ]; then
    echo ".env file found. Sourcing..."
    source docker/.env
else
    echo ".env file not found!"
    exit 1
fi

# Print the environment variables
echo "Running vLLM model server with the following environment variables:"
echo "- LLM_VLLM_MODEL_NAME: $LLM_VLLM_MODEL_NAME"
echo "- LLM_VLLM_PORT: $LLM_VLLM_PORT"
echo "- HABANA_VISIBLE_DEVICES: $HABANA_VISIBLE_DEVICES"
echo "- VLLM_SKIP_WARMUP: $VLLM_SKIP_WARMUP"
echo "- VLLM_TP_SIZE: $VLLM_TP_SIZE"
echo "- VLLM_PP_SIZE: 1" #Note: For VLLM on Gaudi, VLLM_PP_SIZE currently only supports the value 1 as pipeline parallelization is not yet supported.
echo "- VLLM_DTYPE: $VLLM_DTYPE"
echo "- VLLM_MAX_NUM_SEQS: $VLLM_MAX_NUM_SEQS"
echo "- VLLM_CPU_KVCACHE_SPACE: $VLLM_CPU_KVCACHE_SPACE"
echo "- PT_HPU_LAZY_ACC_PAR_MODE: $PT_HPU_LAZY_ACC_PAR_MODE"
echo "- PT_HPU_ENABLE_LAZY_COLLECTIVES: $PT_HPU_ENABLE_LAZY_COLLECTIVES"
echo "- OMPI_MCA_btl_vader_single_copy_mechanism: $OMPI_MCA_btl_vader_single_copy_mechanism"

# Build the image and run the server
docker compose -f docker/docker-compose-hpu.yaml up llm-vllm-model-server --build  -d