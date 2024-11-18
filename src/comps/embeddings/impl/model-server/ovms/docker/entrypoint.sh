#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

if [ -n "$OVMS_MODEL_NAME" ]; then
    NAME=$(basename "$OVMS_MODEL_NAME")
    echo $NAME
else
    NAME="default"
fi

EMBBEDDINGS_MODEL_NAME=${NAME}_embeddings
TOKENIZER_MODEL_NAME=${NAME}_tokenizer

if [ -d "/data/$EMBBEDDINGS_MODEL_NAME" ]; then
    echo "Warning: Embeddings model '$EMBBEDDINGS_MODEL_NAME' already exists in the attached volume. Skipping the embeddings model export."
else
    # Use the optimum-cli tool to export a model to the OpenVINO format. It will be saved in the data directory
    optimum-cli export openvino --model $OVMS_MODEL_NAME --task feature-extraction /data/$EMBBEDDINGS_MODEL_NAME
fi

if [ -d "/data/$TOKENIZER_MODEL_NAME" ]; then
    echo "Warning: Tokenizer model '$TOKENIZER_MODEL_NAME' already exists in the attached volume. Skipping the tokenizer conversion."
else
    # Convert the tokenizer and save it in the data directory, skipping special tokens
    convert_tokenizer -o /data/$TOKENIZER_MODEL_NAME --skip-special-tokens $OVMS_MODEL_NAME
fi

# Combines an embedding model and a tokenizer model using OpenVINO and saves the combined model to the directory /model/1. 
# It is important to name it this way, as OVMS expects the model version to be included in the directory path.
export EMBEDDING_DIR=/data/$EMBBEDDINGS_MODEL_NAME
export TOKENIZER_DIR=/data/$TOKENIZER_MODEL_NAME
export OUTPUT_DIR=/model/1

python combine_models.py

# Start OVMS
exec /ovms/bin/ovms --model_name $NAME --model_path /model --cpu_extension /ovms/lib/libopenvino_tokenizers.so --rest_port 9000 --log_level INFO