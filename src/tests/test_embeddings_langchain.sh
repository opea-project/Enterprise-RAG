#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding-tei:comps -f comps/embeddings/impl/microservice/Dockerfile .
}

function start_service() {
    tei_endpoint=5001
    model="BAAI/bge-large-en-v1.5"
    revision="refs/pr/5"
    unset http_proxy
    docker run -d --rm --name="test-comps-embedding-tei-endpoint" \
      --runtime runc \
      -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model --revision $revision
    tei_service_port=5002
    docker run -d --rm --name="test-comps-embedding-tei-server" \
      --runtime runc \
      -p ${tei_service_port}:6000 \
      -e http_proxy=$http_proxy \
      -e https_proxy=$https_proxy \
      -e EMBEDDING_MODEL_NAME="${model}" \
      -e EMBEDDING_MODEL_SERVER="tei" \
      -e EMBEDDING_MODEL_SERVER_ENDPOINT="http://${ip_address}:${tei_endpoint}" \
      --ipc=host \
      opea/embedding-tei:comps
    sleep 1m
}

function validate_microservice() {
    tei_service_port=5002
    http_proxy="" curl http://${ip_address}:$tei_service_port/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-embedding-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && sleep 1s; fi
}

function test_clean() {
    stop_docker
    echo y | docker system prune -a
}

function main() {

    test_clean

    build_docker_images
    start_service

    validate_microservice

    test_clean

}

main