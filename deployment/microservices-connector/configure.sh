#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

usage() {
    echo "Usage: $0 -a AWS_ACCESS_KEY_ID -s AWS_SECRET_ACCESS_KEY -r REGION [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY]"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

while getopts "a:s:r:p:u:n:g:" opt; do
    case $opt in
        a) AWS_ACCESS_KEY_ID="$OPTARG" ;;
        s) AWS_SECRET_ACCESS_KEY="$OPTARG" ;;
        r) REGION="$OPTARG" ;;
        p) HTTP_PROXY="$OPTARG" ;;
        u) HTTPS_PROXY="$OPTARG" ;;
        n) NO_PROXY="$OPTARG,.cluster.local" ;;
        g) HUG_TOKEN="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$REGION" ]; then
    usage
fi

# Update package list
sudo apt-get update -q

# Install packages
sudo apt-get install -y -q build-essential zip

# Install Docker if not already installed
if command_exists docker; then
    echo "Docker is already installed."
else
    sudo apt-get install -y -q apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
    sudo apt-get update -q
    sudo apt-get install -y -q docker-ce
    sudo mkdir -p /etc/systemd/system/docker.service.d

    if command_exists docker; then
        echo ""
        echo "Docker installation successful."
        echo ""
    else
        echo ""
        echo "Docker installation failed."
        echo ""
        exit 1
    fi

fi

# Configure Docker proxy settings if provided
if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ] || [ -n "$NO_PROXY" ]; then
    sudo mkdir -p /etc/systemd/system/docker.service.d
    sudo tee /etc/systemd/system/docker.service.d/proxy.conf > /dev/null <<EOF
[Service]
EOF
    [ -n "$HTTP_PROXY" ] && echo "Environment=\"HTTP_PROXY=$HTTP_PROXY\"" | sudo tee -a /etc/systemd/system/docker.service.d/proxy.conf > /dev/null
    [ -n "$HTTPS_PROXY" ] && echo "Environment=\"HTTPS_PROXY=$HTTPS_PROXY\"" | sudo tee -a /etc/systemd/system/docker.service.d/proxy.conf > /dev/null
    [ -n "$NO_PROXY" ] && echo "Environment=\"NO_PROXY=$NO_PROXY\"" | sudo tee -a /etc/systemd/system/docker.service.d/proxy.conf > /dev/null

    mkdir -p ~/.docker/
    sudo tee ~/.docker/config.json > /dev/null <<EOF
{
  "proxies": {
    "default": {
EOF
    [ -n "$HTTP_PROXY" ] && echo "      \"httpProxy\": \"$HTTP_PROXY\"," | sudo tee -a ~/.docker/config.json > /dev/null
    [ -n "$HTTPS_PROXY" ] && echo "      \"httpsProxy\": \"$HTTPS_PROXY\"" | sudo tee -a ~/.docker/config.json > /dev/null
    echo "    }" | sudo tee -a ~/.docker/config.json > /dev/null
    echo "  }" | sudo tee -a ~/.docker/config.json > /dev/null
    echo "}" | sudo tee -a ~/.docker/config.json > /dev/null

    sudo systemctl daemon-reload
    sudo systemctl restart docker
fi

# Install Go if not already installed
source ~/.profile
if command_exists go; then
    echo ""
    echo "Go is already installed."
    echo ""
else
    wget https://go.dev/dl/go1.22.1.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.22.1.linux-amd64.tar.gz
    rm go1.22.1.linux-amd64.tar.gz

    echo '
    export GOROOT=/usr/local/go
    export GOPATH=$HOME/go
    export PATH=$GOPATH/bin:$GOROOT/bin:$PATH' >> ~/.profile

    source ~/.profile

    if command_exists go; then
        echo ""
        echo "Go installation successful."
        echo ""
    else
        echo ""
        echo "Go installation failed."
        echo ""
        exit 1
    fi
fi

# Install Helm if not already installed
if command_exists helm; then
    echo ""
    echo "Helm is already installed."
    echo ""
else
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    chmod +x get_helm.sh
    ./get_helm.sh
    rm get_helm.sh

    if command_exists helm; then
        echo ""
        echo "Helm installation successful."
        echo ""
    else
        echo ""
        echo "Helm installation failed."
        echo ""
        exit 1
    fi
fi

# Install and configure aws cli
if ! command_exists aws; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install -i /usr/local/aws/ -b /usr/local/bin
    rm -rf awscliv2.zip ./aws
fi

aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set default.region "$REGION"
aws configure set default.output json

echo ""
echo "All installations and configurations are complete."
echo ""

# Prepare directories and set values.yaml
sudo mkdir -p /mnt/opea-models
bash ./set_values.sh -g "$HUG_TOKEN"
