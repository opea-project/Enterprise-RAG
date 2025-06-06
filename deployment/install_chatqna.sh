#!/bin/bash
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# paths
repo_path=$(realpath "$(pwd)/../")
manifests_path="$repo_path/deployment/pipelines/chatqa"
gmc_path="$repo_path/deployment/components/gmc/microservices-connector/helm"
fingerprint_path="$repo_path/deployment/components/fingerprint"
telemetry_path="$repo_path/deployment/components/telemetry/helm"
telemetry_logs_path="$repo_path/deployment/components/telemetry/helm/charts/logs"
telemetry_traces_path="$repo_path/deployment/components/telemetry/helm/charts/traces"
telemetry_traces_instr_path="$repo_path/deployment/components/telemetry/helm/charts/traces-instr"
ui_path="$repo_path/deployment/components/ui"
scripts_path="$repo_path/deployment/scripts"
hpa_path="$repo_path/deployment/components/hpa"
keycloak_path="$repo_path/deployment/components/keycloak"
api_gateway_path="$repo_path/deployment/components/apisix"
api_gateway_crd_path="$repo_path/deployment/components/apisix-routes"
ingress_path="$repo_path/deployment/components/ingress"
configs_path="$repo_path/deployment/configs"
edp_path="$repo_path/deployment/components/edp"
istio_path="$repo_path/deployment/components/istio"

# ports
KEYCLOAK_FPORT=1234

# namespaces
DEPLOYMENT_NS=chatqa
FINGERPRINT_NS=fingerprint
GATEWAY_NS=auth-apisix
ENHANCED_DATAPREP_NS=edp
TELEMETRY_NS=monitoring
TELEMETRY_TRACES_NS=monitoring-traces
UI_NS=rag-ui
AUTH_NS=auth
INGRESS_NS=ingress-nginx
GMC_NS=system
ISTIO_NS="istio-system"

AUTH_HELM="oci://registry-1.docker.io/bitnamicharts/keycloak"
HPA_HELM="prometheus-community/prometheus-adapter"
INGRESS_HELM="ingress-nginx/ingress-nginx"

# keycloak specific vars
keycloak_user=admin
client_secret=""
KEYCLOAK_URL=http://localhost:$KEYCLOAK_FPORT
DEFAULT_REALM=master
CONFIGURE_URL=$KEYCLOAK_URL/realms/$DEFAULT_REALM/.well-known/openid-configuration

INGRESS_CHARTS_VERSION=4.12.1
KEYCLOAK_CHARTS_VERSION=24.3.2
K8S_VERSION=v1.29

GRAFANA_PASSWORD=""
KEYCLOAK_PASS=""

# others
PIPELINE=""
REGISTRY="docker.io/opea" # alternatively "localhost:5000/erag" for local registry
TAG="1.2.1"
HELM_TIMEOUT="10m"
ISTIO_VERSION="1.24.1" # ambient is GA but kiali fails to resolve workloads properly (app lables issues?)
FEATURES=""
EDP_DATAPREP_TYPE="normal"

#available_pipelines=$(cd "$manifests_path/examples" && find *.yaml && cd "$manifests_path" && find reference* | paste -sd ',')
available_pipelines=$(cd "$manifests_path/examples" && find *.yaml | sed 's/^/examples\//' && cd "$manifests_path" && find reference* | paste -sd ',')
source $repo_path/deployment/credentials_utils.sh

function usage() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "\t--grafana_password (OPTIONAL,defaults:random or from default_credentials.txt): Initial password for grafana."
    echo -e "\t--keycloak_admin_password (OPTIONAL,default:random or from default_credentials.txt): Initial password for keycloak admin."
    echo -e "\t--auth: Start auth services."
    echo -e "\t--mesh: Deploy service mesh installation for enhanced (default: true during pipeline deployment)"
    echo -e "\t--no-mesh: Don't deploy service mesh, not event during pipeline installation"
    echo -e "\t--kind: Changes dns value for telemetry(kind is kube-dns based)."
    echo -e "\t--deploy <PIPELINE_NAME>: Start the deployment process."
    echo -e "\tPipelines available: $available_pipelines"
    echo -e "\t--tag <TAG>: Use specific tag for deployment."
    echo -e "\t--use-alternate-tagging: Use repo:component_tag tagging format instead of the default (repo/component:tag)."
    echo -e "\t--test: Run a connection test."
    echo -e "\t--telemetry: Start telemetry services."
    echo -e "\t--hpa: enables horizontal pod autoscaler for the services"
    echo -e "\t--registry <REGISTRY>: Use specific registry for deployment."
    echo -e "\t--ui: Start ui services (requires deployment & auth)."
    echo -e "\t--no-edp: Skip creation of Enhanced Dataprep Pipeline."
    echo -e "\t--dpguard: Create Dataprep Guardrail."
    echo -e "\t--semantic-chunking: Enable Semantic Chunking."
    echo -e "\t--edp-dataprep-type: Choose type of dataprep: normal or hierarchical. (default normal)"
    echo -e "\t-ep|--enforce-pss: Enforce strict pod security policies."
    echo -e "\t--upgrade: Helm will install or upgrade charts."
    echo -e "\t--timeout <TIMEOUT>: Set timeout for helm commands. (default 5m)"
    echo -e "\t--features <FEATURES>: Comma-separated list of features to enable. Available features: tdx (experimental)"
    echo -e "\t-cd|--clear-deployment: Clear deployment services."
    echo -e "\t-ch|--clear-auth: Clear auth services."
    echo -e "\t-cm|--clear-mesh: Clear mesh deployment."
    echo -e "\t-ct|--clear-telemetry: Clear telemetry services."
    echo -e "\t-cu|--clear-ui: Clear auth and ui services."
    echo -e "\t-ca|--clear-all: Clear the all services."
    echo -e "\t-h|--help: Display this help message."
    echo -e "Example: $0 --auth --deploy reference-hpu.yaml --telemetry --ui --grafana_password changeitplease --keycloak_admin_password changeitplease"
}

function print_header() {
    echo "$1"
    echo "-----------------------"
}

function print_log() {
    echo "-->$1"
}

function validate_deployment_settings() {
    local values_file="${gmc_path}/values.yaml"

    if [[ -z $(grep -E "^  hugToken: " "$values_file" | awk '{print $2}' | xargs) ]]; then
        print_log "Error: The hugToken value is required and must be set in $values_file"
        exit 1
    fi

    local deployment_manifest="$manifests_path/$1"
    if [[ ! -f $deployment_manifest ]]; then
        print_log "Error: Deployment manifest file '$deployment_manifest' does not exist."
        print_log "Pipelines available: $available_pipelines"

        exit 1
    fi


    for proxy in "httpProxy" "httpsProxy" "noProxy"; do
        proxy_name=$(echo "$proxy" | sed 's/P/_p/')
        uppercase_proxy_name=${proxy_name^^}

        if [[ -z $(grep -E "^  $proxy: " "$values_file" | awk '{print $2}' | xargs) && \
              (-n "${!proxy_name}" || -n "${!uppercase_proxy_name}") ]]; then
            print_log "Warning: $proxy is empty in $values_file but set in the environment. Consider updating the values file."
        fi
    done

    local edp_values_file="${edp_path}/values.yaml"

    if [[ -z $(grep -E "^hfToken: " "$edp_values_file" | awk '{print $2}' | xargs) ]]; then
        print_log "Error: The hfToken value is required and must be set in $edp_values_file"
        exit 1
    fi
}

