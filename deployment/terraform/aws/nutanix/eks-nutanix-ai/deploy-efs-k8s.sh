#!/bin/bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# Script to deploy EFS-enabled Kubernetes resources
# This script requires terraform to be applied first and kubectl to be configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}EFS Kubernetes Deployment Script${NC}"
echo "=================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if terraform is available
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform is not installed or not in PATH${NC}"
    exit 1
fi

# Get EFS information from Terraform outputs
echo -e "${YELLOW}Getting EFS information from Terraform...${NC}"

EFS_FILE_SYSTEM_ID=$(terraform output -raw efs_file_system_id 2>/dev/null)
EFS_ACCESS_POINT_ID=$(terraform output -raw efs_access_point_id 2>/dev/null)

if [ -z "$EFS_FILE_SYSTEM_ID" ] || [ -z "$EFS_ACCESS_POINT_ID" ]; then
    echo -e "${RED}Error: Could not get EFS information from Terraform outputs${NC}"
    echo "Make sure you have run 'terraform apply' first"
    exit 1
fi

echo "EFS File System ID: $EFS_FILE_SYSTEM_ID"
echo "EFS Access Point ID: $EFS_ACCESS_POINT_ID"

# Create temporary file with substituted values
TEMP_FILE=$(mktemp)
sed "s/\${EFS_FILE_SYSTEM_ID}/$EFS_FILE_SYSTEM_ID/g; s/\${EFS_ACCESS_POINT_ID}/$EFS_ACCESS_POINT_ID/g" efs-example.yaml > "$TEMP_FILE"

# Check if EKS cluster is accessible
echo -e "${YELLOW}Checking EKS cluster connectivity...${NC}"
if ! kubectl get nodes &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to EKS cluster${NC}"
    echo "Make sure you have configured kubectl to connect to your EKS cluster:"
    echo "aws eks update-kubeconfig --region us-east-1 --name \$(terraform output -raw cluster_name)"
    rm "$TEMP_FILE"
    exit 1
fi

# Apply the Kubernetes resources
echo -e "${YELLOW}Applying Kubernetes resources...${NC}"
kubectl apply -f "$TEMP_FILE"

# Clean up
rm "$TEMP_FILE"

echo -e "${GREEN}EFS Kubernetes resources deployed successfully!${NC}"
echo
echo "To check the status of your resources:"
echo "  kubectl get storageclass efs-sc"
echo "  kubectl get pv efs-pv"
echo "  kubectl get pvc efs-claim"
