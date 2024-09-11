#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')

CONTAINER_NAME_BASE="test-reranks"

MODEL_SERVER_CONTAINER_NAME="${CONTAINER_NAME_BASE}-model-server"
MODEL_SERVER_IMAGE_NAME="ghcr.io/huggingface/text-embeddings-inference:cpu-1.2"
MODEL_SERVER_HOST_PORT=5006

MICROSERVICE_CONTAINER_NAME="${CONTAINER_NAME_BASE}-microservice"
MICROSERVICE_IMAGE_NAME="opea/${MICROSERVICE_CONTAINER_NAME}:comps"
MICROSERVICE_API_PORT=5007

function check_prerequisites() {
    if [ -z "${HF_TOKEN}" ]; then
        test_fail "HF_TOKEN environment variable is not set. Exiting."
    fi
}

function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache \
        -t ${MICROSERVICE_IMAGE_NAME} \
        -f comps/reranks/impl/microservice/Dockerfile .
}

function start_service() {
    model="BAAI/bge-reranker-large"
    revision="refs/pr/4"

    docker run -d --name="${MODEL_SERVER_CONTAINER_NAME}" \
        -p ${MODEL_SERVER_HOST_PORT}:80 \
        -v ./data:/data \
        --pull always \
        ${MODEL_SERVER_IMAGE_NAME} \
        --model-id $model \
        --revision $revision \

    export TEI_RERANKING_ENDPOINT="http://${IP_ADDRESS}:${MODEL_SERVER_HOST_PORT}"

    docker run -d --name="${MICROSERVICE_CONTAINER_NAME}" \
        -p ${MICROSERVICE_API_PORT}:8000 \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e TEI_RERANKING_ENDPOINT=$TEI_RERANKING_ENDPOINT \
        -e HF_TOKEN=$HF_TOKEN \
        ${MICROSERVICE_IMAGE_NAME}

    sleep 1m
}

function check_containers() {
  container_names=("${ENDPOINT_CONTAINER_NAME}" "${MICROSERVICE_CONTAINER_NAME}")
  failed_containers="false"

  for name in "${container_names[@]}"; do
    if [ "$( docker container inspect -f '{{.State.Status}}' "${name}" )" != "running" ]; then
      echo "Container '${name}' failed. Print logs:"
      docker logs "${name}"
      failed_containers="true"
    fi
  done

  if [[ "${failed_containers}" == "true" ]]; then
    test_fail "There are failed containers"
  fi
}

function validate_microservice() {
    # Command errors here are not exceptions, but handled as test fails.
    set +e

    unset http_proxy
    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${MICROSERVICE_API_PORT}/v1/reranking \
        -X POST \
        -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
        -H 'Content-Type: application/json' \
    )

    http_status=$(echo $http_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    if [ "$http_status" -ne "200" ]; then
        test_fail "HTTP status is not 200. Received status was $http_status"
		fi

    http_content=$(echo "$http_response" | sed 's/HTTPSTATUS.*//')
    echo "${http_content}" | jq; parse_return_code=$?
		if [ "${parse_return_code}" -ne "0" ]; then
        test_fail "HTTP response content is not json parsable. Response content was: ${http_content}"
		fi

		set -e
}

function purge_containers() {
    cids=$(docker ps -aq --filter "name=${CONTAINER_NAME_BASE}-*")
    if [[ ! -z "$cids" ]]
    then
      docker stop $cids
      docker rm $cids
    fi
}

function remove_images() {
    # Remove images and the build cache
    iid=$(docker images \
      --filter=reference=${MODEL_SERVER_IMAGE_NAME} \
      --filter=reference=${MICROSERVICE_IMAGE_NAME} \
      --format "{{.ID}}" \
    )
    if [[ ! -z "$iid" ]]; then docker rmi $iid && sleep 1s; fi

    docker buildx prune -f
}

function test_clean() {
    purge_containers
    remove_images
}

function main() {
    check_prerequisites
    test_clean

    build_docker_images
    start_service
    check_containers
    validate_microservice

    test_clean
}

main
