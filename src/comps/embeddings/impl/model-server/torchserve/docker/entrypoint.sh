#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

folder_path="/home/model-server/upload_dir/"
if [ ! -d "$folder_path" ]; then
    mkdir -p "$folder_path"
    echo "Folder created: $folder_path"
else
    echo "Folder already exists: $folder_path"
fi

if [ -n "$MODEL_NAME" ]; then
    ARCHIVE_NAME=$(basename "$MODEL_NAME")
    echo $ARCHIVE_NAME
    sed -i "s|model_name: \".*\"|model_name: \"$MODEL_NAME\"|" /home/model-server/utils/model-config.yaml
else
    ARCHIVE_NAME="default"
fi
echo $ARCHIVE_NAME
cd /home/model-server
torch-model-archiver --force --model-name "$ARCHIVE_NAME" --export-path /home/model-server/upload_dir --version 1.0 --handler /home/model-server/utils/embedding_handler.py --config-file /home/model-server/utils/model-config.yaml --archive-format tgz
sed -i "s|load_models=ALL|load_models=${ARCHIVE_NAME}.tar.gz|" /home/model-server/config.properties
mv /home/model-server/upload_dir/*.tar.gz /opt/ml/model
mkdir -p /home/model-server/model-store

cd /
python /usr/local/bin/dockerd-entrypoint.py "$@"
