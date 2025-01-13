#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')

function check_prerequisites() {
    if [ -z "${HF_TOKEN}" ]; then
        test_fail "HF_TOKEN environment variable is not set. Exiting."
    fi

    if [ -z "${RERANKER_TEI_PORT}" ]; then
        test_fail "RERANKER_TEI_PORT environment variable is not set. Exiting."
    fi

}

function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function build_docker_images() {
    docker compose \
        -f ${WORKPATH}/comps/reranks/impl/model_server/tei/docker/docker-compose.yaml \
        build
}

function start_service() {
    docker compose \
        -f ${WORKPATH}/comps/reranks/impl/model_server/tei/docker/docker-compose.yaml \
        up -d
    sleep 1m
}

function validate_microservice() {
    # Command errors here are not exceptions, but handled as test fails.
    set +e

    unset http_proxy
    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${RERANKER_TEI_PORT}/rerank \
        -X POST \
        -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
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

function test_clean() {
    docker compose \
        -f ${WORKPATH}/comps/reranks/impl/model_server/tei/docker/docker-compose.yaml \
        down
}

function main() {
    source "${WORKPATH}/comps/reranks/impl/model_server/tei/docker/.env"
    check_prerequisites
    test_clean

    build_docker_images
    start_service
    validate_microservice

    test_clean
}

main