function helm_install() {
    local path namespace name args

    namespace=$1
    name=$2
    path=$3
    args=$4
    shift
    shift
    shift
    shift
    args2=("$@")

    msg="installation"
    helm_cmd="install"
    if $helm_upgrade; then
      helm_cmd="upgrade --install"
      msg="upgrade or installation"
    fi

    if [ -z "$PIPELINE" ] || [[ ! "$PIPELINE" == *"hpu"* ]]; then
        helm_cmd+=" --values $manifests_path/resources-reference-cpu.yaml"
        helm_cmd+=" --values $manifests_path/resources-model-cpu.yaml"
    else
        helm_cmd+=" --values $manifests_path/resources-reference-hpu.yaml"
        helm_cmd+=" --values $manifests_path/resources-model-hpu.yaml"
    fi

    if $hpa_flag; then
        helm_cmd+=" --set hpaEnabled=true"
    fi

    IFS=',' read -ra feature_list <<< "$FEATURES"
    for feature in "${feature_list[@]}"; do
        case $feature in
            tdx)
                if [ -z "$KBS_ADDRESS" ]; then
                    print_log "Error: KBS_ADDRESS environment variable is not set. Exiting."
                    exit 1
                fi
                helm_cmd+=" --values $manifests_path/resources-tdx.yaml --set tdx.common.kbsAddress=${KBS_ADDRESS}"
                ;;
        esac
    done

    print_log "helm $msg of \"$name\" in \"$namespace\" namespace in progress ..."

    if [ -z "$args2" ]; then
      #print_log "helm $helm_cmd -n \"$namespace\" --create-namespace \"$name\" \"$path\" $args"
      if helm $helm_cmd -n "$namespace" --create-namespace "$name" "$path" $args 2> >(grep -v 'found symbolic link' >&2) > /dev/null; then
          print_log "helm $msg of \"$name\" in \"$namespace\" namespace finished successfully."
      else
          print_log "helm $msg of \"$name\" in \"$namespace\" namespace failed. Exiting"
          exit 1
      fi
    else
      command_args=""
      for param in "${args2[@]}"; do
        command_args+="$param,"
      done
      command_args="${command_args::-1}"
      #print_log "helm $helm_cmd -n \"$namespace\" --create-namespace \"$name\" \"$path\" $args --set \"$command_args\""
      if helm $helm_cmd -n "$namespace" --create-namespace "$name" "$path" $args --set "$command_args" 2> >(grep -v 'found symbolic link' >&2) > /dev/null; then
          print_log "helm $msg of \"$name\" in \"$namespace\" namespace finished successfully."
      else
          print_log "helm $msg of \"$name\" in \"$namespace\" namespace failed. Exiting"
          exit 1
      fi
    fi
}


function enforce_namespace_policy() {
    local namespace=$1
    local policy=$2

    if $strict_policy_flag; then
        kubectl label namespaces $namespace pod-security.kubernetes.io/enforce=$policy --overwrite
        kubectl label namespace $namespace pod-security.kubernetes.io/enforce-version=$K8S_VERSION --overwrite
    fi
}

# check if all pods in a namespace or specific pod by name are ready
function check_pods() {
    local namespace="$1"
    local deployment_name="$2"

    if [ -z "$deployment_name" ]; then
        # Check all pods in the namespace
        if kubectl get pods -n "$namespace" --no-headers -o custom-columns="NAME:.metadata.name,READY:.status.conditions[?(@.type=='Ready')].status,STATUS:.status.phase" | grep False | grep -v Succeeded &> /dev/null; then
            return 1
        else
            return 0
        fi
    else
        # Check specific pod by deployment name
        if kubectl get pods -n "$namespace" -l app="$deployment_name" --no-headers -o custom-columns="NAME:.metadata.name,READY:.status.conditions[?(@.type=='Ready')].status,STATUS:.status.phase" | grep False | grep -v Succeeded &> /dev/null; then
            return 1
        else
            return 0
        fi
    fi
}

function check_istio() {
    local istio_ns="$1"
    local label="$2"
    if kubectl get pods -n "$istio_ns" -l $label -o custom-columns="NAME:.metadata.name,READY:.status.conditions[?(@.type=='Ready')].status" | grep "False" &> /dev/null; then
        return 1
    else
        return 0
    fi
}

