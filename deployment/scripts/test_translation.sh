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

NAMESPACE=${1:-translation}
NAMESPACE=${1:-chatqa}
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

target_languages=("Chinese" "English" "Russian")

for lang in "${target_languages[@]}"; do
    echo "Processing language: $lang"
    JSON_PAYLOAD='{"text":"Los elefantes pueden ser los animales terrestres más grandes. Se pueden encontrar en India y África.","target_language":"'
    JSON_PAYLOAD=$JSON_PAYLOAD$lang
    JSON_END='"}'
    JSON_PAYLOAD=$JSON_PAYLOAD$JSON_END
    echo kubectl exec "$CLIENT_POD" -n $NAMESPACE -- \
        curl --no-buffer -s $accessUrl -X POST -d "$JSON_PAYLOAD" -H 'Content-Type: application/json' | awk '{ gsub(/^data: /, ""); gsub(/'\''/, ""); printf     "%s", $0 }'

    kubectl exec "$CLIENT_POD" -n $NAMESPACE -- \
        curl --no-buffer -s $accessUrl -X POST -d "$JSON_PAYLOAD" -H 'Content-Type: application/json' | awk '{ gsub(/^data: /, ""); gsub(/'\''/, ""); printf     "%s", $0 }'
    echo ""
    test_return_code=$?

    if [ $test_return_code -eq 0 ]; then
        echo "Test finished successfully"
    else
        echo "Test failed with return code:$test_return_code"
    fi
done
exit
