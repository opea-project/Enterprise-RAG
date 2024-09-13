#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Function to display usage information
usage() {
    echo "Usage: $0 -a AWS_ACCESS_KEY_ID -s AWS_SECRET_ACCESS_KEY -r REGION [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -g HUG_TOKEN"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Parse command-line arguments
while getopts "a:s:r:p:u:n:g:" opt; do
    case $opt in
        a) AWS_ACCESS_KEY_ID="$OPTARG" ;;
        s) AWS_SECRET_ACCESS_KEY="$OPTARG" ;;
        r) REGION="$OPTARG" ;;
        p) HTTP_PROXY="$OPTARG" ;;
        u) HTTPS_PROXY="$OPTARG" ;;
        n) NO_PROXY="$OPTARG" ;;
        g) HUG_TOKEN="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check if mandatory parameters are provided
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$REGION" ] || [ -z "$HUG_TOKEN" ]; then
    usage
fi

# Setup the environment
bash ./configure.sh -a "$AWS_ACCESS_KEY_ID" -s "$AWS_SECRET_ACCESS_KEY" -r "$REGION" -p "$HTTP_PROXY" -u "$HTTPS_PROXY" -n "$NO_PROXY" -g "$HUG_TOKEN"

# Deploy the microservices 
if ! command_exists kubectl; then
    echo "Make sure that kubectl is installed"
    exit 1
fi

# By default deploys the gaudi pipeline with dataprep and telemetry
bash ./install_chatqna.sh --deploy xeon_torch --auth --ui

# Run connection test
bash test_connection.sh
