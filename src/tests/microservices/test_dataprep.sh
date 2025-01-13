#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$(dirname "$PWD")")
IP_ADDRESS=$(hostname -I | awk '{print $1}')
CONTAINER_NAME_BASE="test-dataprep"
MICROSERVICE_PORT=9399
MICROSERVICE_CONTAINER_NAME="${CONTAINER_NAME_BASE}-endpoint"
MICROSERVICE_IMAGE_NAME="opea/${MICROSERVICE_CONTAINER_NAME}:comps"


function build_docker_images() {
    cd $WORKPATH
    docker build -t ${MICROSERVICE_IMAGE_NAME} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/impl/microservice/Dockerfile .
}

function start_service() {
    docker run -d --name "${MICROSERVICE_CONTAINER_NAME}" \
        -p ${MICROSERVICE_PORT}:${MICROSERVICE_PORT} \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        ${MICROSERVICE_IMAGE_NAME}
    sleep 10s
}

function validate_link_upload() {
    http_response_with_status_code=$(curl -X POST \
        --write-out "HTTPSTATUS:%{http_code}" \
        -H 'Content-Type: application/json' \
        -d '{"links": ["https://google.com"]}' \
        http://${IP_ADDRESS}:${MICROSERVICE_PORT}/v1/dataprep
    )
    basic_validate_response "$http_response_with_status_code"
}

function validate_microservice() {
    # Command errors here are not exceptions, but handled as test fails.
    set +e
    validate_link_upload
    validate_txt_file_upload
    validate_pdf_file_upload
    validate_docx_file_upload
    validate_doc_file_upload
    validate_json_file_upload
    validate_ppt_file_upload
    validate_pptx_file_upload
    validate_xls_file_upload
    validate_xlsx_file_upload
    validate_csv_file_upload
    validate_md_file_upload
    validate_html_file_upload
    validate_jsonl_file_upload
    validate_xml_file_upload
    validate_svg_file_upload
    set -e
}

function validate_txt_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.txt")
    basic_validate_response "$http_response_with_status_code"
    check_content "test_file_content" "$http_response_with_status_code"
    http_content=$(echo "$http_response_with_status_code" | sed 's/HTTPSTATUS.*//')

    # Check if file has been split into 2 chunks
    chunks=$( jq -r '.docs | length' <<< $http_content )
    if [[ $chunks -ne "2" ]]; then
        test_fail "Invalid chunk list size. *.txt file content has been split into ${chunks} chunks. Expected: 2. Response: ${http_content}"
    fi
}

function validate_pdf_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.pdf")
    basic_validate_response "$http_response_with_status_code"
    check_content "Please find our recommended suppliers" "$http_response_with_status_code"
}

function validate_docx_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.docx")
    basic_validate_response "$http_response_with_status_code"
    check_content "Docx file content with some images" "$http_response_with_status_code"
}

function validate_doc_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.doc")
    basic_validate_response "$http_response_with_status_code"
    check_content "Doc file content with some images" "$http_response_with_status_code"
}

function validate_html_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.html")
    basic_validate_response "$http_response_with_status_code"
    check_content "Change Content Example" "$http_response_with_status_code"
}

function validate_json_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.json")
    basic_validate_response "$http_response_with_status_code"
    check_content "City Central Library" "$http_response_with_status_code"
}

function validate_jsonl_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.jsonl")
    basic_validate_response "$http_response_with_status_code"
    check_content "Los latinos en Estados Unidos" "$http_response_with_status_code"
}

function validate_md_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.md")
    basic_validate_response "$http_response_with_status_code"
    check_content "This document demonstrates the basic syntax of Markdown" "$http_response_with_status_code"
}

function validate_ppt_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.ppt")
    basic_validate_response "$http_response_with_status_code"
    check_content "PPT WITH SOME TEXT, IMAGES, AND OTHER" "$http_response_with_status_code"
}

function validate_pptx_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.pptx")
    basic_validate_response "$http_response_with_status_code"
    check_content "pptx with some text, images, and other" "$http_response_with_status_code"
}

function validate_xls_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.xls")
    basic_validate_response "$http_response_with_status_code"
    check_content "boolean" "$http_response_with_status_code"
}

function validate_xlsx_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.xlsx")
    basic_validate_response "$http_response_with_status_code"
    check_content "boolean" "$http_response_with_status_code"
}

function validate_xml_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.xml")
    basic_validate_response "$http_response_with_status_code"
    check_content "The Great Gatsby" "$http_response_with_status_code"
}

function validate_csv_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.csv")
    basic_validate_response "$http_response_with_status_code"
    check_content "EmployeeID FirstName LastName Department Salary" "$http_response_with_status_code"
}

function validate_yaml_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.yaml")
    basic_validate_response "$http_response_with_status_code"
    check_content "/path/to/certificate.crt" "$http_response_with_status_code"
}

function validate_svg_file_upload() {
    http_response_with_status_code=$(upload_file_curl "test_dataprep.svg")
    echo $http_response_with_status_code
    basic_validate_response "$http_response_with_status_code"
    check_content "Hello World" "$http_response_with_status_code"
}

function check_content() {
    expected_content="$1"
    http_response_with_status_code="$2"

    http_content=$(echo "$http_response_with_status_code" | sed 's/HTTPSTATUS.*//')
    if [[ ! $http_content =~ $expected_content ]]; then
        test_fail "File content is not present in the response. Actual response: ${http_content}"
    fi
}

function upload_file_curl() {
    file_to_upload="$1"
    http_response_with_status_code=$(curl -X POST --write-out "HTTPSTATUS:%{http_code}" -H 'Content-Type: application/json' -d @- http://${IP_ADDRESS}:${MICROSERVICE_PORT}/v1/dataprep << JSON_DATA
        {
            "files": [{
                "filename": "${file_to_upload}",
                "data64": "$(base64 -w 0 ./tests/files/dataprep_upload/${file_to_upload})"
            }]
        }
JSON_DATA
)
    echo $http_response_with_status_code
}

function basic_validate_response() {
    http_response="$1"

    http_status=$(echo "$http_response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    if [ "$http_status" -ne "200" ]; then
        test_fail "HTTP status is not 200. Received status was $http_status"
    fi

    http_content=$(echo "$http_response" | sed 's/HTTPSTATUS.*//')
    echo "${http_content}" | jq; parse_return_code=$?
    if [ "${parse_return_code}" -ne "0" ]; then
        test_fail "HTTP response content is not json parsable. Response content was: ${http_content}"
    fi
}

function check_containers() {
    container_names=("${MICROSERVICE_CONTAINER_NAME}")
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

function stop_docker() {
    cid=$(docker ps -aq --filter "name=${TEST_CONTAINER_PREFIX}-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
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
        --filter=reference=${MICROSERVICE_IMAGE_NAME} \
        --format "{{.ID}}" \
    )
    if [[ ! -z "$iid" ]]; then docker rmi $iid && sleep 1s; fi
}

function test_clean() {
    purge_containers
    remove_images
}

function test_fail() {
    echo "FAIL: ${1}" 1>&2
    test_clean
    exit 1
}

function main() {
    export no_proxy=${no_proxy},${IP_ADDRESS}
    test_clean
    build_docker_images
    start_service
    check_containers
    validate_microservice
    test_clean
}

main
