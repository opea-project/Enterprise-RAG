#!/bin/bash
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


# DEFAULT_REGISTRY=ger-is-registry.caas.intel.com/ai-validation
DEFAULT_REGISTRY=aws
REGISTRY_NAME=${DEFAULT_REGISTRY}

do_build=false
do_push=false
components_to_build=()
default_components=("gmcManager" "embedding-usvc" "reranking-usvc" "torcheserve" "retriever-usvc" "llm-uservice" "in-guard")


function help() {
    echo -e "Usage: $0 [OPTIONS] [COMPONENTS...]"
    echo -e "Options:"
    echo -e "\t--build: Build specified components."
    echo -e "\t--push: Push specified components to the registry."
    echo -e "\t--no-build: Don't build specified components. (latest specified will be used)"
    echo -e "\t--no-push: Don't push specified components to the registry. (latest specified will be used)"
    echo -e "\t--registry: Specify the registry (default is $DEFAULT_REGISTRY, use localhost to setup local registry at p5000)."
    echo -e "Components available: (default as all)"
    echo -e "\t ${default_components[@]}"
    echo -e "Example: $0 --build --push --registry my-registry embedding-usvc reranking-usvc"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --build)
            do_build=true
            ;;
        --push)
            do_push=true
            ;;
        --no-build)
            do_build=false
            ;;
        --no-push)
            do_push=false
            ;;
        --registry)
            shift
            REGISTRY_NAME=${1}
            ;;
        --help)
            help
            exit 0
            ;;
        *)
            components_to_build+=("$1")
            ;;
    esac
    shift
done

