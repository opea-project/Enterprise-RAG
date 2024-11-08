#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# paths
repo_path=$(realpath "$(pwd)/../")
manifests_path="$repo_path/deployment/microservices-connector/config/samples"
gmc_path="$repo_path/deployment/microservices-connector/helm"
telemetry_path="$repo_path/deployment/telemetry/helm"
telemetry_logs_path="$repo_path/deployment/telemetry/helm/charts/logs"
telemetry_traces_path="$repo_path/deployment/telemetry/helm/charts/traces"
telemetry_traces_instr_path="$repo_path/deployment/telemetry/helm/charts/traces-instr"
ui_path="$repo_path/deployment/ui/chat-qna/helm-ui"
auth_path="$repo_path/deployment/auth/"
api_gateway_path="$repo_path/deployment/auth/apisix-helm"
api_gateway_crd_path="$repo_path/deployment/auth/apis-crd-helm"
configs_path="$repo_path/deployment/configs"

# ports
KEYCLOAK_FPORT=1234

# namespaces
DEPLOYMENT_NS=chatqa
GATEWAY_NS=auth-apisix
DATAPREP_NS=dataprep
TELEMETRY_NS=monitoring
TELEMETRY_TRACES_NS=monitoring-traces
UI_NS=rag-ui
AUTH_NS=auth
INGRESS_NS=ingress-nginx
GMC_NS=system

AUTH_HELM="oci://registry-1.docker.io/bitnamicharts/keycloak"
INGRESS_HELM="ingress-nginx/ingress-nginx"

# keycloak specific vars
keycloak_user=admin
keycloak_pass=admin
client_secret=""
KEYCLOAK_URL=http://localhost:$KEYCLOAK_FPORT
DEFAULT_REALM=master
CONFIGURE_URL=$KEYCLOAK_URL/realms/$DEFAULT_REALM/.well-known/openid-configuration

GRAFANA_PASSWORD=""

# others
PIPELINE=""
REGISTRY="localhost:5000"
TAG="latest"

available_pipelines=$(cd "$manifests_path" && find chatQnA_*.yaml | sed 's|chatQnA_||g; s|.yaml||g' | paste -sd ',')

function usage() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "\t--grafana_password (REQUIRED with --telemetry): Initial password for grafana."
    echo -e "\t--auth: Start auth services."
    echo -e "\t--kind: Changes dns value for telemetry(kind is kube-dns based)."
    echo -e "\t--deploy <PIPELINE_NAME>: Start the deployment process."
    echo -e "\tPipelines available: $available_pipelines"
    echo -e "\t--tag <TAG>: Use specific tag for deployment."
    echo -e "\t--test: Run a connection test."
    echo -e "\t--telemetry: Start telemetry services."
    echo -e "\t--registry <REGISTRY>: Use specific registry for deployment."
    echo -e "\t--ui: Start ui services (requires deployment & auth)."
    echo -e "\t--ip: external IP adress to be exposed via ingress"
    echo -e "\t--upgrade: Helm will install or upgrade charts."
    echo -e "\t-cd|--clear-deployment: Clear deployment services."
    echo -e "\t-ch|--clear-auth: Clear auth services."
    echo -e "\t-ct|--clear-telemetry: Clear telemetry services."
    echo -e "\t-cu|--clear-ui: Clear auth and ui services."
    echo -e "\t-ca|--clear-all: Clear the all services."
    echo -e "\t-h|--help: Display this help message."
    echo -e "Example: $0 --deploy gaudi_torch --telemetry --ui --grafana_password=changeitplease"
}

print_header() {
    echo "$1"
    echo "-----------------------"
}

print_log() {
    echo "-->$1"
}

helm_install() {
    local path namespace name args

    namespace=$1
    name=$2
    path=$3
    args=$4

    msg="installation"
    helm_cmd="install"
    if [[ "$helm_upgrade" ]]; then
      helm_cmd="upgrade --install"
      msg="upgrade or installation"
    fi

    if helm $helm_cmd -n "$namespace" --create-namespace "$name" "$path" $args 2> >(grep -v 'found symbolic link' >&2) > /dev/null; then
        print_log "helm $msg in $namespace of $name finished succesfully"
    else
        print_log "helm $msg in $namespace of $name failed. Exiting"
        exit 1
    fi
}

# check if all pods in a namespace or specific pod by name are ready
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