# waits until a provided condition function returns true
function wait_for_condition() {
    sleep 5 # safety measures for helm to initialize pod deployments
    local current_time
    local timeout=2700
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

function kill_process() {
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

function configure_ns_mesh() {
    ns=$1
    kubectl label namespace $ns istio.io/dataplane-mode=ambient --overwrite
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

        kubectl get namespace $GATEWAY_NS > /dev/null 2>&1 || kubectl create namespace $GATEWAY_NS
        kubectl get secret tls-secret -n $GATEWAY_NS > /dev/null 2>&1 || kubectl create secret tls tls-secret --key tls.key --cert tls.crt -n $GATEWAY_NS
    fi

    if $edp_flag; then
        kubectl get namespace $ENHANCED_DATAPREP_NS > /dev/null 2>&1 || kubectl create namespace $ENHANCED_DATAPREP_NS
        kubectl get secret tls-secret -n $ENHANCED_DATAPREP_NS > /dev/null 2>&1 || kubectl create secret tls tls-secret --key tls.key --cert tls.crt -n $ENHANCED_DATAPREP_NS
    fi
}

function start_fingerprint() {
    print_header "Start fingerprint"

    kubectl get namespace $FINGERPRINT_NS > /dev/null 2>&1 || kubectl create namespace $FINGERPRINT_NS
    enforce_namespace_policy $FINGERPRINT_NS "restricted"

    MONGO_DATABASE_NAME="SYSTEM_FINGERPRINT"

    FINGERPRINT_DB_USERNAME="usr"
    get_or_create_and_store_credentials MONGO_DB $FINGERPRINT_DB_USERNAME ""
    FINGERPRINT_DB_PASSWORD=${NEW_PASSWORD}

    FINGERPRINT_DB_ROOT_USERNAME="root"
    get_or_create_and_store_credentials MONGO_DB_ADMIN $FINGERPRINT_DB_ROOT_USERNAME ""
    FINGERPRINT_DB_ROOT_PASSWORD=${NEW_PASSWORD}

    # Secret for fingerprint db configuration
    create_database_secret "mongo" $FINGERPRINT_NS $FINGERPRINT_DB_USERNAME "$FINGERPRINT_DB_PASSWORD" $FINGERPRINT_NS $MONGO_DATABASE_NAME # for deployment for fingerprint namespace
    create_database_secret "mongo" $DEPLOYMENT_NS $FINGERPRINT_DB_USERNAME "$FINGERPRINT_DB_PASSWORD" $FINGERPRINT_NS $MONGO_DATABASE_NAME # for deployment via gmc manifests in chatqna namespace

    local HELM_INSTALL_FINGERPRINT_REPO
    HELM_INSTALL_FINGERPRINT_REPO="--set image.fingerprint.repository=$REGISTRY --set image.fingerprint.tag=$TAG"
    if $use_alternate_tagging; then
        HELM_INSTALL_FINGERPRINT_REPO="$HELM_INSTALL_FINGERPRINT_REPO --set alternateTagging=true"
    fi

    HELM_INSTALL_FINGERPRINT_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT $HELM_INSTALL_FINGERPRINT_REPO \
        --set mongodb.auth.usernames[0]=$FINGERPRINT_DB_USERNAME \
        --set mongodb.auth.passwords[0]=$FINGERPRINT_DB_PASSWORD \
        --set mongodb.auth.databases[0]=$MONGO_DATABASE_NAME \
        --set mongodb.auth.rootPassword=$FINGERPRINT_DB_ROOT_PASSWORD"

    if [[ "$FEATURES" == *"tdx"* ]]; then
      HELM_INSTALL_FINGERPRINT_TDX_ARGS=(
          "mongodb.runtimeClassName=kata-qemu-tdx"
          "mongodb.podAnnotations.io\\.containerd\\.cri\\.runtime-handler=kata-qemu-tdx"
#        HELM_INSTALL_FINGERPRINT_DEFAULT_ARGS+=" --set mongodb.podAnnotations.io\\.katacontainers\\.config\\.runtime\\.create_container_timeout='1800' --set "
          "mongodb.podAnnotations.io\\.katacontainers\\.config\\.hypervisor\\.kernel_params=agent\\.guest_components_rest_api=all agent\\.aa_kbc_params=cc_kbc::${KBS_ADDRESS}"
          "mongodb.image.pullPolicy=Always"
      )
    fi

    if ! helm repo list | grep -q 'bitnami' ; then helm repo add bitnami https://charts.bitnami.com/bitnami ; fi

    helm repo update > /dev/null
    helm dependency build "$fingerprint_path" > /dev/null

    helm_install "$FINGERPRINT_NS" fingerprint "$fingerprint_path" "$HELM_INSTALL_FINGERPRINT_DEFAULT_ARGS" "${HELM_INSTALL_FINGERPRINT_TDX_ARGS[@]}"
}

function create_secret() {
    local secret_name=$1
    local secret_namespace=$2
    local secret_data=$3

    kubectl get namespace $secret_namespace > /dev/null 2>&1 || kubectl create namespace $secret_namespace

    if kubectl get secret $secret_name -n $secret_namespace > /dev/null 2>&1; then
        print_log "Secret $secret_name already exists in $secret_namespace namespace. Proceeding with existing secret."
    else
        kubectl create secret generic $secret_name -n $secret_namespace --from-literal=$secret_data
    fi
}

function start_mesh() {
    # https://istio.io/latest/docs/ambient/install/helm/#base-components
    # Please note following instruction may be needed for multi node kind
    # https://medium.com/@SabujJanaCodes/touring-the-kubernetes-istio-ambient-mesh-part-1-setup-ztunnel-c80336fcfb2d
    # Install Istio
    print_log "Installing Istio"
    helm repo add istio https://istio-release.storage.googleapis.com/charts
    helm repo update

    kubectl get namespace $ISTIO_NS > /dev/null 2>&1 || kubectl create namespace $ISTIO_NS
    enforce_namespace_policy $ISTIO_NS "privileged"

    HELM_INSTALL_ISTIO_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT -f $istio_path/values.yaml"

    helm dependency build "$istio_path" > /dev/null

    IFS=',' read -ra feature_list <<< "$FEATURES"
    for feature in "${feature_list[@]}"; do
      case $feature in
        tdx)
          HELM_INSTALL_ISTIO_DEFAULT_ARGS+=" --values $istio_path/custom-init-container-values.yaml"
          ;;
      esac
    done

    helm_install $ISTIO_NS istio "$istio_path" "$HELM_INSTALL_ISTIO_DEFAULT_ARGS"

    print_log "waiting until pods in $ISTIO_NS are ready"
    wait_for_condition check_pods "$ISTIO_NS"
}

function clear_mesh() {
    print_log "Clear mesh"
    helm status -n $ISTIO_NS ztunnel > /dev/null 2>&1 && helm uninstall ztunnel -n $ISTIO_NS
    helm status -n $ISTIO_NS istio-cni > /dev/null 2>&1 && helm uninstall istio-cni -n $ISTIO_NS
    helm status -n $ISTIO_NS istiod > /dev/null 2>&1 && helm uninstall istiod -n $ISTIO_NS
    helm status -n $ISTIO_NS istio-base > /dev/null 2>&1 && helm uninstall istio-base -n $ISTIO_NS
    kubectl get ns $ISTIO_NS > /dev/null 2>&1 && kubectl delete ns $ISTIO_NS
    if kubectl get crd -o name | grep 'istio.io' > /dev/null 2>&1; then
        kubectl get crd -o name | grep 'istio.io' | xargs kubectl delete
    fi
}

# deploys GMConnector, chatqna pipeline and dataprep pipeline
function start_deployment() {
    local pipeline=$1

    print_header "Start deployment"

    # set values for helm charts
    bash set_values.sh -r "$REGISTRY" -t "$TAG"

    # create namespaces
    for ns in $GMC_NS $DEPLOYMENT_NS; do
        kubectl get namespace $ns > /dev/null 2>&1 || kubectl create namespace $ns
        enforce_namespace_policy $ns "restricted"
    done

    # Update redis password in chatQnA pipeline's manifest
    VECTOR_DB_USERNAME=default
    get_or_create_and_store_credentials VECTOR_DB $VECTOR_DB_USERNAME ""
    VECTOR_DB_PASSWORD=${NEW_PASSWORD}

    # Create or reuse secret for db configuration
    # Args: database_type, secret_namespace, username, password, namespace_with_database
    create_database_secret "redis" $DEPLOYMENT_NS $VECTOR_DB_USERNAME $VECTOR_DB_PASSWORD $DEPLOYMENT_NS

    local HELM_INSTALL_DEPLOYMENT_TAGGING
    if $use_alternate_tagging; then
        HELM_INSTALL_DEPLOYMENT_TAGGING="--set alternateTagging=true"
    fi

    helm_install $GMC_NS gmc "$gmc_path" "$HELM_INSTALL_DEPLOYMENT_TAGGING"

    # Fingerprint deployment
    local deployment_manifest="$manifests_path/$pipeline"
    if grep -q "Fingerprint" $deployment_manifest; then
        start_fingerprint
    fi

    wait_for_condition check_pods "$GMC_NS"
    # Apply deployment manifest
    kubectl apply -f $deployment_manifest
    wait_for_condition check_pods "$DEPLOYMENT_NS"
}

function clear_deployment() {
    print_header "Clear deployment"

    kubectl get ns $DEPLOYMENT_NS > /dev/null 2>&1 && kubectl delete ns $DEPLOYMENT_NS

    kubectl get crd gmconnectors.gmc.opea.io > /dev/null 2>&1 && kubectl delete crd gmconnectors.gmc.opea.io

    helm status -n $GMC_NS gmc > /dev/null 2>&1 && helm delete -n $GMC_NS gmc
    kubectl get ns $GMC_NS > /dev/null 2>&1 && kubectl delete ns $GMC_NS
}

function clear_fingerprint() {
    print_header "Clear fingerprint"

    helm status -n $FINGERPRINT_NS fingerprint > /dev/null 2>&1 && helm uninstall -n $FINGERPRINT_NS fingerprint
    kubectl get ns $FINGERPRINT_NS > /dev/null 2>&1 && kubectl delete ns $FINGERPRINT_NS
}

function start_telemetry() {
    print_header "Start telemetry"
    get_or_create_and_store_credentials GRAFANA admin $GRAFANA_PASSWORD
    GRAFANA_PASSWORD=${NEW_PASSWORD}

    ### Base variables
    # shellcheck disable=SC2154
    HELM_INSTALL_TELEMETRY_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT --set kube-prometheus-stack.grafana.env.http_proxy=$http_proxy --set kube-prometheus-stack.grafana.env.https_proxy=$https_proxy --set kube-prometheus-stack.grafana.env.no_proxy=127.0.0.1\,localhost\,monitoring\,monitoring-traces --set kube-prometheus-stack.grafana.adminPassword=$GRAFANA_PASSWORD"
    echo "*** Telemetry 'base' variables:"
    echo "HELM_INSTALL_TELEMETRY_DEFAULT_ARGS: $HELM_INSTALL_TELEMETRY_DEFAULT_ARGS"
    echo "HELM_INSTALL_TELEMETRY_EXTRA_ARGS: $HELM_INSTALL_TELEMETRY_EXTRA_ARGS"

    ### Logs variables
    local HELM_INSTALL_TELEMETRY_REPO
    if $use_alternate_tagging; then
        HELM_INSTALL_TELEMETRY_REPO="--set otelcol-logs.image.repository=$REGISTRY --set otelcol-logs.image.tag=erag-otelcol-contrib-journalctl_$TAG"
    else
        HELM_INSTALL_TELEMETRY_REPO="--set otelcol-logs.image.repository=$REGISTRY/erag-otelcol-contrib-journalctl --set otelcol-logs.image.tag=$TAG"
    fi

    TELEMETRY_LOGS_IMAGE="--wait --timeout $HELM_TIMEOUT $HELM_INSTALL_TELEMETRY_REPO"
    TELEMETRY_LOGS_JOURNALCTL="-f $telemetry_logs_path/values-journalctl.yaml"
    HELM_INSTALL_TELEMETRY_LOGS_DEFAULT_ARGS="--wait $TELEMETRY_LOGS_IMAGE  $TELEMETRY_LOGS_JOURNALCTL $LOKI_DNS_FLAG"
    echo "*** Telemetry 'logs' variables:"
    echo "HELM_INSTALL_TELEMETRY_LOGS_DEFAULT_ARGS: $HELM_INSTALL_TELEMETRY_LOGS_DEFAULT_ARGS"
    echo "HELM_INSTALL_TELEMETRY_LOGS_EXTRA_ARGS: $HELM_INSTALL_TELEMETRY_LOGS_EXTRA_ARGS"

    ### Traces variables
    HELM_INSTALL_TELEMETRY_TRACES_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT $TEMPO_DNS_FLAG"
    echo "*** Telemetry 'traces' variables:"
    echo "HELM_INSTALL_TELEMETRY_TRACES_DEFAULT_ARGS: $HELM_INSTALL_TELEMETRY_TRACES_DEFAULT_ARGS"
    echo "HELM_INSTALL_TELEMETRY_TRACES_EXTRA_ARGS: $HELM_INSTALL_TELEMETRY_TRACES_EXTRA_ARGS"

    # Please use following for any additional flag (for development only):
    kubectl get namespace $TELEMETRY_NS > /dev/null 2>&1 || kubectl create namespace $TELEMETRY_NS
    enforce_namespace_policy $TELEMETRY_NS "privileged"
    kubectl get namespace $TELEMETRY_TRACES_NS > /dev/null 2>&1 || kubectl create namespace $TELEMETRY_TRACES_NS
    enforce_namespace_policy $TELEMETRY_TRACES_NS "privileged"

    # add repo if needed
    if ! helm repo list | grep -q 'prometheus-community' ; then helm repo add prometheus-community https://prometheus-community.github.io/helm-charts ; fi # for prometheus/k8s/prometheus operator
    if ! helm repo list | grep -q 'grafana' ; then helm repo add grafana https://grafana.github.io/helm-charts ; fi # for grafana/loki/tempo
    if ! helm repo list | grep -q 'opensearch' ; then helm repo add opensearch https://opensearch-project.github.io/helm-charts/ ; fi # opensearch
    if ! helm repo list | grep -q 'open-telemetry' ; then helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts ; fi # opentelemetry collector/opentelemetry operator

    helm repo update  > /dev/null

    # I) telemetry/base (metrics)
    helm dependency build "$telemetry_path" > /dev/null
    helm_install $TELEMETRY_NS telemetry "$telemetry_path" "$HELM_INSTALL_TELEMETRY_DEFAULT_ARGS $HELM_INSTALL_TELEMETRY_EXTRA_ARGS"
    # install prometheus-adapter if hpa is emabled
    HELM_INSTALL_HPA_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT -f $hpa_path/prometheus_adapter.yaml"
    if $hpaEnabled; then
        helm_install $TELEMETRY_NS prometheus-adapter "$HPA_HELM" "$HELM_INSTALL_HPA_DEFAULT_ARGS $HELM_INSTALL_AUTH_EXTRA_ARGS"
    fi

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
    helm_install "$TELEMETRY_TRACES_NS" telemetry-traces-instr "$telemetry_traces_instr_path" "--set instrumentation.namespaces={$DEPLOYMENT_NS}"
    # IIIb) telemetry/traces-instr check
    print_log "waiting until pods in $TELEMETRY_TRACES_NS are ready"
    wait_for_condition check_pods "$TELEMETRY_TRACES_NS"
}

function clear_telemetry() {
    print_header "Clear telemetry"
    # Timeout duration for deleting otelcol-traces
    local OTELCOL_DELETE_TIMEOUT=60

    # Delete the tls-secret if it exists
    kubectl get secret tls-secret -n $TELEMETRY_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $TELEMETRY_NS

    # uninstall prometheus adapter first
    helm status -n "$TELEMETRY_NS" prometheus-adapter > /dev/null 2>&1 && helm uninstall --namespace $TELEMETRY_NS prometheus-adapter

    # Delete otelcol-traces with timeout and webhook handling
    if kubectl get otelcols/otelcol-traces -n "$TELEMETRY_TRACES_NS" > /dev/null 2>&1; then
        echo "Attempting to delete otelcol-traces (timeout: ${OTELCOL_DELETE_TIMEOUT} seconds)..."

        # Set a timeout for deletion of otelcol-traces
        if ! timeout ${OTELCOL_DELETE_TIMEOUT} kubectl delete otelcols/otelcol-traces -n "$TELEMETRY_TRACES_NS"; then
            echo "Deletion of otelcol-traces is taking too long. Removing webhook and finalizer..."

            # Delete the webhooks if it exists
            kubectl get mutatingwebhookconfiguration telemetry-traces-otel-operator-mutation > /dev/null 2>&1 && \
            kubectl delete mutatingwebhookconfiguration telemetry-traces-otel-operator-mutation

            kubectl get validatingwebhookconfiguration telemetry-traces-otel-operator-validation > /dev/null 2>&1 && \
            kubectl delete validatingwebhookconfiguration telemetry-traces-otel-operator-validation

            # Remove the finalizer blocking deletion
            kubectl patch otelcols otelcol-traces -n "$TELEMETRY_TRACES_NS" --type='merge' -p '{"metadata":{"finalizers":[]}}'

            # Force delete the resource
            kubectl delete otelcols/otelcol-traces -n "$TELEMETRY_TRACES_NS" --force --grace-period=0
        fi
    fi

    helm status -n "$TELEMETRY_TRACES_NS" telemetry-traces-instr > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_TRACES_NS" telemetry-traces-instr
    helm status -n "$TELEMETRY_TRACES_NS" telemetry-traces > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_TRACES_NS" telemetry-traces
    helm status -n "$TELEMETRY_NS" telemetry-logs > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_NS" telemetry-logs
    helm status -n "$TELEMETRY_NS" telemetry > /dev/null 2>&1 && helm uninstall -n "$TELEMETRY_NS" telemetry

    kubectl get ns $TELEMETRY_TRACES_NS > /dev/null 2>&1 && kubectl delete ns $TELEMETRY_TRACES_NS
    kubectl get ns $TELEMETRY_NS > /dev/null 2>&1 && kubectl delete ns $TELEMETRY_NS
}

function start_authentication() {
    local introspection_url

    print_header "Start authentication"

    kubectl get namespace $AUTH_NS > /dev/null 2>&1 || kubectl create namespace $AUTH_NS
    enforce_namespace_policy $AUTH_NS "restricted"

    get_or_create_and_store_credentials KEYCLOAK_REALM_ADMIN admin $KEYCLOAK_PASS
    KEYCLOAK_PASS=${NEW_PASSWORD}

    HELM_INSTALL_AUTH_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT --version $KEYCLOAK_CHARTS_VERSION --set auth.adminUser=$keycloak_user --set auth.adminPassword=$KEYCLOAK_PASS -f $keycloak_path/values.yaml"

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

    # fix paths across scripts
    cd "$scripts_path" && bash keycloak_configurator.sh "$KEYCLOAK_PASS" ; cd - > /dev/null 2>&1

    # create apisix-secret with client_secret
    if ! kubectl get secret apisix-secret -n $GATEWAY_NS > /dev/null 2>&1; then
        client_secret=$(bash "$scripts_path"/get_secret.sh $KEYCLOAK_PASS)
        create_secret apisix-secret $GATEWAY_NS "CLIENT_SECRET=$client_secret"
    fi

    kill -2 $PID
    kill_process "kubectl port-forward --namespace $AUTH_NS svc/keycloak"
}

function clear_authentication() {
    print_header "Clear authentication"

    kubectl get secret tls-secret -n $AUTH_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $AUTH_NS

    helm status -n "$AUTH_NS" keycloak > /dev/null 2>&1 && helm -n "$AUTH_NS" uninstall keycloak

    if kubectl get pvc -n "$AUTH_NS" data-keycloak-postgresql-0 > /dev/null 2>&1; then
        print_log "waiting until keycloak pods are terminated."
        wait_for_condition check_pods "$AUTH_NS"
    fi

    kubectl get ns $AUTH_NS > /dev/null 2>&1 && kubectl delete ns $AUTH_NS
}

function start_ingress() {
    print_header "Start ingress"

    kubectl get namespace $INGRESS_NS > /dev/null 2>&1 || kubectl create namespace $INGRESS_NS
    enforce_namespace_policy $INGRESS_NS "privileged"

    # Install ingress
    if ! helm repo list | grep -q 'ingress-nginx' ; then helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx ; fi
    helm repo update > /dev/null
    helm_install "$INGRESS_NS" ingress-nginx "$INGRESS_HELM" "$HELM_INSTALL_INGRESS_DEFAULT_ARGS"

    print_log "waiting until pods in $INGRESS_NS are ready"
    wait_for_condition check_pods "$INGRESS_NS"
}

function clear_ingress() {
    print_header "Clear ingress"

    helm status -n "$INGRESS_NS" ingress-nginx > /dev/null 2>&1 && helm delete -n "$INGRESS_NS" ingress-nginx
}

function start_gateway() {
    print_header "Start gateway"

    kubectl get ns $ENHANCED_DATAPREP_NS > /dev/null 2>&1 || kubectl create ns $ENHANCED_DATAPREP_NS
    kubectl get ns $DEPLOYMENT_NS > /dev/null 2>&1 || kubectl create ns $DEPLOYMENT_NS
    kubectl get ns $FINGERPRINT_NS > /dev/null 2>&1 || kubectl create ns $FINGERPRINT_NS
    kubectl get ns $UI_NS > /dev/null 2>&1 || kubectl create ns $UI_NS

    kubectl get namespace $GATEWAY_NS > /dev/null 2>&1 || kubectl create namespace $GATEWAY_NS
    enforce_namespace_policy $GATEWAY_NS "privileged"

    helm dependency update "$api_gateway_path" > /dev/null
    helm_install "$GATEWAY_NS" auth-apisix "$api_gateway_path" "$HELM_INSTALL_GATEWAY_DEFAULT_ARGS"

    print_log "waiting until pods in $GATEWAY_NS are ready"
    wait_for_condition check_pods "$GATEWAY_NS"

    helm_install "$GATEWAY_NS" auth-apisix-crds "$api_gateway_crd_path" "$HELM_INSTALL_GATEWAY_CRD_DEFAULT_ARGS"

    print_log "waiting until pods in $GATEWAY_NS are ready"
    wait_for_condition check_pods "$GATEWAY_NS"
}


function clear_gateway() {
    print_header "Clear gateway"

    kubectl get secret tls-secret -n $GATEWAY_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $GATEWAY_NS
    kubectl get secret apisix-secret -n $GATEWAY_NS> /dev/null 2>&1 && kubectl delete secret apisix-secret -n $GATEWAY_NS

    helm status -n "$GATEWAY_NS" auth-apisix-crds > /dev/null 2>&1 &&  helm uninstall auth-apisix-crds -n "$GATEWAY_NS"
    helm status -n "$GATEWAY_NS" auth-apisix > /dev/null 2>&1 &&  helm uninstall auth-apisix -n "$GATEWAY_NS"

    kubectl get ns $GATEWAY_NS > /dev/null 2>&1 && kubectl delete ns $GATEWAY_NS
}

function start_ui() {
    print_header "Start ui"

    kubectl get namespace $UI_NS > /dev/null 2>&1 || kubectl create namespace $UI_NS
    enforce_namespace_policy $UI_NS "restricted"

    helm_install "$UI_NS" chatqa-app "$ui_path" "$HELM_INSTALL_UI_DEFAULT_ARGS"

    print_log "waiting until pods $UI_NS are ready."
    wait_for_condition check_pods "$UI_NS"
}

function start_edp() {
    local pipeline=$1
    local edp_dataprep_type=$2
    print_header "Start Enhanced Dataprep"

    # Update redis password in chatQnA pipeline's manifest
    VECTOR_DB_USERNAME=default
    get_or_create_and_store_credentials VECTOR_DB $VECTOR_DB_USERNAME ""
    VECTOR_DB_PASSWORD=${NEW_PASSWORD}

    # Create or reuse secret for db configuration
    # Args: database_type, secret_namespace, username, password, namespace_with_database
    create_database_secret "redis" $ENHANCED_DATAPREP_NS $VECTOR_DB_USERNAME $VECTOR_DB_PASSWORD $DEPLOYMENT_NS
    create_database_secret "redis" $TELEMETRY_NS $VECTOR_DB_USERNAME $VECTOR_DB_PASSWORD $DEPLOYMENT_NS  # for redis exporter in telemetry namespace

    kubectl get namespace $ENHANCED_DATAPREP_NS > /dev/null 2>&1 || kubectl create namespace $ENHANCED_DATAPREP_NS
    enforce_namespace_policy $ENHANCED_DATAPREP_NS "restricted"

    start_and_keep_port_forwarding "keycloak" "$AUTH_NS" "$KEYCLOAK_FPORT" 80 &
    PID=$!

    sleep 2 # needs a while to work fine
    local minio_keycloak_client_id="EnterpriseRAG-oidc-minio"

    # get passwd from file
    get_or_create_and_store_credentials KEYCLOAK_REALM_ADMIN admin $KEYCLOAK_PASS
    KEYCLOAK_PASS=${NEW_PASSWORD}
    local minio_client_secret=$(bash "$scripts_path"/get_secret.sh $KEYCLOAK_PASS $minio_keycloak_client_id)

    kill -2 $PID
    kill_process "kubectl port-forward --namespace $AUTH_NS svc/keycloak"

    local redis_username="default"
    get_or_create_and_store_credentials EDP_REDIS $redis_username ""
    local redis_password=${NEW_PASSWORD}

    local postgresql_edp_username="edp"
    get_or_create_and_store_credentials EDP_POSTGRESQL $postgresql_edp_username ""
    local postgresql_edp_password=${NEW_PASSWORD}

    local postgresql_admin_username="admin"
    get_or_create_and_store_credentials EDP_POSTGRESQL_ADMIN $postgresql_admin_username ""
    local postgresql_admin_password=${NEW_PASSWORD}

    local erag_http_proxy=$(awk '/httpProxy:/ {gsub(/"/, "", $2); print $2}' "$gmc_path/values.yaml")
    local erag_https_proxy=$(awk '/httpsProxy:/ {gsub(/"/, "", $2); print $2}' "$gmc_path/values.yaml")
    local erag_no_proxy=$(awk '/noProxy:/ {gsub(/"/, "", $2); print $2}' "$gmc_path/values.yaml")

    local embedding_endpoint_helm=""
    if [[ "$pipeline" == "examples/cpu-torch.yaml" ]]; then
        embedding_endpoint_helm=" --set embedding.enabled=true --set embedding.config.modelServer=torchserve --set embedding.config.modelServerEndpoint=http://torchserve-embedding-svc.chatqa.svc:8090 "
    elif [[ "$pipeline" == "examples/cpu-tei.yaml" ]]; then
        embedding_endpoint_helm=" --set embedding.enabled=true --set embedding.config.modelServer=tei --set embedding.config.modelServerEndpoint=http://tei-embedding-svc.chatqa.svc:80 "
    else
        embedding_endpoint_helm=" --set embedding.enabled=false --set embedding.remoteEmbeddingUri=http://embedding-svc.chatqa.svc:6000/v1/embeddings " # use default embedding from chatqa
    fi

    HELM_INSTALL_EDP_CONFIGURATION_ARGS="$embedding_endpoint_helm --set postgresAdminPassword=$postgresql_admin_password --set postgresDatabasePassword=$postgresql_edp_password --set proxy.httpProxy=$erag_http_proxy --set proxy.httpsProxy=$erag_https_proxy --set proxy.noProxy=$(echo "$erag_no_proxy" | sed 's/,/\\,/g') "

    if $dpguard; then
        print_log "Enabling Dataprep Guardrail"
        HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set dpguard.enabled=true --set dpguard.tag=$TAG"
    fi

    # Enable advanced RAG techniques
    if $semantic_chunking; then
        print_log "Enabling Semantic Chunking"
        HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set dataprep.semantic_chunking_enabled=true"
        if [[ "$pipeline" == *"torch"* || "$pipeline" == *"reference"* ]]; then
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set dataprep.config.embedding_model_server=torchserve --set dataprep.config.embedding_model_server_endpoint=http://torchserve-embedding-svc.chatqa.svc:8090"
        else
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set dataprep.config.embedding_model_server=tei --set dataprep.config.embedding_model_server_endpoint=http://tei-embedding-svc.chatqa.svc:80"
        fi
    elif [[ "$edp_dataprep_type" == "hierarchical" ]]; then
        print_log "Enabling Hierarchical Dataprep"
        HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set dataprep.name=hierarchical_dataprep"

        if [[ "$pipeline" == *"cpu"* ]]; then
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set dataprep.config.vllm_server_endpoint=http://vllm-service-m.chatqa.svc:8000" # Use existing vllm-cpu server
        else
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set vllm.enabled=true" # Spin up new vllm-cpu server
        fi
    fi

    helm dependency update "$edp_path" > /dev/null

    STORAGE_TYPE="${edp_storage_type:-""}"
    case $STORAGE_TYPE in
        s3)
            print_log "Using AWS S3 storage"
            region=${s3_region:-"us-west-2"}
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set minio.enabled=false --set awsSqs.enabled=true --set edpExternalUrl=https://s3.amazonaws.com --set edpInternalUrl=https://s3.amazonaws.com --set edpBaseRegion=$region --set edpAccessKey=$s3_access_key --set edpSecretKey=$s3_secret_key --set edpSqsEventQueueUrl=$s3_sqs_queue --set bucketNameRegexFilter=$s3_bucket_name_regex_filter "
            ;;
        s3compatible)
            print_log "Using S3 API compatible storage"
            region=${s3_region:-"us-west-2"}
            s3_cert_verify="${s3_cert_verify:-"true"}"
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set minio.enabled=false --set awsSqs.enabled=false --set edpExternalUrl=$s3_compatible_endpoint --set edpInternalUrl=$s3_compatible_endpoint --set edpBaseRegion=$region --set edpAccessKey=$s3_access_key --set edpSecretKey=$s3_secret_key --set edpInternalCertVerify=$s3_cert_verify --set edpExternalCertVerify=$s3_cert_verify --set bucketNameRegexFilter=$s3_bucket_name_regex_filter "
            ;;
        minio | "")
            print_log "Using Minio storage"
            local minio_access_key=$(tr -dc 'A-Za-z0-9!?%' < /dev/urandom | head -c 10)
            local minio_secret_key=$(tr -dc 'A-Za-z0-9!?%' < /dev/urandom | head -c 16)
            HELM_INSTALL_EDP_CONFIGURATION_ARGS="$HELM_INSTALL_EDP_CONFIGURATION_ARGS --set minio.enabled=true --set awsSqs.enabled=false --set edpExternalUrl=https://s3.erag.com --set edpInternalUrl=http://edp-minio:9000 --set edpAccessKey=$minio_access_key --set edpSecretKey=$minio_secret_key --set edpOidcClientSecret=$minio_client_secret "
            ;;
    esac

    if [[ "$FEATURES" == *"tdx"* ]]; then
        ROOT_PASSWORD=$(kubectl get secret --namespace $ENHANCED_DATAPREP_NS edp-minio -o jsonpath="{.data.root-password}" | base64 -d)
        HELM_INSTALL_TDX_ARGS=(
          "minio.runtimeClassName=kata-qemu-tdx"
          "postgresql.primary.extraPodSpec.runtimeClassName=kata-qemu-tdx"
          "redis.master.extraPodSpec.runtimeClassName=kata-qemu-tdx"
          ## "minio.imagePullSecrets=runtimeClassName=kata-qemu-tdx"
          # "minio.provisioning.spec.template.metadata.spec.runtimeClassName=kata-qemu-tdx"
          "minio.podAnnotations.io\\.containerd\\.cri\\.runtime-handler=kata-qemu-tdx"
          "postgresql.primary.podAnnotations.io\\.containerd\\.cri\\.runtime-handler=kata-qemu-tdx"
          "redis.master.podAnnotations.io\\.containerd\\.cri\\.runtime-handler=kata-qemu-tdx"
          # "minio.provisioning.podAnnotations.io\\.containerd\\.cri\\.runtime-handler=kata-qemu-tdx"
          "postgresql.primary.containers.imagePullPolicy=Always"
          "redis.master.containers.imagePullPolicy=Always"
          "minio.image.PullPolicy=Always"
          "global.postgresql.auth.password=$postgresql_edp_password"
          "minio.podAnnotations.io\\.katacontainers\\.config\\.hypervisor\\.kernel_params=agent\\.guest_components_rest_api=all agent\\.aa_kbc_params=cc_kbc::${KBS_ADDRESS}"
          "postgresql.primary.podAnnotations.io\\.katacontainers\\.config\\.hypervisor\\.kernel_params=agent\\.guest_components_rest_api=all agent\\.aa_kbc_params=cc_kbc::${KBS_ADDRESS}"
          "redis.master.podAnnotations.io\\.katacontainers\\.config\\.hypervisor\\.kernel_params=agent\\.guest_components_rest_api=all agent\\.aa_kbc_params=cc_kbc::${KBS_ADDRESS}"
          # "minio.provisioning.podAnnotations.io\\.katacontainers\\.config\\.hypervisor\\.kernel_params=agent\\.guest_components_rest_api=all agent\\.aa_kbc_params=cc_kbc::${KBS_ADDRESS}"
      )
      if [ ! -z "$ROOT_PASSWORD" ]; then
        HELM_INSTALL_TDX_ARGS+=("auth.rootPassword=$ROOT_PASSWORD")
      fi
    fi

    helm_install $ENHANCED_DATAPREP_NS edp "$edp_path" "$HELM_INSTALL_EDP_DEFAULT_ARGS $HELM_INSTALL_EDP_CONFIGURATION_ARGS --set redisUsername=$redis_username --set redisPassword=$redis_password" "${HELM_INSTALL_TDX_ARGS[@]}"

    print_log "waiting until pods in $ENHANCED_DATAPREP_NS are ready"
    wait_for_condition check_pods "$ENHANCED_DATAPREP_NS"
}

