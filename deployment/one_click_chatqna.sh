#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

# Function to display usage information
usage() {
  echo "Usage: $0  -g HUG_TOKEN -z GRAFANA_PASSWORD -k KEYCLOAK_ADMIN_PASSWORD -i IP [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d [PIPELINE] -t [TAG] -y [REGISTRY]"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

PIPELINE=gaudi_torch_in_out_guards
TAG=latest
REGISTRY=localhost:5000

# Parse command-line arguments
# !TODO this should be changed to use non-positional parameters
while getopts "g:z:p:u:n:d:t:y:i:k:" opt; do
    case $opt in
        g) HUG_TOKEN="$OPTARG";;
        z) GRAFANA_PASSWORD="$OPTARG" ;;
        p) RAG_HTTP_PROXY="$OPTARG";;
        u) RAG_HTTPS_PROXY="$OPTARG";;
        n) RAG_NO_PROXY="$OPTARG" ;;
        d) PIPELINE="$OPTARG" ;;
        t) TAG="$OPTARG" ;;
        y) REGISTRY="$OPTARG" ;;
        i) IP="$OPTARG" ;;
        k) KEYCLOAK_PASSWORD="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check if mandatory parameters are provided
if [ -z "$HUG_TOKEN" ] || [ -z "$GRAFANA_PASSWORD" ] || [ -z "$KEYCLOAK_PASSWORD" ] || [ -z "$IP" ]; then
    usage
fi

# Setup the environment
bash configure.sh -p "$RAG_HTTP_PROXY" -u "$RAG_HTTPS_PROXY" -n "$RAG_NO_PROXY"

# Build images & push to local registry
bash update_images.sh --setup-registry --build --push --registry "$REGISTRY" --tag "$TAG"

# Set helm values
bash set_values.sh -p "$RAG_HTTP_PROXY" -u "$RAG_HTTPS_PROXY" -n "$RAG_NO_PROXY" -g "$HUG_TOKEN"

# Verify kubectl
if ! command_exists kubectl; then
    echo "Make sure that kubectl is installed"
    exit 1
fi

# Install chatqna & run test
bash ./install_chatqna.sh --deploy "$PIPELINE" --telemetry --auth --ui --registry "$REGISTRY" --tag "$TAG" --test --grafana_password "$GRAFANA_PASSWORD" --ip "$IP" --keycloak_admin_password "$KEYCLOAK_PASSWORD"