# waits until a provided condition function returns true
wait_for_condition() {
    sleep 5 # safety measures for helm to initialize pod deployments
    local current_time
    local timeout=1800
    local end_time=$(( $(date +%s) + timeout ))
    while true; do
        current_time=$(date +%s)
        if [[ "$current_time" -ge "$end_time" ]]; then
            print_log "Timeout reached: Condition $* not met after $((timeout / 60)) minutes."
            print_log "Exiting" ; exit 1
        fi

        if "$@"; then
            printf ""
            return 0
        else
            printf '.'
            sleep 2
        fi
    done
    print_log "Exiting" ; exit 1
}

function start_and_keep_port_forwarding() {
    local SVC_NAME=$1
    local NAMESPACE=$2
    local HOST_PORT=$3
    local REMOTE_PORT=$4

    local PID=""

    print_log "Starting and monitoring port-forwarding for $SVC_NAME in namespace $NAMESPACE"

    while true
    do
        nohup kubectl port-forward --namespace "$NAMESPACE" svc/"$SVC_NAME" "$HOST_PORT":"$REMOTE_PORT" >> nohup_"$SVC_NAME".out 2>&1 &
        PID=$!
        wait $PID
    done
}

kill_process() {
    local pattern pid full_command
    pattern=$1
    pid=$(pgrep -f "$pattern")

    if [ -n "$pid" ]; then
        full_command=$(ps -p "$pid" -o cmd= | tail -n1)

        if [ -n "$pid" ]; then
            print_log "Killing '$full_command' with PID $pid"
            kill -2 "$pid"
        fi
    fi
}

function create_certs() {
    print_header "Generate self-signed certificates"

    if [[ ! -e tls.key || ! -e tls.crt ]]; then
        openssl req -x509 -new -nodes -days 365 -keyout tls.key -out tls.crt -config "$configs_path"/openssl.cnf > /dev/null 2>&1
        print_log "Generated certificates"
    else
        print_log "Proceeding with existing certificates"
    fi

    # flags initialized before while loop
    if $ui_flag; then
        kubectl get namespace $UI_NS > /dev/null 2>&1 || kubectl create namespace $UI_NS
        kubectl get secret tls-secret -n $UI_NS > /dev/null 2>&1|| kubectl create secret tls tls-secret --key tls.key --cert tls.crt -n $UI_NS
    fi

    if $telemetry_flag; then
        kubectl get namespace $TELEMETRY_NS > /dev/null 2>&1 || kubectl create namespace $TELEMETRY_NS
        kubectl get secret tls-secret -n $TELEMETRY_NS > /dev/null 2>&1 || kubectl create secret tls tls-secret --key tls.key --cert tls.crt -n $TELEMETRY_NS
    fi

    if $auth_flag; then
        kubectl get namespace $AUTH_NS > /dev/null 2>&1 || kubectl create namespace $AUTH_NS
        kubectl get secret tls-secret -n $AUTH_NS > /dev/null 2>&1 || kubectl create secret tls tls-secret --key tls.key --cert tls.crt -n $AUTH_NS
    fi
}

# deploys GMConnector, chatqna pipeline and dataprep pipeline
function start_deployment() {
    local pipeline=$1

    print_header "Start deployment"

    # set values for helm charts
    bash set_values.sh -r "$REGISTRY" -t "$TAG"

    # create namespaces
    kubectl get namespace $GMC_NS > /dev/null 2>&1 || kubectl create namespace $GMC_NS
    kubectl get namespace $DEPLOYMENT_NS > /dev/null 2>&1 || kubectl create namespace $DEPLOYMENT_NS
    kubectl get namespace $DATAPREP_NS > /dev/null 2>&1 || kubectl create namespace $DATAPREP_NS

    helm_install $GMC_NS gmc "$gmc_path "

    print_log "waiting for pods in $GMC_NS are ready"
    wait_for_condition check_pods "$GMC_NS"

    kubectl apply -f "$manifests_path/chatQnA_$pipeline".yaml
    kubectl apply -f "$manifests_path/dataprep_xeon.yaml"

    print_log "waiting until pods in $DEPLOYMENT_NS and $DATAPREP_NS are ready"

    wait_for_condition check_pods "$DEPLOYMENT_NS"
    wait_for_condition check_pods "$DATAPREP_NS"
}

