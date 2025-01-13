#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ENV_FILE=docker/.env
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

docker compose -f docker/docker-compose.yaml up --build -d reranking-tei-model-server
