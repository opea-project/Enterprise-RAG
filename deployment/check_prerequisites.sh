#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


HELM_VERSION=v3.16.1
DOCKER_VERSION=25.0.1
K8S_VERSION=1.29
HABANA_PLUGIN_POD_NAME=habanalabs-device-plugin-daemonset
HABANA_PLUGIN_NAMESPACE=habana-system
CSI_PROVISIONER=local-path-storage
CSI_PROVISIONER_NAME=local-path-provisioner
REMOTE_PREREQUISITE_SCRIPT_PATH=$(pwd)/check_prerequisites_remote.sh

# Set flags
REMOTE=""
all_requirements_met=true

function usage() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "\t--remote <USER@IP>: Execute remote checks for given host."
    echo -e "\t-h|--help: Display this help message."
}

# Verify if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print error msg & set flag
print_err() {
    echo "Error: $1"; all_requirements_met=false
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --remote)
            shift
            REMOTE=$1
            if [ -z "$REMOTE" ]; then
                echo "--remote parameter must be passed with user@ip e.g. ./check_prerequisites.sh --remote user@ip"; exit 1
            fi
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown action $1"
            usage
            exit 1
            ;;
    esac
    shift
done

# Check Helm installation
if command_exists helm; then
    current_helm_version=$(helm version --short --client 2>&1)
    if [[ "$current_helm_version" =~ "$HELM_VERSION" ]]; then
        echo "Helm installation is correct."
    else
        print_err "Helm version is not $HELM_VERSION. Current version: $current_helm_version."
    fi
else
    print_err "Helm is not installed."
fi

# Check K8s installation
if command_exists kubectl; then
    current_k8s_version=$(kubectl version | grep Server | awk '{print $3}')
    if [[ "$current_k8s_version" =~ "$K8S_VERSION" ]]; then
            echo "Kubernetes cluster version is correct."
            # Check Gaudi k8s plugin
            if kubectl get pods -n "$HABANA_PLUGIN_NAMESPACE" 2>/dev/null | grep "$HABANA_PLUGIN_POD_NAME" > /dev/null 2>&1; then
                echo "Habana plugin is installed in cluster."
            else
                print_err "Habana plugin is not intalled in the cluster."
            fi
            # Check CSI local-path-provisioner
            if kubectl get deployments -n "$CSI_PROVISIONER" | grep -q "$CSI_PROVISIONER_NAME"; then
                echo "CSI local-path-provisioner is installed."
            else
                print_err "CSI local-path-provisioner is not installed."
            fi
        else
            print_err "Kubernetes cluster version is not $K8S_VERSION. Current version: $current_k8s_version."
    fi
else
    print_err "Kubectl command is not working."
fi

# Check Docker installation
if command_exists docker; then
    current_docker_version=$(docker --version | grep -oP 'Docker version \K[^\s,]+')
    if [[ "$current_docker_version" =~ "$DOCKER_VERSION" ]]; then
            echo "Docker installation is correct."
        else
            print_err "Docker version is not $DOCKER_VERSION. Current version: $current_docker_version."
    fi
else
    print_err "Docker is not installed."
fi

# Check apt packages
if ! command_exists aws; then
    print_err "awscli is not installed."
fi

if ! command_exists make; then
    print_err "make is not installed."
fi

if ! command_exists zip; then
    print_err "zip is not installed."
fi

# Execute remote prerequisites
if [ -z "$REMOTE" ]; then
    if bash "$REMOTE_PREREQUISITE_SCRIPT_PATH"; then
        echo "All additional prerequisites for localhost are satisfied."
    else
        all_requirements_met=false
    fi
else
    if ssh "$REMOTE" "bash -s" < "${REMOTE_PREREQUISITE_SCRIPT_PATH}"; then
        echo "All remote prerequisites for $REMOTE are satisfied."
    else
        all_requirements_met=false
    fi
fi

if $all_requirements_met; then
    echo "Every requirement is satisfied."
else
    echo "Fix printed errors."
    exit 1
fi