function clear_deployment() {
    print_header "Clear deployment"

    kubectl get ns $DEPLOYMENT_NS > /dev/null 2>&1 && kubectl delete ns $DEPLOYMENT_NS
    kubectl get ns $DATAPREP_NS > /dev/null 2>&1 && kubectl delete ns $DATAPREP_NS

    kubectl get crd gmconnectors.gmc.opea.io > /dev/null 2>&1 && kubectl delete crd gmconnectors.gmc.opea.io

    helm status -n $GMC_NS gmc > /dev/null 2>&1 && helm delete -n $GMC_NS gmc
    kubectl get ns $GMC_NS > /dev/null 2>&1 && kubectl delete ns $GMC_NS
}

function start_telemetry() {
    print_header "Start telemetry"

    kubectl get namespace $TELEMETRY_NS > /dev/null 2>&1 || kubectl create namespace $TELEMETRY_NS
    kubectl get namespace $TELEMETRY_TRACES_NS > /dev/null 2>&1 || kubectl create namespace $TELEMETRY_TRACES_NS

    # add repo if needed
    if ! helm repo list | grep -q 'prometheus-community' ; then helm repo add prometheus-community https://prometheus-community.github.io/helm-charts ; fi # for prometheus/k8s/prometheus operator
    if ! helm repo list | grep -q 'grafana' ; then helm repo add grafana https://grafana.github.io/helm-charts ; fi # for grafana/loki/tempo
    if ! helm repo list | grep -q 'opensearch' ; then helm repo add opensearch https://opensearch-project.github.io/helm-charts/ ; fi # opensearch
    if ! helm repo list | grep -q 'open-telemetry' ; then helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts ; fi # opentelemetry collector/opentelemetry operator

    # traces (optional dependecies)
    if ! helm repo list | grep -q 'jaegertracing' ; then helm repo add jaegertracing  https://jaegertracing.github.io/helm-charts; fi # for jaeger

    # other metrics-server/pcm...
    if ! helm repo list | grep -q 'metrics-server' ; then helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ ; fi

    helm repo update  > /dev/null

    # I) telemetry/base (metrics)
    helm dependency build "$telemetry_path" > /dev/null
    helm_install $TELEMETRY_NS telemetry "$telemetry_path" "$HELM_INSTALL_TELEMETRY_DEFAULT_ARGS $HELM_INSTALL_TELEMETRY_EXTRA_ARGS"

    # II) telemetry/logs
    helm dependency build "$telemetry_logs_path"  > /dev/null
    helm_install "$TELEMETRY_NS" telemetry-logs "$telemetry_logs_path" "$HELM_INSTALL_TELEMETRY_LOGS_DEFAULT_ARGS $HELM_INSTALL_TELEMETRY_LOGS_EXTRA_ARGS"

    # WAIT I/II) wait for telemetry + telemetry logs pods to be ready
    print_log "waiting until pods in $TELEMETRY_NS are ready"
    wait_for_condition check_pods "$TELEMETRY_NS"

    # III) telemetry/traces
    helm dependency build "$telemetry_traces_path"  > /dev/null
    # IIIa) 'Traces' (backends) installation: because of dependency between opentelemetry-operator CRDs and CR create when otelcol-traces are enabled and webhook installation race condition.
    helm_install "$TELEMETRY_TRACES_NS" telemetry-traces "$telemetry_traces_path" "$HELM_INSTALL_TELEMETRY_TRACES_DEFAULT_ARGS $HELM_INSTALL_TELEMETRY_TRACES_EXTRA_ARGS"
    # IIIa) Check telemetry/traces
    print_log "waiting until pods in $TELEMETRY_TRACES_NS are ready"
    wait_for_condition check_pods "$TELEMETRY_TRACES_NS"

    # IIIb) 'Traces-instr' deploy OpenTelemetry collector and instrumenation for ChatQnA (requires chatqa namespace)
    kubectl get namespace $DEPLOYMENT_NS > /dev/null 2>&1 || kubectl create namespace $DEPLOYMENT_NS
    kubectl get namespace $DATAPREP_NS > /dev/null 2>&1 || kubectl create namespace $DATAPREP_NS
    helm_install "$TELEMETRY_TRACES_NS" telemetry-traces-instr "$telemetry_traces_instr_path" "--set instrumentation.namespaces={$DEPLOYMENT_NS,$DATAPREP_NS}"
    # IIIb) telemetry/traces-instr check
    print_log "waiting until pods in $TELEMETRY_TRACES_NS are ready"
    wait_for_condition check_pods "$TELEMETRY_TRACES_NS"

}

