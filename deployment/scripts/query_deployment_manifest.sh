#!/bin/bash
# Query and display the deployment manifest ConfigMap
# Usage: ./query_deployment_manifest.sh [namespace]
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

NAMESPACE="${1:-default}"
LABEL_SELECTOR="app.kubernetes.io/name=erag-deployment,app.kubernetes.io/component=deployment-manifest"

echo "=== ERAG Deployment Manifest ==="
echo

# Check if kubectl can connect to cluster
if ! kubectl cluster-info &>/dev/null; then
    echo "ERROR: Cannot connect to Kubernetes cluster"
    if [ -z "$KUBECONFIG" ]; then
        echo "KUBECONFIG is not set. Set it to your cluster config file."
    else
        echo "KUBECONFIG is set to: $KUBECONFIG"
        if [ ! -f "$KUBECONFIG" ]; then
            echo "File does not exist: $KUBECONFIG"
        fi
    fi
    exit 2
fi

MANIFEST_OUTPUT=$(kubectl get cm -n "$NAMESPACE" -l "$LABEL_SELECTOR" --no-headers 2>&1)
MANIFEST_RC=$?

if [ $MANIFEST_RC -ne 0 ]; then
    echo "ERROR: Failed to query manifests: $MANIFEST_OUTPUT"
    exit 1
fi

MANIFEST_COUNT=$(echo "$MANIFEST_OUTPUT" | grep -c . 2>/dev/null || echo 0)

if [ "$MANIFEST_COUNT" -eq 0 ] || [ -z "$MANIFEST_OUTPUT" ]; then
    echo "No deployment manifest found in namespace '$NAMESPACE'"
    echo "The manifest is created after successful deployment."
    exit 0
fi

if [ "$MANIFEST_COUNT" -gt 1 ]; then
    echo "WARNING: Multiple manifests found ($MANIFEST_COUNT). Using the first one."
fi

kubectl get cm -n "$NAMESPACE" -l "$LABEL_SELECTOR" -o jsonpath='{.items[0].data.manifest\.yaml}'
