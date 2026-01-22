#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

REGISTRY_NAME=localhost:5000
REGISTRY_PATH=erag
TAG=latest
IMAGE_PREFIX="erag-"
_max_parallel_jobs=4

components_to_build=()
failed_components=()
successful_components=()

repo_path=$(realpath "$(pwd)/../")
images_yaml="$repo_path/deployment/images.yaml"
logs_dir="$repo_path/deployment/logs"
mkdir -p $logs_dir

summary_log="$logs_dir/build_summary_$(date +%Y%m%d_%H%M%S).log"
touch "$summary_log"

log_info() {
    local message="[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$message"
    echo "$message" >> "$summary_log"
}

log_error() {
    local message="[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$message" >&2
    echo "$message" >> "$summary_log"
}

log_success() {
    local message="[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$message"
    echo "$message" >> "$summary_log"
}

log_warning() {
    local message="[WARNING] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$message"
    echo "$message" >> "$summary_log"
}

if ! command -v yq &> /dev/null; then
    log_error "'yq' is not installed."
    echo "Please install yq using one of the following commands:"
    echo -e "\tsudo apt install yq\t\t# Ubuntu"
    echo -e "\tpip install yq     \t\t# python version"
    exit 1
fi

if [ ! -f "$images_yaml" ]; then
    log_error "images.yaml not found at $images_yaml"
    echo "Please check out it from the repository."
    exit 1
fi

default_components=($(yq -r '.images | keys | .[]' "$images_yaml"))

# only owner - read, write, and execute
chmod 700 $logs_dir

use_proxy=""
no_cache=""

[ -n "$https_proxy" ] && use_proxy+="--build-arg https_proxy=$https_proxy "
[ -n "$http_proxy" ] && use_proxy+="--build-arg http_proxy=$http_proxy "
[ -n "$no_proxy" ] && use_proxy+="--build-arg no_proxy=$no_proxy "

usage() {
    echo -e "Usage: $0 [OPTIONS] [COMPONENTS...]"
    echo -e "Options:"
    echo -e "\t--build: Build specified components."
    echo -e "\t-j|--jobs <N>: max number of parallel builds (default is $_max_parallel_jobs)."
    echo -e "\t--push: Push specified components to the registry."
    echo -e "\t--setup-registry: Setup local registry at port 5000."
    echo -e "\t--registry: Specify the registry (default is $REGISTRY_NAME)."
    echo -e "\t--tag: Specify the tag version (default is latest)."
    echo -e "\t--use-alternate-tagging: Enable repo:component_tag tagging format instead of the default (repo/component:tag)."
    echo -e "\t\tCan be useful for using a single Docker repository to store multiple images."
    echo -e "\t\tExample: repo/erag:gmcrouter_1.2 instead of repo/erag/gmcrouter:1.2."
    echo -e "\t--hpu: Build components for HPU platform."
    echo -e "\t--no-cache: Build images without using docker cache."
    echo -e "\t--registry-path: Specify the registry path (default is $REGISTRY_PATH)."
    echo -e "Components available (default is all):"
    echo -e "\t ${default_components[*]}"
    echo -e "Example: $0 --build --push --registry my-registry embedding-usvc reranking-usvc"
}

setup_local_registry() {
    LOCAL_REGISTRY_NAME=local-registry
    REGISTRY_PORT=5000
    REGISTRY_IMAGE=registry:2
    REGISTRY_NAME=localhost:$REGISTRY_PORT

    log_info "Setting up local registry..."

    # Check if the local registry container is already there
    if [ "$(docker ps -a -q -f name="$LOCAL_REGISTRY_NAME")" ]; then
        log_warning "$LOCAL_REGISTRY_NAME is already taken. Existing registry will be used."
    else
        log_info "Starting $LOCAL_REGISTRY_NAME..."
        docker run -d -p $REGISTRY_PORT:$REGISTRY_PORT --name $LOCAL_REGISTRY_NAME $REGISTRY_IMAGE
        if [ $? -eq 0 ]; then
            log_success "Local registry started successfully"
        else
            log_error "Failed to start local registry"
        fi
    fi
}

