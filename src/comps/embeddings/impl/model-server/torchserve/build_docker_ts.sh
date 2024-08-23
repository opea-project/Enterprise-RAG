#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

folder_path="docker/upload_dir/"
if [ ! -d "$folder_path" ]; then
    mkdir -p "$folder_path"
    echo "Folder created: $folder_path"
else
    echo "Folder already exists: $folder_path"
fi

MODEL_NAME="BAAI/bge-large-en-v1.5"

docker build -f docker/Dockerfile . -t pl-qna-rag-embedding-torchserve --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy

docker run --rm -it --name embedding-torchserve -p 8090:8090 -p 8091:8091 -p 8092:8092 -e MODEL_NAME=$MODEL_NAME pl-qna-rag-embedding-torchserve

TORCHSERVE_MODEL_NAME=$(echo "$MODEL_NAME" | awk -F'/' '{print $NF}')

curl http://localhost:8090/predictions/${TORCHSERVE_MODEL_NAME} -H "Content-Type: text/plain" --data "What is machine learning?"