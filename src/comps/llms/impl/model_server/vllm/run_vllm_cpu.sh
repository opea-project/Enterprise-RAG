#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# todo: implement docker-compose-cpu.yml for scenario within device CPU
# Note: This configuration is based on the legacy build_docker_vllm.sh and launch_vll_service.sh from the original OPEA code. 
# It will need to be improved in the near future, and this will be addressed in a separate pull request.


LLM_VLLM_PORT=8008
LLM_VLLM_MODEL_NAME="Intel/neural-chat-7b-v3-3"
HF_TOKEN="your-hf-api-key"
volume=$PWD/data


echo "Build the image vllm:cpu"
# Clone the vLLM repository (tag v0.5.5) and build a Docker image using the provided Dockerfile.cpu.
# The docker:stable container is used to enable BuildKit and ensure a clean, reproducible build by isolating the process from previous artifacts.
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker:stable sh -c "
apk add --no-cache git && \
git clone https://github.com/vllm-project/vllm.git /workspace/vllm && \
cd /workspace/vllm && \
git checkout tags/v0.5.5 && \
DOCKER_BUILDKIT=1 docker build -f Dockerfile.cpu -t vllm:cpu --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
"

echo "Run vllm service on CPU"
docker run -it --rm --name="llm-vllm-cpu-model-server" -p $LLM_VLLM_PORTr:80 -v $volume:/data -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -e HF_TOKEN=${HF_TOKEN} -e VLLM_CPU_KVCACHE_SPACE=40 vllm:cpu --model $LLM_VLLM_MODEL_NAME --host 0.0.0.0 --port 80




