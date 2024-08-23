#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

LLM_TGI_PORT=8008
LLM_TGI_MODEL_NAME="Intel/neural-chat-7b-v3-3"

volume=$PWD/data


docker run -d -p $LLM_TGI_PORT:80 -v $volume:/data \
        --name llm-tgi-cpu \
        -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy \
        --pull always ghcr.io/huggingface/text-generation-inference:2.1.0 \
        --model-id $LLM_TGI_MODEL_NAME


