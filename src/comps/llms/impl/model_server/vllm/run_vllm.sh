#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# todo: implement docker-compose-cpu.yml for scenario within device CPU

# Check if LLM_DEVICE is set and valid
if [ -z "${LLM_DEVICE}" ]; then
    echo "Error: LLM_DEVICE is not set. Please set it to 'hpu' or 'cpu'."
    exit 1
elif [ "${LLM_DEVICE}" != "hpu" ] && [ "${LLM_DEVICE}" != "cpu" ]; then
    echo "Error: LLM_DEVICE must be set to 'hpu' or 'cpu'. Provided value: ${LLM_DEVICE}."
    exit 1
fi

echo "Info: LLM_DEVICE is set to: $LLM_DEVICE"

ENV_FILE=docker/.env.${LLM_DEVICE}
echo "Reading configuration from $ENV_FILE..."

# Check if docker compose is available (prerequisite)
if ! command -v docker compose &> /dev/null; then
  echo "Error: 'docker compose' is not installed or not available in the PATH."
  exit 1
fi

# Read configuration - priority is given to environment variables already set in the OS, then variables from the .env file.
if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        # Ignore comments and empty lines
        if [[ -z "$key" || "$key" == \#* ]]; then
            continue
        fi

        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        # Ignore comments after the value
        value=$(echo "$value" | cut -d'#' -f1 | xargs)

        # Remove surrounding quotes from the value (if any)
        value=$(echo "$value" | sed 's/^["'\'']//;s/["'\'']$//')

        # Check if the variable is already exported
        if ! printenv | grep -q "^$key="; then
            export "$key=$value"
        else
            echo "$key is already set; skipping"
        fi
    done < "$ENV_FILE"
else
    echo "Error: $ENV_FILE not available. Please create the file with the required environment variables."
    exit 1
fi


if [ "${LLM_DEVICE}" = "hpu" ]; then
    # Check if 'habana' runtime exists
    if ! docker info | grep -q 'Runtimes:.*habana'; then
        echo "Error: 'habana' runtime is not available."
        exit 1
    fi

    docker compose -f docker/docker-compose-hpu.yaml up --build -d llm-vllm-model-server

elif [ "${LLM_DEVICE}" = "cpu" ]; then
    volume=$PWD/data

    echo "Build the image vllm:cpu"
    # Clone the vLLM repository (tag v0.5.5) and build a Docker image using the provided Dockerfile.cpu.
    # The docker:stable container is used to enable BuildKit and ensure a clean, reproducible build by isolating the process from previous artifacts.
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker:stable sh -c "
    apk add --no-cache git && \
    git clone https://github.com/vllm-project/vllm.git /workspace/vllm && \
    cd /workspace/vllm && \
    git checkout tags/v0.5.5 && \
    DOCKER_BUILDKIT=1 docker build -f Dockerfile.cpu -t vllm:cpu --shm-size=128g . --build-arg https_proxy=$HTTP_PROXY --build-arg http_proxy=$HTTPS_PROXY
    "

    echo "Run vllm service on CPU"

    docker run -it -d --name="llm-vllm-model-server" \
        -p $LLM_VLLM_PORT:80 \
        -v $volume:/data \
        -e HF_TOKEN=$HF_TOKEN \
        -e HTTPS_PROXY=$HTTP_PROXY \
        -e HTTP_PROXY=$HTTPS_PROXY \
        -e NO_PROXY=$NO_PROXY \
        -e VLLM_CPU_KVCACHE_SPACE=$VLLM_CPU_KVCACHE_SPACE \
        -e VLLM_DTYPE=$VLLM_DTYPE \
        -e VLLM_MAX_NUM_SEQS=$VLLM_MAX_NUM_SEQS \
        -e VLLM_SKIP_WARMUP=$VLLM_SKIP_WARMUP \
        -e VLLM_TP_SIZE=$VLLM_TP_SIZE \
        -e VLLM_PP_SIZE=$VLLM_PP_SIZE \
        vllm:cpu --model $LLM_VLLM_MODEL_NAME --host 0.0.0.0 --port 80
fi