if [ ${#components_to_build[@]} -eq 0 ]; then
    components_to_build=("${default_components[@]}")
fi

echo "REGISTRY_NAME = $REGISTRY_NAME"
echo "do_build = $do_build"
echo "do_push = $do_push"
echo "components_to_build = ${components_to_build[@]}"


setup_local_registry() {
    LOCAL_REGISTRY_NAME=local-registry
    REGISTRY_PORT=5000
    REGISTRY_IMAGE=registry:2
    REGISTRY_NAME=localhost:$REGISTRY_PORT

    # Check if the local registry container is already running
    if [ $(docker ps -a -q -f name=$LOCAL_REGISTRY_NAME) ]; then
        echo "$LOCAL_REGISTRY_NAME is already running."
    else
        echo "Starting $LOCAL_REGISTRY_NAME..."
        docker run -d -p $REGISTRY_PORT:$REGISTRY_PORT --name $LOCAL_REGISTRY_NAME $REGISTRY_IMAGE
    fi
}


tag_and_push() {
    if [[ "$do_push" == false ]]; then
        echo "skip pushing $@"
        return
    fi

    local registry_url=$1
    local image_name=$2
    local image_tag=$3

    local full_image_name="${image_name}:${image_tag}"

    if [[ "$registry_url" == *".amazonaws.com"* ]]; then
        if ! aws ecr describe-repositories --repository-names "$image_name" > /dev/null 2>&1; then
            aws ecr create-repository \
                --repository-name ${image_name} > /dev/null 2>&1
        fi
    fi

    docker tag ${full_image_name} ${registry_url}/${full_image_name}
    docker push ${registry_url}/${full_image_name}

    helm_values_info+="    repository: \"${registry_url}/${image_name}\"\n    tag: \"${image_tag}\"\n"
}


create_or_replace_secret() {
    local namespace=$1
    local ecr_registry_url=$2
    local ecr_password=$3

    kubectl get namespace $namespace || kubectl create namespace $namespace

    # resetting the k8s secret with the ecr login info
    if kubectl get secret regcred -n ${namespace} > /dev/null 2>&1; then
        kubectl delete secret regcred -n ${namespace}
    fi

    kubectl create secret docker-registry regcred \
      --docker-server="${ecr_registry_url}" \
      --docker-username=AWS \
      --docker-password="${ecr_password}" \
      -n ${namespace}
}


docker_login_aws() {
    local region=$(aws configure get region)
    local aws_account_id=$(aws sts get-caller-identity --query "Account" --output text)

    if [ -z "$region" ] || [ -z "$aws_account_id" ]; then
        echo "Error: AWS region or account ID could not be determined."
        echo "Please login to aws to be able to pull or push images"
        exit 1
    fi

    local ecr_registry_url="${aws_account_id}.dkr.ecr.${region}.amazonaws.com"
    local ecr_password=$(aws ecr get-login-password --region "$region")

    echo "${ecr_password}" | \
    docker login --username AWS --password-stdin "${ecr_registry_url}" > /dev/null 2>&1

    create_or_replace_secret "system" "${ecr_registry_url}" "${ecr_password}" > /dev/null 2>&1;
    create_or_replace_secret "chatqa" "${ecr_registry_url}" "${ecr_password}" > /dev/null 2>&1;

    echo "${ecr_registry_url}"
}


if [[ "$REGISTRY_NAME" == "localhost" ]]; then
    setup_local_registry
elif [[ "$REGISTRY_NAME" == "aws" ]]; then
    REGISTRY_NAME=$(docker_login_aws)
    echo "successfully logged into aws"
fi

repo_path=$(realpath "$(pwd)/../../")

use_proxy=""

[ -n "$https_proxy" ] && use_proxy+="--build-arg https_proxy=$https_proxy "
[ -n "$http_proxy" ] && use_proxy+="--build-arg http_proxy=$http_proxy "
# [ -n "$no_proxy" ] && use_proxy+="--build-arg no_proxy=$no_proxy "


build_component() {
    if [[ "$do_build" == false ]]; then
        echo "skip pushing $@"
        return
    fi

    local component_path=$1
    local dockerfile_path=$2
    local image_name=$3
    local image_tag=$4
    local build_args=${5:-""}

    local full_image_name="${image_name}:${image_tag}"

    cd ${component_path}

    docker build -t ${full_image_name} ${use_proxy} -f ${dockerfile_path} . ${build_args}

    tag_and_push ${REGISTRY_NAME} ${image_name} ${image_tag}
}



for component in "${components_to_build[@]}"; do
    echo "processing the ${component}..."
    if [[ "$do_push" == true ]]; then
        helm_values_info+="  $component:\n"
    fi

    case $component in
        gmcManager)
            if [[ "$do_build" == true ]]; then
                make build
                make docker.build
            fi

            if [[ "$do_push" == true ]]; then
                tag_and_push $REGISTRY_NAME opea/gmcmanager latest
                helm_values_info+="    pullPolicy: Always\n"

                helm_values_info+="  gmcRouter:\n"
                tag_and_push $REGISTRY_NAME opea/gmcrouter latest
            fi
            ;;
        embedding-usvc)
            path="${repo_path}/src"
            dockerfile="comps/embeddings/impl/microservice/Dockerfile"
            image_name=opea/embedding-tei
            image_tag=latest
            additional_args="--target langchain"

            build_component $path $dockerfile $image_name $image_tag "$additional_args"
            ;;

        torcheserve)
            path="${repo_path}/src/comps/embeddings/impl/model-server/torchserve"
            dockerfile="docker/Dockerfile"
            image_name=pl-qna-rag-embedding-torchserve
            image_tag=latest

            build_component $path $dockerfile $image_name $image_tag
            ;;

        reranking-usvc)
            path="${repo_path}/src"
            dockerfile="comps/reranks/impl/microservice/Dockerfile"
            image_name=opea/reranking
            image_name=opea/reranking
            image_tag=latest

            build_component $path $dockerfile $image_name $image_tag
            ;;

        retriever-usvc)
            path="${repo_path}/src"
            dockerfile="comps/retrievers/langchain/redis/docker/Dockerfile"
            image_name=test/retriever-redis
            image_tag=latest

            build_component $path $dockerfile $image_name $image_tag
            ;;

        llm-uservice)
            path="${repo_path}/src"
            dockerfile="comps/llms/impl/microservice/Dockerfile"
            image_name=opea/llm
            image_tag=latest

            build_component $path $dockerfile $image_name $image_tag
            ;;

        in-guard)
            path="${repo_path}/src"
            dockerfile="comps/guardrails/llm_guard_scanners/input_scanner/impl/microservice/Dockerfile"
            image_name=opea/in-guard
            image_tag=latest

            build_component $path $dockerfile $image_name $image_tag
            ;;
    esac
done


if [[ -n "$helm_values_info" ]]; then
    echo
    echo "Using $REGISTRY_NAME"
    echo -e "you can update following images in your helm values.yaml like this:"
    echo
    echo -e "images:"
    echo -e "$helm_values_info"
fi
