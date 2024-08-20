#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

folder_path="upload_dir/"
if [ ! -d "$folder_path" ]; then
    mkdir -p "$folder_path"
    echo "Folder created: $folder_path"
else
    echo "Folder already exists: $folder_path"
fi

docker build . -t qna-rag-mosec-embedding --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy

docker run --rm -itd --name embedding-mosec -p 8000:8000 --cap-add SYS_NICE qna-rag-mosec-embedding
