#!/bin/bash
# Query and display the deployment manifest ConfigMap
# Usage: ./query_deployment_manifest.sh [namespace]
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

NAMESPACE="${1:-default}"
LABEL_SELECTOR="app.kubernetes.io/name=erag-deployment,app.kubernetes.io/component=deployment-manifest"

echo "=== ERAG Deployment Manifest ==="
echo

MANIFEST_COUNT=$(kubectl get cm -n "$NAMESPACE" -l "$LABEL_SELECTOR" --no-headers 2>/dev/null | wc -l)

if [ "$MANIFEST_COUNT" -eq 0 ]; then
    echo "ERROR: Deployment manifest not found in namespace '$NAMESPACE'"
    echo "The manifest is created after successful deployment."
    exit 1
fi

if [ "$MANIFEST_COUNT" -gt 1 ]; then
    echo "WARNING: Multiple manifests found ($MANIFEST_COUNT). Using the first one."
fi

kubectl get cm -n "$NAMESPACE" -l "$LABEL_SELECTOR" -o jsonpath='{.items[0].data.manifest\.yaml}'
