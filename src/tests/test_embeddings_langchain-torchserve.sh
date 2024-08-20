#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# This test checks embedding microservice with Torchserve model engine by sending request and verifying 200 response code.

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

EMBEDDINGS_MICROSERVICE_PORT=5005
EMBEDDINGS_MICROSERVICE_CONTAINER_NAME="embedding-torchserve-microservice"
EMBEDDINGS_MICROSERVICE_IMAGE_NAME="opea/${EMBEDDINGS_MICROSERVICE_CONTAINER_NAME}:comps"

BUILD_VENV_NAME="test-embeddings-langchain-torchserve-venv"
BUILD_VENV_SRC="${WORKPATH}/tests/${BUILD_VENV_NAME}"

TORCHSERVE_DIR="./comps/embeddings/impl/model-server/torchserve/docker"
TORCHSERVE_CONTAINER_NAME="embedding-torchserve"
TORCHSERVE_IMAGE_NAME="opea/${TORCHSERVE_CONTAINER_NAME}:comps"

function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function make_build_env() {
    cd $WORKPATH/tests

    # Dedicated Python env required to build Torchserve model server.
    python3 -m venv ${BUILD_VENV_SRC}
    source ${BUILD_VENV_NAME}/bin/activate
    pip install torch-model-archiver

    cd $WORKPATH/${TORCHSERVE_DIR}
    mkdir -p upload_dir

    torch-model-archiver --force --model-name all-MiniLM-L6-v2 --export-path ./upload_dir/ --version 1.0 --handler ../model/embedding_handler.py --config-file ../model/model-config.yaml --archive-format tgz

    deactivate
}

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t ${TORCHSERVE_IMAGE_NAME} -f comps/embeddings/impl/model-server/torchserve/docker/Dockerfile comps/embeddings/impl/model-server/torchserve/docker/
    docker build --no-cache -t ${EMBEDDINGS_MICROSERVICE_IMAGE_NAME} -f comps/embeddings/impl/microservice/Dockerfile .
}

function delete_build_env() {
    if [ -d "${BUILD_VENV_SRC}" ]; then
        rm -rf "${BUILD_VENV_NAME}"
    fi
}

function start_service() {
    model="sentence-transformers/all-MiniLM-L6-v2"
    revision="refs/pr/5"
    unset http_proxy
    docker run -d --rm --name ${TORCHSERVE_CONTAINER_NAME} \
        --runtime runc \
        -p 8090:8090 \
        -p 8091:8091 \
        -p 8092:8092 \
        ${TORCHSERVE_IMAGE_NAME} \
        torchserve --start --models all-MiniLM-L6-v2.tar.gz --ts-config /home/model-server/config.properties

    docker run -d --rm --name ${EMBEDDINGS_MICROSERVICE_CONTAINER_NAME} \
        --runtime runc \
        -p ${EMBEDDINGS_MICROSERVICE_PORT}:6000 \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e EMBEDDING_MODEL_NAME="${model}" \
        -e EMBEDDING_MODEL_SERVER="torchserve" \
        -e EMBEDDING_MODEL_SERVER_ENDPOINT="http://${ip_address}:8090/predictions/all-MiniLM-L6-v2" \
        --ipc=host \
        ${EMBEDDINGS_MICROSERVICE_IMAGE_NAME}
    sleep 1m
}

function validate_microservice() {
    HTTP_RESPONSE=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${ip_address}:${EMBEDDINGS_MICROSERVICE_PORT}/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json' \
    )

    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        if [ "$HTTP_STATUS" -ne "200" ]; then
            test_fail "HTTP status is not 200. Received status was $HTTP_STATUS"
		fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=${TORCHSERVE_CONTAINER_NAME}")
    if [[ ! -z "$cid" ]]; then docker stop $cid && sleep 1s; fi

    cid=$(docker ps -aq --filter "name=test-comps-embedding-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && sleep 1s; fi
}

function test_clean() {
    delete_build_env
    stop_docker
    echo y | docker system prune -a
}

function main() {

    test_clean

    make_build_env

    build_docker_images

    start_service

    validate_microservice

    test_clean
}

main
