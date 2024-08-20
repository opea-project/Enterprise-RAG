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

cd model
torch-model-archiver --force --model-name all-MiniLM-L6-v2 --export-path ../docker/upload_dir/ --version 1.0 --handler embedding_handler.py --config-file model-config.yaml --archive-format tgz

cd ../docker
docker build . -t pl-qna-rag-embedding-torchserve --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy

docker run --rm -it --name embedding-torchserve -p 8090:8090 -p 8091:8091 -p 8092:8092 pl-qna-rag-embedding-torchserve torchserve --start --models all-MiniLM-L6-v2.tar.gz --ts-config /home/model-server/config.properties

# curl http://localhost:8090/predictions/all-MiniLM-L6-v2 -H "Content-Type: text/plain" --data "As of November 30, 2022, the aggregate market values of the Regis trant's Common Stock held by non-affiliates were:Class A$7,831,564,572 Class B136,467,702,472 $144,299,267,044"
