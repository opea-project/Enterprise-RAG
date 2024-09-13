#! /bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

repo_path=$(realpath "$(pwd)/../../")
available_pipelines=$(ls config/samples/chatQnA_*.yaml | sed 's|config/samples/chatQnA_|\t\t|; s|.yaml||')


KEYCLOAK_FPORT=1234
GRAFANA_FPORT=3000
CHAT_ROUTER_PORT=4444
UI_PORT=4173
DEPLOYMENT_NS=chatqa
DATAPREP_NS=dataprep
UI_NS=rag-ui


function help() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "\t--deploy <PIPELINE_NAME>: Start the deployment process (default)."
    echo -e "\tPipelines available:\n$available_pipelines"
    echo -e "\t--test: Run a connection test."
    echo -e "\t--auth: Start authentication service with Keycloak."
    echo -e "\t--ui: Startui service (requires Keycloak and deployment services)."
    # echo -e "\t--auth: Start authentication and authorization services with APISIX and an OIDC-based identity provider (Keycloak). (requires deployment to work)"
    echo -e "\t--telemetry: Start telemetry services."
    echo -e "\t--clear: Clear the cluster and stop auth and telemetry services."
    echo -e "\t--help: Display this help message."
    echo -e "Example: $0 --deploy gaudi"
    echo -e "Example: $0 --deploy gaudi_torch --telemetry --auth --ui"
}


function start_deployment() {
    MODELS_VOLUME=/mnt/opea-models
    if [[ ! -e $MODELS_VOLUME ]]; then
        sudo mkdir -p $MODELS_VOLUME
        sudo chmod 755 $MODELS_VOLUME
    fi

    cd "${repo_path}/deployment/microservices-connector"

    # just logging into aws
    ./update_images.sh --registry aws --no-build --no-push

    local use_proxy=""
    [ -n "$https_proxy" ] && use_proxy+="--set proxy.httpProxy=$https_proxy "
    [ -n "$http_proxy" ] && use_proxy+="--set proxy.httpsProxy=$http_proxy "
    [ -n "$no_proxy" ] && no_proxy_k8s=$(echo "$no_proxy,.svc,.svc.cluster.local,.pod.cluster.local" | sed 's/,/\\,/g') && \
        use_proxy+="--set proxy.noProxy=$no_proxy_k8s "

    helm install -n system $use_proxy --create-namespace gmc helm || exit 1

    printf "waiting for gmc to start working"
    wait_for_condition check_pods "system"

    kubectl get namespace $DEPLOYMENT_NS || kubectl create namespace $DEPLOYMENT_NS
    kubectl get namespace $DATAPREP_NS || kubectl create namespace $DATAPREP_NS

    kubectl apply -f $(pwd)/config/samples/dataprep_xeon.yaml
    kubectl apply -f $(pwd)/config/samples/chatQnA_$1.yaml

    printf "waiting for chatqa pods to start working"
    wait_for_condition check_pods "$DEPLOYMENT_NS"
    wait_for_condition check_pods "$DATAPREP_NS"
}


function start_telemetry() {
    cd "${repo_path}/telemetry/helm"

    if ! helm repo list | grep -q 'prometheus-community'; then
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    fi

    helm repo update
    helm dependency build
    # telemetry/base (metrics)
    helm install -n monitoring --create-namespace telemetry .
    # telemetry/logs

    # Please remember prerequesites from telemetry/helm/charts/logs/README.md must be met (volumes/image)
    # helm install -n monitoring telemetry-logs charts/logs                                          # simple version without journald/unit logs
    # Set own image with --set otelcol-logs.image.repository="$REGISTRY/otelcol-contrib-journalctl"
    helm install -n monitoring telemetry-logs -f charts/logs/values-journalctl.yaml charts/logs     # custom image version with journald/unit logs

    # wait for telemetry pods to be ready
    printf "waiting until telemetry is ready. "
    wait_for_condition check_pods "monitoring"
    # Please remember prerequesites from telemetry/helm/charts/logs/README.md must be met (volumes/image)
    # helm install -n monitoring telemetry-logs charts/logs                                          # simple version without journald/unit logs
    # Set own image with --set otelcol-logs.image.repository="$REGISTRY/otelcol-contrib-journalctl"
    helm install -n monitoring telemetry-logs -f charts/logs/values-journalctl.yaml charts/logs     # custom image version with journald/unit logs
    
    nohup kubectl --namespace monitoring port-forward svc/telemetry-grafana $GRAFANA_FPORT:80 >> nohup_grafana.out 2>&1 &
    nohup kubectl proxy >> nohup_kubectl_proxy.out 2>&1 &
}