function clear_telemetry() {
    print_header "Clear telemetry"

    kubectl get secret tls-secret -n $TELEMETRY_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $TELEMETRY_NS

    # remove CR manually to allow (helm uninstall doesn't remove it!)
    kubectl get otelcols/otelcol-traces -n "$TELEMETRY_TRACES_NS" > /dev/null 2>&1 && kubectl delete otelcols/otelcol-traces -n "$TELEMETRY_TRACES_NS"
    helm status -n "$TELEMETRY_TRACES_NS" telemetry-traces-instr > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_TRACES_NS" telemetry-traces-instr
    helm status -n "$TELEMETRY_TRACES_NS" telemetry-traces > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_TRACES_NS" telemetry-traces
    helm status -n "$TELEMETRY_NS" telemetry-logs > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_NS" telemetry-logs
    helm status -n "$TELEMETRY_NS" telemetry > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_NS" telemetry

    kubectl get ns $TELEMETRY_TRACES_NS > /dev/null 2>&1 && kubectl delete ns $TELEMETRY_TRACES_NS
    kubectl get ns $TELEMETRY_NS > /dev/null 2>&1 && kubectl delete ns $TELEMETRY_NS
}

function start_authentication() {
    local introspection_url

    print_log "Start authentication"

    helm_install $AUTH_NS keycloak "$AUTH_HELM" "$HELM_INSTALL_AUTH_DEFAULT_ARGS $HELM_INSTALL_AUTH_EXTRA_ARGS"

    print_log "waiting until pods in $AUTH_NS are ready"
    wait_for_condition check_pods "$AUTH_NS"

    start_and_keep_port_forwarding "keycloak" "$AUTH_NS" "$KEYCLOAK_FPORT" 80 &
    PID=$!

    print_log "verify if $CONFIGURE_URL works"
    wait_for_condition curl --output /dev/null --silent --head --fail "$CONFIGURE_URL"

    introspection_url=$(curl -s $CONFIGURE_URL | grep -oP '"introspection_endpoint"\s*:\s*"\K[^"]+' | head -n1)

    if [[ ! "$introspection_url" =~ ^https?:// ]]; then
        print_log "Error: Introspection URL '$introspection_url' is not valid."
        exit 1
    fi

    bash "$auth_path"/keycloak_realm_creator.sh $AUTH_NS

    kill -2 $PID
    kill_process "kubectl port-forward --namespace $AUTH_NS svc/keycloak"
}

function clear_authentication() {
    print_header "Clear authentication"

    kubectl get secret tls-secret -n $AUTH_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $AUTH_NS

    helm status -n "$AUTH_NS" keycloak > /dev/null 2>&1 && helm -n "$AUTH_NS" uninstall keycloak

    # if pvc exists add finalizers & remove it
    if kubectl get pvc -n "$AUTH_NS" data-keycloak-postgresql-0 > /dev/null 2>&1; then
        kubectl patch pvc -n "$AUTH_NS" data-keycloak-postgresql-0 -p '{"metadata":{"finalizers":null}}'

        print_log "waiting until keycloak pods are terminated."
        wait_for_condition check_pods "$AUTH_NS"

        kubectl get pvc -n "$AUTH_NS" data-keycloak-postgresql-0 > /dev/null 2>&1 && kubectl delete pvc -n "$AUTH_NS" data-keycloak-postgresql-0
    fi
}

function start_ingress() {
    print_header "Start ingress"

    # Install ingress
    if ! helm repo list | grep -q 'ingress-nginx' ; then helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx ; fi
    helm repo update > /dev/null
    helm_install "$INGRESS_NS" ingress-nginx "$INGRESS_HELM" "$HELM_INSTALL_INGRESS_DEFAULT_ARGS"

    print_log "waiting until pods in $INGRESS_NS are ready"
    wait_for_condition check_pods "$INGRESS_NS"
}

function clear_ingress() {
    print_header "Clear ingress"

    rm -f tls.crt tls.key
    helm status -n "$INGRESS_NS" ingress-nginx > /dev/null 2>&1 && helm delete -n "$INGRESS_NS" ingress-nginx
}

function start_gateway() {
    print_header "Start gateway"

    start_and_keep_port_forwarding "keycloak" "$AUTH_NS" "$KEYCLOAK_FPORT" 80 &
    PID=$!

    sleep 2 # needs a while to work fine
    client_secret=$(bash "$auth_path"/get_secret.sh)

    kill -2 $PID
    kill_process "kubectl port-forward --namespace $AUTH_NS svc/keycloak"

    sed -i -E "s#(.*client_secret:) \"(.*)\"#\1 \"$client_secret\"#g" $api_gateway_crd_path/values.yaml

    kubectl get ns $DATAPREP_NS > /dev/null 2>&1 || kubectl create ns $DATAPREP_NS
    kubectl get ns $DEPLOYMENT_NS > /dev/null 2>&1 || kubectl create ns $DEPLOYMENT_NS
    kubectl get ns $UI_NS > /dev/null 2>&1 || kubectl create ns $UI_NS

    helm dependency update "$api_gateway_path" > /dev/null
    helm_install "$GATEWAY_NS" auth-apisix "$api_gateway_path" "$HELM_INSTALL_GATEWAY_DEFAULT_ARGS"

    print_log "waiting until pods in $GATEWAY_NS are ready"
    wait_for_condition check_pods "$GATEWAY_NS"

    helm dependency update "$api_gateway_crd_path" > /dev/null
    helm_install "$GATEWAY_NS" auth-apisix-crds "$api_gateway_crd_path" "$HELM_INSTALL_GATEWAY_CRD_DEFAULT_ARGS"

    print_log "waiting until pods in $GATEWAY_NS are ready"
    wait_for_condition check_pods "$GATEWAY_NS"
}


function clear_gateway() {
    print_header "Clear gateway"

    helm status -n "$GATEWAY_NS" auth-apisix-crds > /dev/null 2>&1 &&  helm uninstall auth-apisix-crds -n "$GATEWAY_NS"
    helm status -n "$GATEWAY_NS" auth-apisix > /dev/null 2>&1 &&  helm uninstall auth-apisix -n "$GATEWAY_NS"
}

function start_ui() {
    print_header "Start ui"

    kubectl get namespace $UI_NS > /dev/null 2>&1 || kubectl create namespace $UI_NS

    helm_install "$UI_NS" chatqa-app "$ui_path" "$HELM_INSTALL_UI_DEFAULT_ARGS"

    # !TODO this should be moved to UI helm templates
    kubectl apply -f "$configs_path/ingress-ui.yaml"

    print_log "waiting until pods $UI_NS are ready."
    wait_for_condition check_pods "$UI_NS"
}


function clear_ui() {
    print_header "Clear UI"

    # !TODO mv ingress object UI to helm
    kubectl get ingress.networking.k8s.io -n $UI_NS ui > /dev/null 2>&1 && kubectl delete -f "$configs_path"/ingress-ui.yaml
    kubectl get secret tls-secret -n $UI_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $UI_NS
    helm status -n $UI_NS chatqa-app > /dev/null 2>&1 && helm uninstall -n $UI_NS chatqa-app
}


# Initialize flags
deploy_flag=false
test_flag=false
telemetry_flag=false
ui_flag=false
auth_flag=false
clear_deployment_flag=false
clear_ui_flag=false
clear_telemetry_flag=false
clear_all_flag=false
clear_auth_flag=false


# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --kind)
            LOKI_DNS_FLAG="--set loki.global.dnsService=kube-dns"
            TEMPO_DNS_FLAG="--set tempo.global.dnsService=kube-dns"
            ;;
        -d|--deploy)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --deploy. Please provide a valid pipeline name."
                usage
                exit 1
            fi
            PIPELINE=$1
            deploy_flag=true
            ;;
        --grafana_password)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --grafana_password. Please provide inital password for Grafana."
                usage
                exit 1
            fi
            GRAFANA_PASSWORD=$1
            ;;
        --tag)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --tag. Please provide a valid tag name."
                usage
                exit 1
            fi
            TAG=$1
            ;;
        --test)
            test_flag=true
            ;;
        --telemetry)
            telemetry_flag=true
            ;;
        --registry)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --registry. Please provide a valid registry name."
                usage
                exit 1
            fi
            REGISTRY=$1
            ;;
        --ip)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --ip. Please provide a valid ip."
                usage
                exit 1
            fi
            IP=$1
            ;;
        --ui)
            ui_flag=true
            ;;
        --upgrade)
            helm_upgrade=true
            ;;
        --auth)
            auth_flag=true
            ;;
        -ch|--clear-auth)
            clear_auth_flag=true
            ;;
        -cd|--clear-deployment)
            clear_deployment_flag=true
            ;;
        -cu|--clear-ui)
            clear_ui_flag=true
            ;;
        -ct|--clear-telemetry)
            clear_telemetry_flag=true
            ;;
        -ca|--clear-all)
            clear_all_flag=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown action $1"
            usage
            exit 1
            ;;
    esac
    shift