function clear_edp() {
    print_header "Clear Enhanced Dataprep"

    kubectl get secret tls-secret -n $ENHANCED_DATAPREP_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $ENHANCED_DATAPREP_NS

    helm status -n $ENHANCED_DATAPREP_NS edp > /dev/null 2>&1 && helm uninstall -n $ENHANCED_DATAPREP_NS edp
    kubectl get ns $ENHANCED_DATAPREP_NS > /dev/null 2>&1 && kubectl delete ns $ENHANCED_DATAPREP_NS
}

function clear_ui() {
    print_header "Clear UI"

    kubectl get secret tls-secret -n $UI_NS > /dev/null 2>&1 && kubectl delete secret tls-secret -n $UI_NS
    helm status -n $UI_NS chatqa-app > /dev/null 2>&1 && helm uninstall -n $UI_NS chatqa-app

    kubectl get ns $UI_NS > /dev/null 2>&1 && kubectl delete ns $UI_NS
}

function clear_all_ns() {
    print_header "removing all EnterpriseRAG namespaces"

    kubectl get ns $DEPLOYMENT_NS > /dev/null 2>&1 && kubectl delete ns $DEPLOYMENT_NS
    kubectl get ns $ENHANCED_DATAPREP_NS > /dev/null 2>&1 && kubectl delete ns $ENHANCED_DATAPREP_NS
    kubectl get ns $TELEMETRY_NS > /dev/null 2>&1 && kubectl delete ns $TELEMETRY_NS
    kubectl get ns $TELEMETRY_TRACES_NS > /dev/null 2>&1 && kubectl delete ns $TELEMETRY_TRACES_NS
    kubectl get ns $GMC_NS > /dev/null 2>&1 && kubectl delete ns $GMC_NS
    kubectl get ns $GATEWAY_NS > /dev/null 2>&1 && kubectl delete ns $GATEWAY_NS
    kubectl get ns $UI_NS > /dev/null 2>&1 && kubectl delete ns $UI_NS
    kubectl get ns $INGRESS_NS > /dev/null 2>&1 && kubectl delete ns $INGRESS_NS
    kubectl get ns $AUTH_NS > /dev/null 2>&1 && kubectl delete ns $AUTH_NS
    kubectl get ns $FINGERPRINT_NS > /dev/null 2>&1 && kubectl delete ns $FINGERPRINT_NS
    kubectl get ns $ISTIO_NS > /dev/null 2>&1 && kubectl delete ns $ISTIO_NS
}

