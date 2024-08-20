#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

TEI_PORT=8090
TEI_MODEL_NAME="BAAI/bge-large-en-v1.5"

docker run --rm -d -p $TEI_PORT:80 -v ./data:/data --name embedding-tei -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $TEI_MODEL_NAME