done


# check required parameters
if [[ "$telemetry_flag" == "true" ]]; then
  if [[ -z "$GRAFANA_PASSWORD" ]]; then
      print_log "Error: Grafana initial password is required for --telemetry!. Please provide inital password for Grafana --grafana_password."
      exit 1
  fi

  # system validation (for journald/ctl systemd OpenTelemetry collector)
  if  [[ $(sysctl -n fs.inotify.max_user_instances) -lt 8000 ]]; then
      print_log "Error: Host OS System is not configured properly. Insufficent inotify.max_user_instances < 8000 (for OpenTelemetry systemd/journald collector). Did you run configure.sh? Or fix it with: sudo sysctl -w fs.inotify.max_user_instances=8192"
      exit 1
  fi
fi

# !TODO this is hacky stuff - especially using env variables @ GRAFANA_PROXY
# shellcheck disable=SC2154
HELM_INSTALL_TELEMETRY_DEFAULT_ARGS="--set kube-prometheus-stack.grafana.env.http_proxy=$http_proxy --set kube-prometheus-stack.grafana.env.https_proxy=$https_proxy --set kube-prometheus-stack.grafana.env.no_proxy=127.0.0.1\,localhost\,monitoring\,monitoring-traces --set kube-prometheus-stack.grafana.adminPassword=$GRAFANA_PASSWORD"
TELEMETRY_LOGS_IMAGE="--set otelcol-logs.image.repository=$REGISTRY/otelcol-contrib-journalctl --set otelcol-logs.image.tag=$TAG"
TELEMETRY_LOGS_JOURNALCTL="-f $telemetry_logs_path/values-journalctl.yaml"
HELM_INSTALL_UI_DEFAULT_ARGS="--set image.ui.repository=$REGISTRY/opea/chatqna-conversation-ui --set image.ui.tag=$TAG --set image.fingerprint.repository=$REGISTRY/system-fingerprint --set image.fingerprint.tag=$TAG --set aliasIP=$IP"

