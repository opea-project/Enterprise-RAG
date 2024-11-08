#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail


echo "USE WITH CAUTION THIS SCRIPT USES SUDO PRIVILAGES TO INSTALL NEEDED PACKAGES LOCALLY AND CONFIGURE THEM. \
USING IT MAY OVERWRITE EXISTING CONFIGURATION. Press ctrl+c to cancel. Sleeping for 30s." && sleep 30


GOROOT=/usr/local/go
GOPATH=$HOME/go
ENV_FILE_NAME=.env

usage() {
    echo "Usage: $0 -g HUG_TOKEN [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY]"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# !TODO this should be changed to use non-positional parameters
# Parse command-line arguments
while getopts "p:u:n:" opt; do
    case $opt in
        p) RAG_HTTP_PROXY="$OPTARG";;
        u) RAG_HTTPS_PROXY="$OPTARG";;
        n) RAG_NO_PROXY="$OPTARG,.cluster.local";;
        *) usage ;;
    esac
done

# Update package list
sudo apt-get update -q

# Install packages
sudo apt-get install -y -q build-essential make zip jq apt-transport-https ca-certificates curl software-properties-common

# Install Docker if not already installed
if command_exists docker; then
    echo "Docker is already installed."
else
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo bash get-docker.sh --version 25.0.1
    rm get-docker.sh

    sudo usermod -aG docker "$USER"

    if command_exists docker; then
        echo "Docker installation successful."
    else
        echo "Docker installation failed."
        exit 1
    fi
fi

# Configure Docker proxy settings if provided
if [[ -n "$RAG_HTTP_PROXY" || "$RAG_HTTPS_PROXY" || "$RAG_NO_PROXY" ]]; then
    export RAG_HTTP_PROXY
    export RAG_HTTPS_PROXY
    export RAG_NO_PROXY
    envsubst < tpl/config.json.tpl > tmp.config.json
    if [ -e ~/.docker/config.json ]; then
        echo "Warning! Docker config.json exists; continues using the existing file"
    else
        if [ ! -d ~/.docker/ ]; then
            mkdir ~/.docker
        fi
        mv tmp.config.json ~/.docker/config.json
        sudo systemctl restart docker
        echo "Created Docker config.json, restarting docker.service"
    fi
fi

# Install Go if not already installed
if [ -f $ENV_FILE_NAME ]; then
    # shellcheck disable=SC1090
    source $ENV_FILE_NAME
fi

if command_exists go; then
    echo "Go is already installed."
else
    wget https://go.dev/dl/go1.22.1.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.22.1.linux-amd64.tar.gz
    rm go1.22.1.linux-amd64.tar.gz

    if [ -f $ENV_FILE_NAME ]; then
        echo "Warning! $ENV_FILE_NAME exists; continues using the existing file"
    else
        cat <<EOL > $ENV_FILE_NAME
export GOROOT=$GOROOT
export GOPATH=$GOPATH
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
EOL
    fi

    # shellcheck disable=SC1090
    source $ENV_FILE_NAME

    if command_exists go; then
        echo "Go installation successful."
    else
        echo "Go installation failed."
        exit 1
    fi
fi

# Install Helm if not already installed
if command_exists helm; then
    echo "Helm is already installed."
else
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    bash get_helm.sh --version 3.16.1
    rm get_helm.sh

    if command_exists helm; then
        echo "Helm installation successful."
    else
        echo "Helm installation failed."
        exit 1
    fi
fi

# OpenTelemetry contrib journals/systemd collector requires plenty of inotify instances or it fails
# without error occurs: "Insufficient watch descriptors available. Reverting to -n." (in journalctl receiver)
[[ $(sudo sysctl -n fs.inotify.max_user_instances) -lt 8000 ]] && sudo sysctl -w fs.inotify.max_user_instances=8192

echo "All installations and configurations are complete."
