#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

HELM_VALUES_PATH=microservices-connector/helm/values.yaml

# Function to display usage information
usage() {
    echo "Usage: $0 -p [HTTP_PROXY] -u [HTTPS_PROXY] -n [NO_PROXY] -g [HUGGINGFACEHUB_API_TOKEN ] -r [REPOSITORY] -t [TAG]"
}

if [ $# -eq 0 ]; then
        echo "No parameters passed. Please provide at least one parameter"
        usage
        exit 1
fi

update_helm_value() {
local key="$1"
local value="$2"

if [ -n "$value" ]; then
    sed -i -E "s#(${key}) \"(.*)\"#\1 \"${value}\"#g" "$HELM_VALUES_PATH"
fi
}

# Parse command-line arguments; using RAG_* to prevent from pre exported variables
# !TODO this should be changed to use non-positional parameters
while getopts "p:u:n:g:r:t:" opt; do
    case $opt in
        p) RAG_HTTP_PROXY="$OPTARG" ;;
        u) RAG_HTTPS_PROXY="$OPTARG" ;;
        n) RAG_NO_PROXY="$OPTARG,cluster.local,monitoring,monitoring-traces" ;;
        g) RAG_HUG_TOKEN="$OPTARG" ;;
        r) RAG_REPOSITORY="$OPTARG" ;;
        t) RAG_TAG="$OPTARG" ;;
        *) usage; exit 1 ;;
    esac
done

# Change values if RAG
if [ -n "$RAG_HUG_TOKEN" ]; then update_helm_value ".*hugToken:" "$RAG_HUG_TOKEN" ;fi
if [ -n "$RAG_REPOSITORY" ]; then update_helm_value "^common_repository: &repo" "$RAG_REPOSITORY" ;fi
if [ -n "$RAG_TAG" ]; then update_helm_value "^common_tag: &tag" "$RAG_TAG" ;fi
if [ -n "$RAG_HTTP_PROXY" ]; then update_helm_value "httpProxy:" "$RAG_HTTP_PROXY" ;fi
if [ -n "$RAG_HTTPS_PROXY" ]; then update_helm_value "httpsProxy:" "$RAG_HTTPS_PROXY" ;fi
if [ -n "$RAG_NO_PROXY" ]; then update_helm_value "noProxy:" "$RAG_NO_PROXY" ;fi