kill_process() {
    local pattern=$1
    local PID=$(pgrep -f "$pattern")

    if [ -n "$PID" ]; then
        local full_command=$(ps -p $PID -o cmd= | tail -n1)

        if [ ! -z "$PID" ]; then
            echo "Killing '$full_command' with PID $PID"
            kill -2 $PID
        fi
    fi
}

function stop_telemetry() {
    cd "${repo_path}/telemetry/helm"

    helm uninstall -n monitoring telemetry-logs
    helm uninstall -n monitoring telemetry

    kill_process "kubectl --namespace monitoring port-forward"
    kill_process "kubectl proxy"
}


# check if all pods in a namespece or specific pod by name are ready
check_pods() {
    local namespace="$1"
    local deployment_name="$2"

    if [ -z "$deployment_name" ]; then
        # Check all pods in the namespace
        if kubectl get pods -n "$namespace" --no-headers -o custom-columns="NAME:.metadata.name,READY:.status.conditions[?(@.type=='Ready')].status" | grep "False" &> /dev/null; then
            return 1
        else
            return 0
        fi
    else
        # Check specific pod by deployment name
        if kubectl get pods -n "$namespace" -l app="$deployment_name" --no-headers -o custom-columns="NAME:.metadata.name,READY:.status.conditions[?(@.type=='Ready')].status" | grep "False" &> /dev/null; then
            return 1
        else
            return 0
        fi
    fi
}


# waits until all pods in a namespece or specific pod by name are ready
wait_for_pods() {
    local namespace="$1"
    local deployment_name="$2"
    # warmup of LLM model might take a long time in case of using big model
    TIMEOUT=1000
    END_TIME=$(( $(date +%s) + TIMEOUT ))

    echo "Waiting for pods to be ready in namespace '$namespace'..."

    while true; do
        CURRENT_TIME=$(date +%s)
        if [[ $CURRENT_TIME -ge $END_TIME ]]; then
            echo "Timeout reached: Not all pods are ready after $((timeout / 60)) minutes."
            return 1
        fi

        if check_pods "$namespace" "$deployment_name"; then
            return 0
        else
            printf '.'
            sleep 2
        fi
    done
}


# waits until a provided condition function returns true
wait_for_condition() {
    sleep 30 # safety measures for k8s objects to be created
    local TIMEOUT=1800
    local END_TIME=$(( $(date +%s) + TIMEOUT ))
    while true; do
        local CURRENT_TIME=$(date +%s)
        if [[ "$CURRENT_TIME" -ge "$END_TIME" ]]; then
            echo "Timeout reached: Condition $* not met after $((TIMEOUT / 60)) minutes."
            return 1
        fi

        if "$@"; then
            echo
            return 0
        else
            printf '.'
            sleep 2
        fi
    done
}