tag_and_push() {
    if [[ "$do_push_flag" == false ]]; then
        log_info "Skipping push for $3 (push flag disabled)"
        return 0
    fi

    local registry_url=$1
    local repo_name=$2
    local image=$3

    local full_image_name
    if $use_alternate_tagging; then
        full_image_name="${repo_name}:${image}_${TAG}"
    else
        full_image_name="${repo_name}/${image}:${TAG}"
    fi

    log_info "Starting push for $full_image_name"

    if [[ "$registry_url" == *"aws"* ]]; then
        if ! aws ecr describe-repositories --repository-names "$repo_name" > /dev/null 2>&1; then
            log_info "Creating ECR repository $repo_name"
            aws ecr create-repository \
                --repository-name "${repo_name}" > /dev/null 2>&1
        fi
    fi

    log_info "Tagging image: docker tag ${full_image_name} ${registry_url}/${full_image_name}"
    docker tag "${full_image_name}" "${registry_url}/${full_image_name}"

    log_info "Pushing image: ${registry_url}/${full_image_name}"
    docker push "${registry_url}/${full_image_name}" &> ${logs_dir}/push_$(basename ${full_image_name}).log

    if [ $? -eq 0 ]; then
        log_success "$full_image_name pushed successfully"
        return 0
    else
        log_error "Push failed for $full_image_name. Check logs at ${logs_dir}/push_$(basename ${full_image_name}).log"
        return 1
    fi
}

docker_login_aws() {
    local region=""
    local aws_account_id=""

    log_info "Attempting AWS ECR login..."

    region=$(aws configure get region)
    aws_account_id=$(aws sts get-caller-identity --query "Account" --output text)

    if [ -z "$region" ] || [ -z "$aws_account_id" ]; then
        log_error "AWS region or account ID could not be determined."
        echo "Please login to aws to be able to pull or push images"
        exit 1
    fi

    local ecr_registry_url="${aws_account_id}.dkr.ecr.${region}.amazonaws.com"
    local ecr_password=""
    ecr_password=$(aws ecr get-login-password --region "$region")

    echo "${ecr_password}" | \
    docker login --username AWS --password-stdin "${ecr_registry_url}" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        log_success "AWS ECR login successful"
    else
        log_error "AWS ECR login failed"
    fi

    echo "${ecr_registry_url}"
}

build_component() {
    if [[ "$do_build_flag" == false ]]; then
        log_info "Skipping build for $4 (build flag disabled)"
        return 0
    fi

    local component_path=$1
    local dockerfile_path=${2#$component_path/}
    local repo_name=$3
    local image=$4
    local build_args=${5:-""}

    local full_image_name
    if $use_alternate_tagging; then
        full_image_name="${repo_name}:${image}_${TAG}"
    else
        full_image_name="${repo_name}/${image}:${TAG}"
    fi

    log_info "Starting build for $full_image_name"
    log_info "Build context: ${repo_path}/${component_path}"
    log_info "Dockerfile: ${dockerfile_path}"

    cd "${repo_path}/${component_path}"
    docker build -t ${full_image_name} ${use_proxy} -f ${dockerfile_path} . ${build_args} ${no_cache} --progress=plain &> ${logs_dir}/build_$(basename ${full_image_name}).log

    if [ $? -eq 0 ]; then
        log_success "$full_image_name built successfully"
        return 0
    else
        log_error "Build failed for $full_image_name. Check logs at ${logs_dir}/build_$(basename ${full_image_name}).log"
        return 1
    fi
}

get_content() {
    local component="$1"
    local field="$2"
    local value

    value=$(yq -r '.images["'"$component"'"].'"$field" "$images_yaml" 2>/dev/null)
    [[ "$value" == "null" ]] && value=""

    echo "$value"
}

do_build_flag=false
do_push_flag=false
setup_registry_flag=false
if_gaudi_flag=false
use_alternate_tagging=false

while [ $# -gt 0 ]; do
    case "$1" in
        --build)
            do_build_flag=true
            ;;
        --push)
            do_push_flag=true
            ;;
        --setup-registry)
            setup_registry_flag=true
            ;;
        --registry)
            shift
            REGISTRY_NAME=${1}
            ;;
        --tag)
            shift
            TAG=${1}
            ;;
        --use-alternate-tagging)
            use_alternate_tagging=true
            ;;
        -j|--jobs)
            shift
            if { [ -n "$1" ] && [ "$1" -eq "$1" ] ; } &> /dev/null; then
                _max_parallel_jobs=${1}
            else
                log_warning "The input '${1}' is not a valid number. Setting number of max parallel jobs to the default value of ${_max_parallel_jobs}."
            fi
            ;;
        --hpu)
            if_gaudi_flag=true
            ;;
        --no-cache)
            no_cache="--no-cache"
            ;;
        --registry-path)
            shift
            REGISTRY_PATH=${1}
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            # Check if $1 is in default_components
            if [[ " ${default_components[*]} " == *" $1 "* ]]; then
                components_to_build+=("$1")
            else
                log_warning "'$1' is not a valid component and it will be ignored. Run '$0 --help' to see available components."
            fi
            ;;
    esac
    shift
done

