#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')

CONTAINER_NAME_BASE="test-ingestion"

REDIS_PORT=6379
REDIS_IMAGE_NAME="redis/redis-stack:7.2.0-v9"
REDIS_CONTAINER_NAME="${CONTAINER_NAME_BASE}-redis"

MICROSERVICE_API_PORT=6120
MICROSERVICE_CONTAINER_NAME="${CONTAINER_NAME_BASE}-microservice"
MICROSERVICE_IMAGE_NAME="opea/${MICROSERVICE_CONTAINER_NAME}:comps"


function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function build_docker_images() {
    cd $WORKPATH

    docker pull ${REDIS_IMAGE_NAME}
    docker build -t ${MICROSERVICE_IMAGE_NAME} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/ingestion/impl/microservice/Dockerfile .
}

function start_service() {

    docker run -d --name ${REDIS_CONTAINER_NAME} \
        -p ${REDIS_PORT}:${REDIS_PORT} \
        ${REDIS_IMAGE_NAME}

    docker run -d --name ${MICROSERVICE_CONTAINER_NAME} \
        -e VECTOR_STORE=redis \
        --ipc=host \
        -e REDIS_URL="redis://${IP_ADDRESS}:${REDIS_PORT}" \
        -p ${MICROSERVICE_API_PORT}:${MICROSERVICE_API_PORT} \
        ${MICROSERVICE_IMAGE_NAME}

    sleep 10s
}

function check_containers() {
    container_names=("${REDIS_CONTAINER_NAME}" "${MICROSERVICE_CONTAINER_NAME}")
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
    set +e
    unset http_proxy
    unset https_proxy
    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${MICROSERVICE_API_PORT}/v1/ingestion \
        -X POST \
        -d '{ "docs": [{ "text": "qwerty", "embedding": [1,2,3]}] }' \
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

    # Check if the value passed through the microservice API
    # is actually propagated properly into Redis
    redis_key=$( docker exec ${REDIS_CONTAINER_NAME} redis-cli keys '*' )
    if [[ -z "$redis_key" ]]; then
        test_fail "No data has been propagated into Redis."
    fi

    key_content=$( docker exec ${REDIS_CONTAINER_NAME} redis-cli hgetall ${redis_key} )
    if [[ ! $key_content =~ "qwerty" ]]; then
        test_fail "Invalid value of the key: ${redis_key}, actual value: ${key_content}, expected value: qwerty"
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
      --filter=reference=${ENDPOINT_IMAGE_NAME} \
      --filter=reference=${MICROSERVICE_IMAGE_NAME} \
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
    validate_microservice
    test_clean
}

main
