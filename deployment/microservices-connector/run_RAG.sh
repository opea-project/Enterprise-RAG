#! /bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

repo_path=$(realpath "$(pwd)/../../")
available_pipelines=$(ls config/samples/chatQnA_*.yaml | sed 's|config/samples/chatQnA_|\t\t|; s|.yaml||')


function help() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "\t--deploy <PIPELINE_NAME>: Start the deployment process (default)."
    echo -e "\tPipelines available:\n$available_pipelines"
    echo -e "\t--test: Run connection test."
    echo -e "\t--telemetry: Start telemetry services."
    echo -e "\t--clear: Clear the cluster and stop telemetry services."
    echo -e "\t--help: Display this help message."
    echo -e "Example: $0 --deploy dataprep_gaudi"
    echo -e "Example: $0 --deploy dataprep_gaudi_torch --telemetry"
    echo -e "Example: $0 dataprep_gaudi"
}


function start_deployment() {
    cd "${repo_path}/deployment/microservices-connector"

    # just logging into aws
    ./update_images.sh --registry aws --no-build --no-push

    helm install -n system --create-namespace gmc helm
    namespace=chatqa
    kubectl get namespace $namespace || kubectl create namespace $namespace
    kubectl apply -f $(pwd)/config/samples/chatQnA_$1.yaml
    kubectl create deployment client-test -n $namespace --image=python:3.8.13 -- sleep infinity
}


function start_telemetry() {
    cd "${repo_path}/telemetry/helm"

    if ! helm repo list | grep -q 'prometheus-community'; then
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    fi

    helm repo update
    helm dependency build
    helm install -n monitoring --create-namespace rag-telemetry .

    nohup kubectl --namespace monitoring port-forward svc/rag-telemetry-grafana 3000:80 > port_3000.out 2>&1 &
    nohup kubectl proxy > kubectl_proxy.out 2>&1 &
}


kill_process() {
    local pattern=$1
    local PID=$(pgrep -f "$pattern")
    local full_command=$(ps -p $PID -o cmd)

    if [ ! -z "$PID" ]; then
        echo "Killing $full_command with PID $PID"
        kill -2 $PID
    fi
}

function stop_telemetry() {
    cd "${repo_path}/telemetry/helm"

    helm uninstall -n monitoring rag-telemetry

    kill_process "kubectl --namespace monitoring port-forward"
    kill_process "kubectl proxy"
}



if [ $# -eq 0 ]; then
    echo "Error: No parameter provided for deployment."
    help
    exit 1
fi


if [ $# -eq 1 ] && [[ ! "$1" == --* ]]; then
    echo start_deployment "$1"
    exit 0
fi


while [ $# -gt 0 ]; do
    case "$1" in
        --deploy)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                echo "Error: Invalid or no parameter provided for --deploy. Please provide a valid pipeline name."
                help
                exit 1
            fi
            echo start_deployment "$1"
            ;;
        --test)
            echo bash ./test_connection.sh
            ;;
        --telemetry)
            echo start_telemetry
            ;;
        --clear)
            echo bash ./clear_cluster.sh
            echo stop_telemetry
            ;;
        --help)
            help
            exit 0
            ;;
        *)
            echo "Error: unknown action $1"
            help
            exit 1
            ;;
    esac
    shift
done