# Initialize flags
# if true then any service is about to get created
create_flag=false
deploy_flag=false
test_flag=false
telemetry_flag=false
hpa_flag=false
ui_flag=false
# mesh installation is undecided, unless deploy is given or mesh explicitly requested
default_mesh_flag=true
mesh_flag=""
mesh_installed=false
auth_flag=false
helm_upgrade=false
edp_flag=true
dpguard=false
semantic_chunking=false
strict_policy_flag=false
clear_any_flag=false
clear_deployment_flag=false
clear_fingerprint_flag=false
clear_ui_flag=false
clear_telemetry_flag=false
clear_hpa_flag=false
clear_mesh_flag=false
clear_all_flag=false
clear_auth_flag=false
clear_edp_flag=false
use_alternate_tagging=false


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
            create_flag=true
            ;;
        -g|--grafana_password)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --grafana_password. Please provide inital password for Grafana."
                usage
                exit 1
            fi
            GRAFANA_PASSWORD=$1
            ;;
        -k|--keycloak_admin_password)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --keycloak_admin_password. Please provide inital password for Keycloak admin."
                usage
                exit 1
            fi
            KEYCLOAK_PASS=$1
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
        --use-alternate-tagging)
            use_alternate_tagging=true
            ;;
        --test)
            test_flag=true
            ;;
        --telemetry)
            telemetry_flag=true
            create_flag=true
            ;;
        --hpa)
            hpa_flag=true
            create_flag=true
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
        --ui)
            ui_flag=true
            create_flag=true
            ;;
        -ep|--enforce-pss)
            strict_policy_flag=true
            ;;
        --no-edp)
            edp_flag=false
            ;;
        --dpguard)
            dpguard=true
            ;;
        --semantic-chunking)
            semantic_chunking=true
            ;;
        --edp-dataprep-type)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --edp-dataprep-type. Please provide a valid dataprep type."
                usage
                exit 1
            fi
            EDP_DATAPREP_TYPE=$1
            ;;
        --no-mesh)
            mesh_flag=false
            ;;
        --mesh)
            # explicitly request mesh, even outside deployment
            mesh_flag=true
            ;;
        --upgrade)
            helm_upgrade=true
            ;;
        --auth)
            auth_flag=true
            create_flag=true
            ;;
        --timeout)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --timeout. Please provide a valid timeout."
                usage
                exit 1
            fi
            HELM_TIMEOUT=$1
            ;;
        -ce|--clear-edp)
            clear_edp_flag=true
            clear_any_flag=true
            ;;
        -ch|--clear-auth)
            clear_auth_flag=true
            clear_any_flag=true
            ;;
        -cd|--clear-deployment)
            clear_deployment_flag=true
            clear_any_flag=true
            ;;
        -cu|--clear-ui)
            clear_ui_flag=true
            clear_any_flag=true
            ;;
        -ct|--clear-telemetry)
            clear_telemetry_flag=true
            clear_any_flag=true
            ;;
        -cf|--clear-fingerprint)
            clear_fingerprint_flag=true
            clear_any_flag=true
            ;;
        -cm|--clear-mesh)
            clear_mesh_flag=true
            mesh_flag=false
            clear_any_flag=true
            ;;
        -ca|--clear-all)
            clear_all_flag=true
            clear_any_flag=true
            ;;
        --features)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                print_log "Error: Invalid or no parameter provided for --features. Please provide a comma-separated list of features."
                usage
                exit 1
            fi
            FEATURES=$1
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

