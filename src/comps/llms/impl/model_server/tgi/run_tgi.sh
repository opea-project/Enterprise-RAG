#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


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

    if [ "${IF_FP8_QUANTIZATION}" = "true" ]; then
        docker compose -f docker/docker-compose-hpu-fp8.yaml up --build -d llm-tgi-fp8-model-server
    else
        docker compose -f docker/docker-compose-hpu.yaml up --build -d llm-tgi-model-server
    fi

elif [ "${LLM_DEVICE}" = "cpu" ]; then
    # Build the image and run the server
    docker compose -f docker/docker-compose-cpu.yaml up --build -d llm-tgi-model-server
fi
