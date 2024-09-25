#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
OVMS_MODEL_NAME="BAAI/bge-large-en-v1.5"

mkdir -p models
name=$(echo ${OVMS_MODEL_NAME} | cut -d "/" -f 2)
embeddings_model_name=${name}_embeddings
tokenizer_model_name=${name}_tokenizer

optimum-cli export openvino --model ${OVMS_MODEL_NAME} --task feature-extraction models/${embeddings_model_name}
convert_tokenizer -o models/${tokenizer_model_name} --skip-special-tokens ${OVMS_MODEL_NAME}

python combine_models.py models/${embeddings_model_name} models/${tokenizer_model_name}

docker run -d --rm -p 9000:9000 -p 9001:9001 --name ovms_embeddings -v $(pwd)/models/${name}_combined/:/model/1 openvino/model_server:2024.3 --model_name ${name} --model_path /model --cpu_extension /ovms/lib/libopenvino_tokenizers.so --port 9000 --rest_port 9001 --log_level DEBUG