function start_authentication() {
    # TODO: looks like this PV needs to be fixed
    KEYCLOAK_VOLUME=/mnt/keycloak-vol
    # clean up data on host prior deploy postgress database
    sudo rm -rf $KEYCLOAK_VOLUME
   
    if [[ ! -e $KEYCLOAK_VOLUME ]]; then
        sudo mkdir -p $KEYCLOAK_VOLUME
        sudo chmod a+rwx $KEYCLOAK_VOLUME
    fi

    kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: data-keycloak-postgresql-0
spec:
  capacity:
    storage: 9Gi
  hostPath:
    path: "$KEYCLOAK_VOLUME"
  accessModes:
    - ReadWriteOnce
EOF


    # NOTE: these values are for test deployment only
    # in real developementб it's not recommended to use admin/admin
    # it's also necessary to create a separate realm and user for setting up apisix
    KEYCLOAK_USER=admin
    KEYCLOAK_PASS=admin

    # Running the server in development mode. DO NOT use this configuration in production.
    helm install keycloak oci://registry-1.docker.io/bitnamicharts/keycloak \
        --version 22.1.0 \
	    --set volumePermissions.enabled=true \
        --set auth.adminUser=$KEYCLOAK_USER \
        --set auth.adminPassword=$KEYCLOAK_PASS

    # Additional sleep as helm command does not wait for deploying PODs 
    # without sleep "wait_for_condition" function might pass as it might start when 
    # there no pods created in default namespace
    printf "waiting until keycloak in default namespace is UP"
    wait_for_condition check_pods "default"
    DEFAULT_REALM=master
    nohup kubectl port-forward --namespace default svc/keycloak $KEYCLOAK_FPORT:80 >> nohup_keycloak.out 2>&1 & 

    KEYCLOAK_URL=http://localhost:$KEYCLOAK_FPORT
    printf "forwarding port to $KEYCLOAK_URL"
    CONFIGURE_URL=$KEYCLOAK_URL/realms/$DEFAULT_REALM/.well-known/openid-configuration
    wait_for_condition curl --output /dev/null --silent --head --fail "$CONFIGURE_URL"

    INTROSPECTION_URL=$(curl -s $CONFIGURE_URL | grep -oP '"introspection_endpoint"\s*:\s*"\K[^"]+' | head -n1)

    if [[ ! "$INTROSPECTION_URL" =~ ^https?:// ]]; then
        echo "Error: Introspection URL '$INTROSPECTION_URL' is not valid."
        exit 1
    fi

    echo $CONFIGURE_URL
    echo $INTROSPECTION_URL

    bash ${repo_path}/auth/keycloak_realm_creator.sh

}

function stop_authentication() {

    kill_process "kubectl port-forward --namespace default svc/keycloak"
    helm uninstall keycloak

    kubectl patch pvс data-keycloak-postgresql-0 -p '{"metadata":{"finalizers":null}}'
    kubectl patch pv data-keycloak-postgresql-0 -p '{"metadata":{"finalizers":null}}'

    # volume can be removed only when it's released
    printf "waiting until keycloak pods are terminated."
    wait_for_condition check_pods "default"

    kubectl delete pvc data-keycloak-postgresql-0
    kubectl delete pv data-keycloak-postgresql-0
}


function start_ui() {
    cd "${repo_path}/app/chat-qna"

    helm install chatqa-app helm-ui --create-namespace -n $UI_NS
    wait_for_condition check_pods "$UI_NS"
    nohup kubectl port-forward --namespace $UI_NS svc/ui-chart $UI_PORT:$UI_PORT >> nohup_ui.out 2>&1 & 
}


function stop_ui() {
    cd "${repo_path}/app/chat-qna"

    helm status -n $UI_NS chatqa-app > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        helm uninstall chatqa-app  -n $UI_NS
    fi
    kill_process "kubectl port-forward --namespace $UI_NS svc/ui-chart"
}


if [ $# -eq 0 ]; then
    echo "Error: No parameter provided for deployment."
    help
    exit 1
fi


if [ $# -eq 1 ] && [[ ! "$1" == --* ]]; then
    echo "---> Start deployment"
    start_deployment "$1"
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
            echo "---> Start deployment"
            start_deployment "$1"
            ;;
        --test)
            echo "---> Test connection"
            bash ./test_connectin.sh
            ;;
        --telemetry)
            echo "---> Start telemetry"
            start_telemetry
            ;;
        --auth)
            echo "---> Start authentication"
            start_authentication
            ;;
        --ui)
            echo "---> Start ui"
            start_ui
            ;;
        --clear)
            echo "---> Clear cluster"
            bash ./clear_cluster.sh
            stop_authentication
            stop_ui
            stop_telemetry
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
