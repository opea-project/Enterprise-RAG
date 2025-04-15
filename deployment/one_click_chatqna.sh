#!/bin/bash
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

# Function to display usage information
usage() {
    echo "Usage: $0  -g HUG_TOKEN [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d [PIPELINE] -t [TAG] -y [REGISTRY_NAME] [-r REGISTRY_PATH] [--features FEATURES]"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

PIPELINE=gaudi_torch_guard
TAG=latest
REGISTRY_NAME=localhost:5000
REGISTRY_PATH=erag
FEATURES=""

# Parse command-line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -g) HUG_TOKEN="$2"; shift 2 ;;
        -p) RAG_HTTP_PROXY="$2"; shift 2 ;;
        -u) RAG_HTTPS_PROXY="$2"; shift 2 ;;
        -n) RAG_NO_PROXY="$2"; shift 2 ;;
        -d) PIPELINE="$2"; shift 2 ;;
        -t) TAG="$2"; shift 2 ;;
        -a) ALTERNATE_TAGGING="--use-alternate-tagging"; shift ;;
        -y) REGISTRY_NAME="$2"; shift 2 ;;
        -r) REGISTRY_PATH="$2"; shift 2 ;;
        --features) FEATURES="$2"; shift 2 ;;
        -*) echo "Unknown option: $1" >&2; usage ;;
        *) break ;;
    esac
done

# Check if mandatory parameters are provided
if [ -z "$HUG_TOKEN" ]; then
    usage
fi

# Setup the environment
bash configure.sh -p "$RAG_HTTP_PROXY" -u "$RAG_HTTPS_PROXY" -n "$RAG_NO_PROXY"

# Build images & push to local registry
bash update_images.sh --setup-registry --build --push --registry "$REGISTRY_NAME" --registry-path "$REGISTRY_PATH" --tag "$TAG" $ALTERNATE_TAGGING

# Set helm values
bash set_values.sh -p "$RAG_HTTP_PROXY" -u "$RAG_HTTPS_PROXY" -n "$RAG_NO_PROXY" -g "$HUG_TOKEN"

# Verify kubectl
if ! command_exists kubectl; then
    echo "Make sure that kubectl is installed"
    exit 1
fi

if [ -n "$FEATURES" ]; then
  bash ./install_chatqna.sh --deploy "$PIPELINE" --telemetry --auth --ui --registry "$REGISTRY_NAME/$REGISTRY_PATH" --tag "$TAG" $ALTERNATE_TAGGING --test --features "$FEATURES"
else
  bash ./install_chatqna.sh --deploy "$PIPELINE" --telemetry --auth --ui --registry "$REGISTRY_NAME/$REGISTRY_PATH" --tag "$TAG" $ALTERNATE_TAGGING --test
fi
