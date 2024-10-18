#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')

CONTAINER_NAME_BASE="test-retriever"

REDIS_PORT=6379
REDIS_IMAGE_NAME="redis/redis-stack:7.2.0-v9"
REDIS_CONTAINER_NAME="${CONTAINER_NAME_BASE}-redis"

INGESTION_API_PORT=6120
INGESTION_CONTAINER_NAME="${CONTAINER_NAME_BASE}-ingestion"
INGESTION_IMAGE_NAME="opea/${INGESTION_CONTAINER_NAME}:comps"

RETRIEVER_API_PORT=6620
RETRIEVER_CONTAINER_NAME="${CONTAINER_NAME_BASE}-microservice"
RETRIEVER_IMAGE_NAME="opea/${RETRIEVER_CONTAINER_NAME}:comps"


function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function build_docker_images() {
    cd $WORKPATH

    # Redis
    docker pull ${REDIS_IMAGE_NAME}
    # Ingestion service (to populate database before the test)
    docker build --no-cache -t ${INGESTION_IMAGE_NAME} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/ingestion/impl/microservice/Dockerfile .
    # Retriever
    docker build --no-cache -t ${RETRIEVER_IMAGE_NAME} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/impl/microservice/Dockerfile .
}

function start_service() {
    # Redis
    docker run -d --name ${REDIS_CONTAINER_NAME} \
        -p ${REDIS_PORT}:${REDIS_PORT} \
        ${REDIS_IMAGE_NAME}

    # Ingestion
    docker run -d --name ${INGESTION_CONTAINER_NAME} \
        -e VECTOR_STORE=redis \
        --ipc=host \
        -e REDIS_URL="redis://${IP_ADDRESS}:${REDIS_PORT}" \
        -p ${INGESTION_API_PORT}:${INGESTION_API_PORT} \
        ${INGESTION_IMAGE_NAME}

    # Retriever
    docker run -d --name=${RETRIEVER_CONTAINER_NAME} \
        -p ${RETRIEVER_API_PORT}:${RETRIEVER_API_PORT} \
        -e REDIS_URL="redis://${IP_ADDRESS}:${REDIS_PORT}" \
        ${RETRIEVER_IMAGE_NAME}

    sleep 10s
}

function check_containers() {
    container_names=("${REDIS_CONTAINER_NAME}" "${INGESTION_CONTAINER_NAME}" "${RETRIEVER_CONTAINER_NAME}")
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

function populate_db() {
    unset http_proxy
    unset https_proxy
    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${INGESTION_API_PORT}/v1/ingestion \
        -X POST \
        -d '{ "docs": [{ "text": "What is deep learning?", "embedding": [1,2,3,4,5]},
            { "text": "Other text 2", "embedding": [0,-1,3,4,5]},
            { "text": "Distant embedding", "embedding": [-100,-100,-100,-100,-100]},
            { "text": "Other text 4", "embedding": [0,0,0,0,0]},
            { "text": "Other text 5", "embedding": [6,7,8,9,10]}] }' \
        -H 'Content-Type: application/json' \
    )
}

function validate_microservice() {
    set +e
    unset http_proxy
    unset https_proxy
    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${RETRIEVER_API_PORT}/v1/retrieval \
        -X POST \
        -d '{ "text": "What is deep learning?", "embedding": [1,2,3,4,5], "search_type": "similarity" }' \
        -H 'Content-Type: application/json'
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

    # Check if exactly 4 documents are returned
    # 4 is a default value for "-k" parameter which is not passed to the query
    retrieved_docs=$(echo $http_content | jq -r '.retrieved_docs | length')
    if [[ $retrieved_docs -ne 4 ]]; then
        test_fail "Invalid number of retrieved docs. Expected 1, got: ${retrieved_docs}. Response: ${http_content}"
    fi
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
      --filter=reference=${ENDPOINT_IMAGE_NAME} \
      --filter=reference=${INGESTION_IMAGE_NAME} \
      --format "{{.ID}}" \
    )
    if [[ ! -z "$iid" ]]; then docker rmi $iid && sleep 1s; fi
}

function test_clean() {
    purge_containers
    remove_images
}

function main() {
    test_clean
    build_docker_images
    start_service
    check_containers
    populate_db
    validate_microservice
    test_clean
}

main