# !TODO needs to be verified if we need values.yaml to be deployed
HELM_INSTALL_INGRESS_DEFAULT_ARGS="--set controller.hostPort.enabled=true --set controller.ingressClass=nginx -f $configs_path/ingress-values.yaml"
HELM_INSTALL_GATEWAY_DEFAULT_ARGS=""
HELM_INSTALL_GATEWAY_CRD_DEFAULT_ARGS=""
# !TODO we need to verify if creating ingress object via keycloak helm charts is needed, since we have additional ingress creating via ingress/configs/
HELM_INSTALL_AUTH_DEFAULT_ARGS="--version 22.1.0 --set volumePermissions.enabled=true --set auth.adminUser=$keycloak_user \
  --set auth.adminPassword=$keycloak_pass -f $auth_path/keycloak-config/keycloak-additional-values.yaml"

HELM_INSTALL_TELEMETRY_LOGS_DEFAULT_ARGS="$TELEMETRY_LOGS_IMAGE  $TELEMETRY_LOGS_JOURNALCTL $LOKI_DNS_FLAG"
HELM_INSTALL_TELEMETRY_TRACES_DEFAULT_ARGS="$TEMPO_DNS_FLAG"
# Please use following for any additional flag (for development only):
#HELM_INSTALL_TELEMETRY_EXTRA_ARGS
#HELM_INSTALL_TELEMETRY_LOGS_EXTRA_ARGS
#HELM_INSTALL_TELEMETRY_TRACES_EXTRA_ARGS

# Execute given arguments
if $auth_flag; then
    create_certs
    start_authentication
    start_gateway
fi

if $deploy_flag; then
    start_deployment "$PIPELINE"
fi

if $telemetry_flag; then
    start_telemetry
fi

if $auth_flag; then
    start_ingress
fi

if $ui_flag; then
    start_ui
fi

if $test_flag; then
    print_header "Test connection"
    bash test_connection.sh
fi

if $clear_auth_flag; then
    clear_ingress
    clear_gateway
    clear_authentication
fi

if $clear_deployment_flag; then
    clear_deployment
fi

if $clear_ui_flag; then
    clear_ui
fi

if $clear_telemetry_flag; then
    clear_telemetry
fi

if $clear_all_flag; then
    clear_deployment
    clear_authentication
    clear_ui
    clear_telemetry
    clear_ingress
    clear_gateway
fi