if $deploy_flag; then
    validate_deployment_settings "$PIPELINE"
fi

# additional logic for-default settings
# - if mesh not given explicitly:
#   - mesh is by default (true) for deployment
#   - otherwise it is auto-detected,
#     and will be installed if new services are started
# - if given alone:
#   - will be installed
if [ -z $mesh_flag ]; then
    if $deploy_flag; then
        mesh_flag=$default_mesh_flag
    elif $create_flag; then
        # auto-detect istio
        if helm status -n $ISTIO_NS istio-base > /dev/null 2>&1; then
            echo "Mesh detected and enabled for new services"
            mesh_installed=true
            mesh_flag=true
        else
            mesh_flag=false
        fi
    fi
fi

# Additional validation for required parameters
if [[ "$telemetry_flag" == "true" ]]; then
    # system validation (for journald/ctl systemd OpenTelemetry collector)
    if  [[ $(sysctl -n fs.inotify.max_user_instances) -lt 8000 ]]; then
        print_log "Error: Host OS System is not configured properly. Insufficent inotify.max_user_instances < 8000 (for OpenTelemetry systemd/journald collector). Did you run configure.sh? Or fix it with: sudo sysctl -w fs.inotify.max_user_instances=8192"
        exit 1
    fi
fi

if [[ "$FEATURES" == *"tdx"* ]]; then
  if [[ ! "$PIPELINE" == *"cpu"* ]]; then
    print_log "Error: TDX feature is only supported for cpu pipelines."
    exit 1
  fi

  if [[ "$REGISTRY" == *"localhost"* ]]; then
      print_log "Error: TDX feature is only supported for public image registries."
      exit 1
    fi
