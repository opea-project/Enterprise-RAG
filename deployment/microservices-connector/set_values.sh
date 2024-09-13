#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

helm_values_path=helm/values.yaml

# Function to display usage information
usage() {
    echo "Usage: $0 -g HUG_TOKEN"
    exit 1
}

# Parse command-line arguments
while getopts "g:" opt; do
    case $opt in
        g) HUG_TOKEN="$OPTARG" ;;
        *) usage ;;
    esac
done

# Change values
sed -i -E "s/(.*hugToken): \"(.*)\"/\1: \"${HUG_TOKEN}\"/g" $helm_values_path
