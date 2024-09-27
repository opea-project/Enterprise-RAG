#! /bin/bash
# Copyright (C) 2024 Intel Corporation
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

check_pods() {
    if kubectl get pods -n $NAMESPACE --no-headers -o custom-columns="NAME:.metadata.name,READY:.status.conditions[?(@.type=='Ready')].status" | grep "False" &> /dev/null; then
        return 1
    else
        return 0
    fi
}



POD_EXISTS=$(kubectl get pod -n $NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})

if [ -z "$POD_EXISTS" ]; then
    kubectl create deployment client-test -n $NAMESPACE --image=python:3.8.13 -- sleep infinity
fi


TIMEOUT=300
END_TIME=$(( $(date +%s) + TIMEOUT ))

printf "Waiting for all pods to be running and ready..."
while true; do
    CURRENT_TIME=$(date +%s)
    if [[ $CURRENT_TIME -ge $END_TIME ]]; then
        echo "Timeout reached: Not all pods are ready after 5 minutes."
        exit 1
    fi

    if check_pods; then
        echo "All pods in the $NAMESPACE namespace are running and ready."
        break
    else
        printf '.'
        sleep 2
    fi
done


export CLIENT_POD=$(kubectl get pod -n $NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
export accessUrl=$(kubectl get gmc -n $NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='$NAMESPACE')].status.accessUrl}")

echo "Connecting to the server through the pod $CLIENT_POD using URL $accessUrl..."

# encode content into base64 - -w option is required to avoid new line characters
content=$(echo -n "AVX-512 are 512-bit extensions to the 256-bit Advanced Vector Extensions SIMD instructions for x86 instruction set architecture" | base64 -w 0)

# run query with encoded content
kubectl exec "$CLIENT_POD" -n $NAMESPACE -- \
    curl --no-buffer -s $accessUrl -X POST -d "{ \"files\": [{\"filename\": \"file.txt\", \"data64\": \"${content}\"}], \"links\": [] }" -H 'Content-Type: application/json'

echo ""
