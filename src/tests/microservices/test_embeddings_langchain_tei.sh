#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# This test checks embedding microservice by sending request and verifying 200 response code and response content.
# Framework: Langchain
# Moder server: TEI

set -xe

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')

CONTAINER_NAME_BASE="test-comps-embeddings"

ENDPOINT_CONTAINER_NAME="${CONTAINER_NAME_BASE}-endpoint"
ENDPOINT_IMAGE_NAME="ghcr.io/huggingface/text-embeddings-inference:cpu-1.2"

MICROSERVICE_API_PORT=5005
MICROSERVICE_CONTAINER_NAME="${CONTAINER_NAME_BASE}-microservice"
MICROSERVICE_IMAGE_NAME="opea/${MICROSERVICE_CONTAINER_NAME}:comps"

function fail_test() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t ${MICROSERVICE_IMAGE_NAME} -f comps/embeddings/impl/microservice/Dockerfile .
}

function start_service() {
    model="BAAI/bge-large-en-v1.5"
    internal_communication_port=5001
    revision="refs/pr/5"

    docker run -d --rm --name="${ENDPOINT_CONTAINER_NAME}" \
      --runtime runc \
      -p $internal_communication_port:80 \
      -v ./data:/data \
      --pull always "${ENDPOINT_IMAGE_NAME}" \
      --model-id $model \
      --revision $revision

   docker run -d --rm --name ${MICROSERVICE_CONTAINER_NAME} \
      --runtime runc \
      -p ${MICROSERVICE_API_PORT}:6000 \
      -e http_proxy=$http_proxy \
      -e https_proxy=$https_proxy \
      -e EMBEDDING_MODEL_NAME="${model}" \
      -e EMBEDDING_MODEL_SERVER="tei" \
      -e EMBEDDING_MODEL_SERVER_ENDPOINT="http://${IP_ADDRESS}:${internal_communication_port}" \
      --ipc=host \
      ${MICROSERVICE_IMAGE_NAME}
    sleep 1m
}

function validate_microservice() {
    # Command errors here are not exceptions, but handled as test fails.
    set +e

    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${MICROSERVICE_API_PORT}/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json' \
    )

    http_status=$(echo $http_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    if [ "$http_status" -ne "200" ]; then
        fail_test "HTTP status is not 200. Received status was $http_status"
		fi

    http_content=$(echo "$http_response" | sed 's/HTTPSTATUS.*//')
		echo "${http_content}" | jq; parse_return_code=$?
		if [ "${parse_return_code}" -ne "0" ]; then
        fail_test "HTTP response content is not json parsable. Response content was: ${http_content}"
		fi

		set -e
}

function stop_containers() {
    cid=$(docker ps -aq --filter "name=${CONTAINER_NAME_BASE}-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && sleep 1s; fi
}

function remove_images() {
    # Remove images and the build cache
    iid=$(docker images \
      --filter=reference=${ENDPOINT_IMAGE_NAME} \
      --filter=reference=${MICROSERVICE_IMAGE_NAME} \
      --format "{{.ID}}" \
    )
    if [[ ! -z "$iid" ]]; then docker rmi $iid && sleep 1s; fi

    docker buildx prune -f
}

function test_clean() {
    stop_containers
    remove_images
}

function main() {

    test_clean

    build_docker_images
    start_service

    validate_microservice

    test_clean

}

main