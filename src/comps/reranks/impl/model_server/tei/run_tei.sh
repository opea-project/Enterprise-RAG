#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

RERANKER_TEI_PORT=6060
RERANKER_TEI_MODEL_NAME="BAAI/bge-reranker-large"
volume=$PWD/data


docker run -d -p $RERANKER_TEI_PORT:80 -v $volume:/data \
        --name reranking-tei \
        -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy \
        --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 \
        --model-id $RERANKER_TEI_MODEL_NAME

