#! /bin/bash
# Copyright (C) 2024-2026 Intel Corporation
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

NAMESPACE=docsum
CLIENT_POD=""
accessUrl=""

POD_EXISTS=$(kubectl get pod -n $NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})

if [ -z "$POD_EXISTS" ]; then
    kubectl apply -f client_test/client-test.yaml -n $NAMESPACE
fi

kubectl wait --for=condition=available --timeout=500s deployment/client-test -n $NAMESPACE

export CLIENT_POD=$(kubectl get pod -n $NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
export accessUrl=$(kubectl get gmc -n $NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='$NAMESPACE')].status.accessUrl}")

echo "Connecting to the server through the pod $CLIENT_POD using URL $accessUrl..."
echo ""

# Test 1: File-based summarization with base64 encoded content
echo "=========================================="
echo "Test 1: Summarizing a file (base64 encoded)"
echo "=========================================="

# Encode file content into base64 - -w option is required to avoid new line characters
file_content=$(cat ./scripts/ai_overview.txt | base64 -w 0)
IF_STREAM=false

JSON_PAYLOAD_FILE='{
    "files": [
        {
            "filename": "ai_overview.txt",
            "data64": "'"${file_content}"'"
        }
    ],
    "links": [],
    "parameters": {
        "stream": "'"${IF_STREAM}"'",
        "summary_type": "map_reduce",
        "chunk_size": 2048
    }
}'


kubectl exec "$CLIENT_POD" -n $NAMESPACE -- \
    curl --no-buffer -s $accessUrl -X POST -d "$JSON_PAYLOAD_FILE" -H 'Content-Type: application/json'

test_return_code=$?

# !TODO returns 0 if curl succeed, but answer was not proper
if [ $test_return_code -eq 0 ]; then
    echo "Test finished successfully"
else
    echo "Test failed with return code:$test_return_code"
fi
