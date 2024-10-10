#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

MODEL_CONFIG_FILE="/home/model-server/utils/model-config.yaml"

if [ -n "$TORCHSERVE_MODEL_NAME" ]; then
    ARCHIVE_NAME=$(basename "$TORCHSERVE_MODEL_NAME")
    echo $ARCHIVE_NAME
else
    ARCHIVE_NAME="default"
fi


# This function assigns a value to a specified target variable based on the status of an environment variable.
# Parameters:
#   - <env_name>: The name of the environment variable to check.
#   - <target_name>: The name of the target variable where the value will be assigned.
#   - <default_value>: The value to assign to the target variable if the environment variable is not defined.

assign_model_config_params() {
    local env_name="$1"
    local env_value="${!env_name}"
    local target_name="$2"
    local target_default_value="$3"

    if [ -n "$env_value" ]; then
        if [[ "$env_value" =~ ^[0-9]+$ ]]; then
            eval "$target_name=$env_value"
        else
            echo "Error: Invalid value for $env_name. Expected an integer, but received '$env_value'."
            exit 1
        fi
    else
        # env var is not defined; using default value
        eval "$target_name=$target_default_value"
    fi
}

# assign TorchServe model deployment parameters
assign_model_config_params "TORCHSERVE_MIN_WORKERS" "minWorkers" 1
assign_model_config_params "TORCHSERVE_MAX_WORKERS" "maxWorkers" 4
assign_model_config_params "TORCHSERVE_MAX_BATCH_DELAY" "maxBatchDelay" 100
assign_model_config_params "TORCHSERVE_RESPONSE_TIMEOUT" "responseTimeout" 1200


# update the model-config.yaml template with the provided parameters

sed -i "s/{{MIN_WORKERS}}/$minWorkers/" $MODEL_CONFIG_FILE
sed -i "s/{{MAX_WORKERS}}/$maxWorkers/" $MODEL_CONFIG_FILE
sed -i "s/{{MAX_BATCH_DELAY}}/$maxBatchDelay/" $MODEL_CONFIG_FILE
sed -i "s/{{RESPONSE_TIMEOUT}}/$responseTimeout/" $MODEL_CONFIG_FILE

torch-model-archiver --force \
    --model-name "$ARCHIVE_NAME" \
    --export-path /opt/ml/model \
    --version 1.0 \
    --handler /home/model-server/utils/embedding_handler.py \
    --config-file $MODEL_CONFIG_FILE \
    --archive-format tgz

torchserve --start --ts-config /home/model-server/config.properties --models ${ARCHIVE_NAME}.tar.gz

# Prevent the container from exiting
tail -f /dev/null
