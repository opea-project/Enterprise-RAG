#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# This test checks llms microservice by sending request and verifying 200 response code.
# Model server: TGI
# Requires HF_TOKEN : Hugging Face auth token

set -xe

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')
LLMS_DOCKER_PATH="${WORKPATH}/comps/llms/impl/model_server/tgi/docker"
COMPOSE_FILE="docker-compose-cpu.yaml"
USVC_PORT=9000

function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function check_prerequisites() {
    if [ -z "${HF_TOKEN}" ]; then
        test_fail "HF_TOKEN environment variable is not set. Exiting."
    fi
}

function build_docker_images() {
    cd "${LLMS_DOCKER_PATH}"
    docker compose \
        --env-file=.env.cpu \
        -f ${COMPOSE_FILE} \
        build
}

function start_service() {
    cd "${LLMS_DOCKER_PATH}"
    docker compose \
        --env-file=.env.cpu \
        -f ${COMPOSE_FILE} \
        up -d
    sleep 2m
}

function check_readiness() {
    # Check microservice with TGI is fully ready.
    # Delays are to be expected due to TGI/LLM download.

    # values unit is seconds
    wait_pause=5
    timeout=120
    total_wait=0

    usvc_ready="false"

    # Curl errors here are not exceptions, but readiness check trial
    set +e
    until [[ ${total_wait} -ge ${timeout} ]] || [[ "${usvc_ready}" == "true" ]]; do
        curl http://localhost:9000/v1/health_check \
            -X GET \
            -H 'Content-Type: application/json'

        if [ $? -eq 0 ]; then
            usvc_ready="true"
            break
        fi

        sleep "${wait_pause}s"
        (( total_wait += wait_pause ))
    done
    set -e

    if [[ "${usvc_ready}" != "true" ]]; then
        cd "${LLMS_DOCKER_PATH}"
        echo "Compose readiness check exceeded timeout. Print logs:"
        docker compose -f ${COMPOSE_FILE} logs
        test_fail "Docker compose is not ready after timeout."
    fi
}

function validate_microservice() {
    # Command errors here are not exceptions, but handled as test fails.
    set +e

    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${USVC_PORT}/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
        -H 'Content-Type: application/json' \
    )

    http_status=$(echo $http_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    if [ "$http_status" -ne "200" ]; then
        test_fail "HTTP status is not 200. Received status was $http_status"
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
    cd "${LLMS_DOCKER_PATH}"
    docker compose \
        -f ${COMPOSE_FILE} \
        down
}

function main() {

    check_prerequisites
    test_clean

    build_docker_images
    start_service
    check_readiness
    validate_microservice

    test_clean

}

main
