#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

# Function to display usage information
usage() {
    echo "Usage: $0  -g HUG_TOKEN -a [AWS_ACCESS_KEY_ID] -s [AWS_SECRET_ACCESS_KEY] -r [REGION] [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d [PIPELINE] -t [TAG] -y [REGISTRY]"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

PIPELINE=gaudi_torch_guard
TAG=latest
REGISTRY=localhost:5000

# Parse command-line arguments
# !TODO this should be changed to use non-positional parameters
while getopts "g:a:s:r:p:u:n:d:t:y:" opt; do
    case $opt in
        g) HUG_TOKEN="$OPTARG";;
        a) AWS_ACCESS_KEY_ID="$OPTARG";;
        s) AWS_SECRET_ACCESS_KEY="$OPTARG";;
        r) REGION="$OPTARG";;
        p) RAG_HTTP_PROXY="$OPTARG";;
        u) RAG_HTTPS_PROXY="$OPTARG";;
        n) RAG_NO_PROXY="$OPTARG" ;;
        d) PIPELINE="$OPTARG" ;;
        t) TAG="$OPTARG" ;;
        y) REGISTRY="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check if mandatory parameters are provided
if [ -z "$HUG_TOKEN" ]; then
    usage
fi

# Setup the environment
bash configure.sh -a "$AWS_ACCESS_KEY_ID" -s "$AWS_SECRET_ACCESS_KEY" -r "$REGION" -p "$RAG_HTTP_PROXY" -u "$RAG_HTTPS_PROXY" -n "$RAG_NO_PROXY"

# Build images & push to local registry
bash update_images.sh --setup-registry --build --push --registry "$REGISTRY" --version "$TAG"

# Set helm values
bash set_values.sh -p "$RAG_HTTP_PROXY" -u "$RAG_HTTPS_PROXY" -n "$RAG_NO_PROXY" -g "$HUG_TOKEN"

# Open tunel for remote host
# !TODO kill tunneling
if [ -n "$REMOTE" ]; then
   echo "Forwarding docker registry on port 5000"
   nohup ssh -R 5000:5000 "$REMOTE" >> 5000-registry-tunnel.out 2>&1 &
fi


# Verify kubectl
if ! command_exists kubectl; then
    echo "Make sure that kubectl is installed"
    exit 1
fi

# Install chatqna
bash ./install_chatqna.sh --deploy "$PIPELINE" --telemetry --ui --tag "$TAG" --test