if [ ${#components_to_build[@]} -eq 0 ]; then
    log_info "No specific components provided, using all default components"
    components_to_build=("${default_components[@]}")
    log_info "Default components to build: ${components_to_build[*]}"
fi

__pcidev=$(grep PCI_ID /sys/bus/pci/devices/*/uevent | grep -i 1da3: || echo "")
if echo $__pcidev | grep -qE '1000|1001|1010|1011|1020|1030|1060'; then
    if_gaudi_flag=true
fi

log_info "=== BUILD CONFIGURATION ==="
log_info "Gaudi flag: $if_gaudi_flag"
log_info "Registry: $REGISTRY_NAME"
log_info "Build enabled: $do_build_flag"
log_info "Push enabled: $do_push_flag"
log_info "Max parallel jobs: $_max_parallel_jobs"
log_info "Tag version: $TAG"
log_info "Registry path: $REGISTRY_PATH"
log_info "Components to build: ${components_to_build[*]}"
log_info "Summary log: $summary_log"

if $setup_registry_flag; then
    setup_local_registry
fi

if [ ${#components_to_build[@]} -eq 0 ]; then
    log_info "No specific components provided, using all default components"
    components_to_build=("${default_components[@]}")
fi

log_info "=== STARTING BUILD PROCESS ==="
log_info "Processing ${#components_to_build[@]} components"

count_current_jobs=0

for component in "${components_to_build[@]}"; do
    if [[ "$if_gaudi_flag" == false && "${component,,}" =~ "gaudi" ]]; then
        log_warning "Skipping '$component' as it is not supported on this platform."
        continue
    fi

    log_info "Processing component: $component"

    (
        component_success=true

        docker_context=$(get_content "$component" "docker_context")
        dockerfile_path=$(get_content "$component" "dockerfile_path")
        image_name=$(get_content "$component" "image_name")

        if [[ -z "$docker_context" || -z "$dockerfile_path" || -z "$image_name" ]]; then
            log_error "Required field is missing for component '$component'. Values:"
            log_error "  docker_context: $docker_context"
            log_error "  dockerfile_path: $dockerfile_path"
            log_error "  image_name: $image_name"
            echo "$component" >> "${logs_dir}/failed_components.tmp"
            exit 1
        fi

        image_name="${IMAGE_PREFIX}${image_name}"

        if $do_build_flag; then
            if ! build_component "${docker_context}" "$dockerfile_path" "$REGISTRY_PATH" "$image_name"; then
                component_success=false
            fi
        fi

        if $do_push_flag && $component_success; then
            if ! tag_and_push "$REGISTRY_NAME" "$REGISTRY_PATH" "$image_name"; then
                component_success=false
            fi
        fi

        if $component_success; then
            echo "$component" >> "${logs_dir}/successful_components.tmp"
            log_success "Component '$component' completed successfully"
        else
            echo "$component" >> "${logs_dir}/failed_components.tmp"
            log_error "Component '$component' failed"
        fi
    ) &

    count_current_jobs=$((count_current_jobs + 1))
    if [ "$count_current_jobs" -ge "$_max_parallel_jobs" ]; then
        wait -n
        count_current_jobs=$((count_current_jobs - 1))
    fi

done

wait

log_info "=== BUILD SUMMARY ==="

if [ -f "${logs_dir}/successful_components.tmp" ]; then
    successful_components=($(cat "${logs_dir}/successful_components.tmp" | sort | uniq))
    log_success "Successfully processed ${#successful_components[@]} components:"
    for comp in "${successful_components[@]}"; do
        log_success "$comp"
    done
    rm -f "${logs_dir}/successful_components.tmp"
else
    log_info "No components were successfully processed"
fi

if [ -f "${logs_dir}/failed_components.tmp" ]; then
    failed_components=($(cat "${logs_dir}/failed_components.tmp" | sort | uniq))
    log_error "Failed to process ${#failed_components[@]} components:"
    for comp in "${failed_components[@]}"; do
        log_error "$comp"
        # Show the most recent error from logs
        if [ -f "${logs_dir}/build_erag-${comp}.log" ]; then
            log_error "    Last error: $(tail -n 3 "${logs_dir}/build_erag-${comp}.log" | head -n 1)"
        fi
    done
    rm -f "${logs_dir}/failed_components.tmp"

    log_error "Build completed with errors. Check individual log files in $logs_dir"
    exit 1
else
    log_success "All components processed successfully!"
fi

log_info "=== DETAILED LOGS ==="
log_info "Summary log: $summary_log"
log_info "Individual logs: $logs_dir/build_*.log"
log_info "Push logs: $logs_dir/push_*.log"