fi


HELM_INSTALL_UI_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT --set image.ui.repository=$REGISTRY --set image.ui.tag=$TAG"
HELM_INSTALL_EDP_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT --set celery.repository=$REGISTRY --set celery.tag=$TAG --set flower.repository=$REGISTRY --set flower.tag=$TAG --set backend.repository=$REGISTRY --set backend.tag=$TAG --set dataprep.repository=$REGISTRY --set dataprep.tag=$TAG  --set embedding.repository=$REGISTRY --set embedding.tag=$TAG --set ingestion.repository=$REGISTRY --set ingestion.tag=$TAG --set awsSqs.repository=$REGISTRY --set awsSqs.tag=$TAG --set dpguard.repository=$REGISTRY --set dpguard.tag=$TAG --set vllm.repository=$REGISTRY --set vllm.tag=$TAG"
if $use_alternate_tagging; then
    HELM_INSTALL_UI_DEFAULT_ARGS="$HELM_INSTALL_UI_DEFAULT_ARGS --set alternateTagging=true"
    HELM_INSTALL_EDP_DEFAULT_ARGS="$HELM_INSTALL_EDP_DEFAULT_ARGS --set alternateTagging=true"
fi

HELM_INSTALL_INGRESS_DEFAULT_ARGS="--timeout $HELM_TIMEOUT --version $INGRESS_CHARTS_VERSION -f $ingress_path/values.yaml"
HELM_INSTALL_GATEWAY_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT"
HELM_INSTALL_GATEWAY_CRD_DEFAULT_ARGS="--wait --timeout $HELM_TIMEOUT"

