#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# This test checks embedding microservice by sending request and verifying 200 response code and response content.
# Framework: Langchain
# Moder server: OVMS

set -xe

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')

CONTAINER_NAME_BASE="test-comps-embeddings"

ENDPOINT_CONTAINER_DIR="./comps/embeddings/impl/model-server/ovms"
ENDPOINT_CONTAINER_NAME="${CONTAINER_NAME_BASE}-endpoint"
ENDPOINT_IMAGE_NAME="openvino/model_server:2024.3"
ENDPOINT_BUILD_VENV_NAME="test-embeddings-langchain-ovms-venv"
ENDPOINT_BUILD_VENV_SRC="${WORKPATH}/tests/${ENDPOINT_BUILD_VENV_NAME}"
ENDPOINT_MODEL_NAME="BAAI/bge-large-en-v1.5"
ENDPOINT_MODEL_NAME_SHORT="bge-large-en-v1.5"

MICROSERVICE_API_PORT=5005
MICROSERVICE_CONTAINER_NAME="${CONTAINER_NAME_BASE}-microservice"
MICROSERVICE_IMAGE_NAME="opea/${MICROSERVICE_CONTAINER_NAME}:comps"

function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function make_build_env() {
    cd $WORKPATH/tests

    # Dedicated Python env required to prepare OVMS model server.
    python3 -m venv ${ENDPOINT_BUILD_VENV_SRC}
    source ${ENDPOINT_BUILD_VENV_NAME}/bin/activate
    pip install -r https://raw.githubusercontent.com/openvinotoolkit/model_server/releases/2024/3/demos/continuous_batching/requirements.txt
    deactivate

    cd $WORKPATH/${ENDPOINT_CONTAINER_DIR}
    mkdir -p models
}

function load_model() {
    # This functions is specific to OVMS which needs model to pre-load
    model_full_name=$1
    model_short_name=$(echo "${model_full_name}" | cut -d "/" -f 2)
    embeddings_model_name="${model_short_name}_embeddings"
    tokenizer_model_name="${model_short_name}_tokenizer"

    cd $WORKPATH/tests
    source ${ENDPOINT_BUILD_VENV_NAME}/bin/activate

    cd $WORKPATH/${ENDPOINT_CONTAINER_DIR}
    optimum-cli export openvino --model "${model_full_name}" --task feature-extraction "models/${embeddings_model_name}"
    convert_tokenizer -o "models/${tokenizer_model_name}" --skip-special-tokens "${model_full_name}"
    python combine_models.py "models/${embeddings_model_name}" "models/${tokenizer_model_name}"

    deactivate
}

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)

    docker build --no-cache -t ${MICROSERVICE_IMAGE_NAME} -f comps/embeddings/impl/microservice/Dockerfile .
}

function delete_build_env() {
    if [ -d "${ENDPOINT_BUILD_VENV_SRC}" ]; then
      rm -rf "${ENDPOINT_BUILD_VENV_SRC}"
    fi

    if [ -d "$WORKPATH/${ENDPOINT_CONTAINER_DIR}/models" ]; then
      rm -rf "$WORKPATH/${ENDPOINT_CONTAINER_DIR}/models"
    fi
}

function start_service() {
    # In this test, this functions is not the only one which operates on model name
    model_full_name=$1
    model_short_name=$(echo "${model_full_name}" | cut -d "/" -f 2)
    internal_communication_port=9001
    unset http_proxy

    cd $WORKPATH/${ENDPOINT_CONTAINER_DIR}
    docker run -d --name ${ENDPOINT_CONTAINER_NAME} \
        --runtime runc \
        -p ${internal_communication_port}:${internal_communication_port} \
        -p 9000:9000 \
        -v "${WORKPATH}/${ENDPOINT_CONTAINER_DIR}/models/${model_short_name}_combined/:/model/1" \
        ${ENDPOINT_IMAGE_NAME} \
        --model_name ${model_short_name} \
        --model_path /model \
        --cpu_extension /ovms/lib/libopenvino_tokenizers.so \
        --port 9000 \
        --rest_port ${internal_communication_port} \
        --log_level DEBUG

    docker run -d --name ${MICROSERVICE_CONTAINER_NAME} \
        --runtime runc \
        -p ${MICROSERVICE_API_PORT}:6000 \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e EMBEDDING_MODEL_NAME="${model_full_name}" \
        -e EMBEDDING_MODEL_SERVER="ovms" \
        -e EMBEDDING_MODEL_SERVER_ENDPOINT="http://${IP_ADDRESS}:${internal_communication_port}" \
        --ipc=host \
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
    unset https_proxy

    http_response=$(curl \
        --write-out "HTTPSTATUS:%{http_code}" \
        http://${IP_ADDRESS}:${MICROSERVICE_API_PORT}/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
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
      --filter=reference=${ENDPOINT_IMAGE_NAME} \
      --filter=reference=${MICROSERVICE_IMAGE_NAME} \
      --format "{{.ID}}" \
    )
    if [[ ! -z "$iid" ]]; then docker rmi $iid && sleep 1s; fi

    docker buildx prune -f
}

function test_clean() {
    purge_containers
    remove_images
    delete_build_env
}

function main() {
    test_clean
    make_build_env
    load_model "${ENDPOINT_MODEL_NAME}"
    build_docker_images
    start_service "${ENDPOINT_MODEL_NAME_SHORT}"
    check_containers
    validate_microservice
    test_clean
}

main
