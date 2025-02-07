#! /bin/bash
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

# Function to handle errors
error_handler() {
    local error_code="$?"
    local error_command="$BASH_COMMAND"
    printf '%s\n' "Error in command: '$error_command' with exit code $error_code" >&2
    exit "$error_code"
}

# Trap all error signals and runs the aboves error handler
trap 'error_handler' ERR

NAMESPACE=dataprep
CLIENT_POD=""
accessUrl=""

POD_EXISTS=$(kubectl get pod -n $NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})

if [ -z "$POD_EXISTS" ]; then
    kubectl apply -f client_test/client-test.yaml -n $NAMESPACE
fi

kubectl wait --for=condition=available --timeout=300s deployment/client-test -n $NAMESPACE

export CLIENT_POD=$(kubectl get pod -n $NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
export accessUrl=$(kubectl get gmc -n $NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='$NAMESPACE')].status.accessUrl}")

echo "Connecting to the server through the pod $CLIENT_POD using URL $accessUrl..."

# encode content into base64 - -w option is required to avoid new line characters
content=$(echo -n "AVX-512 are 512-bit extensions to the 256-bit Advanced Vector Extensions SIMD instructions for x86 instruction set architecture" | base64 -w 0)

# JSON payload with encoded content
JSON_PAYLOAD='{
    "files": [
        {
            "filename": "file.txt",
            "data64": "'"${content}"'"
        }
    ],
    "links": []
}'

# run query with encoded content
kubectl exec "$CLIENT_POD" -n $NAMESPACE -- \
    curl --no-buffer -s $accessUrl -X POST -d "$JSON_PAYLOAD" -H 'Content-Type: application/json'

test_return_code=$?

# !TODO returns 0 if curl succeed, but answer was not proper
if [ $test_return_code -eq 0 ]; then
    echo "Test finished successfully"
else
    echo "Test failed with return code:$test_return_code"
fi