# Execute given arguments

# allow istio to inject during the upgrade process
if [[ "$helm_upgrade" == "true" && ( "$mesh_installed" == "true" || "$mesh_flag" == "true" ) ]]; then
    istio_protected_ns_list=$(kubectl get namespaces -l erag-istio-protected=true -o jsonpath='{.items[*].metadata.name}')

    for ns in $istio_protected_ns_list; do
        kubectl label namespace $ns erag-istio-protected=false --overwrite
        kubectl label namespace $ns istio.io/dataplane-mode- --overwrite
    done
fi

if $create_flag; then
    create_certs
fi

if $mesh_flag && $create_flag; then
    if ! $mesh_installed || $helm_upgrade; then
        start_mesh
    fi
fi

updated_ns_list=()

if $auth_flag; then
    start_authentication
    start_gateway
    start_ingress
    updated_ns_list+=($AUTH_NS $GATEWAY_NS $INGRESS_NS)
fi

if $deploy_flag; then
    start_deployment "$PIPELINE"
    updated_ns_list+=($GMC_NS $DEPLOYMENT_NS $FINGERPRINT_NS)
fi

if $ui_flag; then
    start_ui
    updated_ns_list+=($UI_NS)
fi

if $edp_flag && ! $clear_any_flag; then
    start_edp "$PIPELINE" "$EDP_DATAPREP_TYPE"
    updated_ns_list+=($ENHANCED_DATAPREP_NS)
fi

if $telemetry_flag; then
    start_telemetry
    updated_ns_list+=($TELEMETRY_NS $TELEMETRY_TRACES_NS)
fi

if $mesh_flag && $create_flag; then
    # introduce namespace into mesh
    for ns in "${updated_ns_list[@]}"; do
        configure_ns_mesh $ns
    done
    # configure mTLS strict mode for namespace
    for ns in "${updated_ns_list[@]}"; do
	if [ -f $istio_path/mTLS-strict-$ns.yaml ]; then
            # ingress needs dedicated configuration
	    kubectl apply -n $ns -f $istio_path/mTLS-strict-$ns.yaml
        else
            kubectl apply -n $ns -f $istio_path/mTLS-strict.yaml
        fi
    done

    # apply authorization policies
    authz_policies=""
    for ns in "${updated_ns_list[@]}"; do
        authz_file=$(printf "$istio_path/authz/authz-%s.yaml" "$ns")
        if [ -f $authz_file ]; then
            authz_policies="${authz_policies}${authz_policies:+ }${authz_file}"
        fi

        kubectl label namespace $ns erag-istio-protected=true --overwrite
        kubectl label namespace $ns istio.io/dataplane-mode=ambient --overwrite
    done
    kubectl apply $(printf " -f %s" $authz_policies)
fi

if $test_flag; then
    print_header "Test connection"
    test_args=""
    if $mesh_flag; then
        test_args="--mesh --istio-path $istio_path"
    fi
    bash scripts/test_connection.sh $test_args
fi

if $clear_auth_flag; then
    clear_ingress
    clear_gateway
    clear_authentication
fi

if $clear_deployment_flag; then
    clear_deployment
    clear_fingerprint
fi

if $clear_ui_flag; then
    clear_ui
fi

if $clear_edp_flag; then
    clear_edp
fi

if $clear_mesh_flag; then
    clear_mesh
fi

if $clear_telemetry_flag; then
    clear_telemetry
fi

if $clear_fingerprint_flag; then
    clear_fingerprint
fi

if $clear_all_flag; then
    # disable strict mode and authorization policies first to avoid cleanup lock-up
    kubectl delete --ignore-not-found $(printf " -f %s" $(ls $istio_path/authz/authz-*))
    for ns in $(kubectl get peerauthentication -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"\n"}{end}'); do
      if [ -f $istio_path/mTLS-strict-$ns.yaml ]; then
        kubectl delete --ignore-not-found -n $ns -f $istio_path/mTLS-strict-$ns.yaml
      else
        kubectl delete --ignore-not-found -n $ns -f $istio_path/mTLS-strict.yaml
      fi
    done
    clear_deployment
    clear_fingerprint
    clear_edp
    clear_authentication
    clear_ui
    clear_telemetry
    clear_ingress
    clear_fingerprint
    clear_gateway
    clear_mesh
    clear_all_ns
    rm -f default_credentials.txt
    rm -f tls.crt tls.key
fi
