#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

DEFAULT_REGISTRY=localhost:5000
REGISTRY_NAME=${DEFAULT_REGISTRY}
TAG=latest

components_to_build=()

default_components=("gmcManager" "dataprep-usvc" "embedding-usvc" "reranking-usvc" "torchserve" "retriever-usvc" "ingestion-usvc" "llm-usvc" "in-guard-usvc" "out-guard-usvc" "ui-usvc" "otelcol-contrib-journalctl" "fingerprint-usvc")

repo_path=$(realpath "$(pwd)/../")

use_proxy=""

[ -n "$https_proxy" ] && use_proxy+="--build-arg https_proxy=$https_proxy "
[ -n "$http_proxy" ] && use_proxy+="--build-arg http_proxy=$http_proxy "
[ -n "$no_proxy" ] && use_proxy+="--build-arg no_proxy=$no_proxy "

usage() {
    echo -e "Usage: $0 [OPTIONS] [COMPONENTS...]"
    echo -e "Options:"
    echo -e "\t--build: Build specified components."
    echo -e "\t--push: Push specified components to the registry."
    echo -e "\t--setup-registry: Setup local registry at port 5000."
    echo -e "\t--registry: Specify the registry (default is $DEFAULT_REGISTRY)."
    echo -e "\t--tag: Specify the tag (default is latest)."
    echo -e "Components available (default is all):"
    echo -e "\t ${default_components[*]}"
    echo -e "Example: $0 --build --push --registry my-registry embedding-usvc reranking-usvc"
}

# !TODO verify existing stuff at p5000
setup_local_registry() {
    LOCAL_REGISTRY_NAME=local-registry
    REGISTRY_PORT=5000
    REGISTRY_IMAGE=registry:2
    REGISTRY_NAME=localhost:$REGISTRY_PORT

    # Check if the local registry container is already there
    if [ "$(docker ps -a -q -f name="$LOCAL_REGISTRY_NAME")" ]; then
        echo "Warning! $LOCAL_REGISTRY_NAME is already taken. Existing registry will be used."
    else 
        echo "Starting $LOCAL_REGISTRY_NAME..."
        docker run -d -p $REGISTRY_PORT:$REGISTRY_PORT --name $LOCAL_REGISTRY_NAME $REGISTRY_IMAGE
    fi
}

tag_and_push() {
    if [[ "$do_push_flag" == false ]]; then
        echo "skip pushing $*"
        return
    fi

    local registry_url=$1
    local image_name=$2
    local image_tag=$3

    local full_image_name="${image_name}:${image_tag}"

    if [[ "$registry_url" == *"aws"* ]]; then
        if ! aws ecr describe-repositories --repository-names "$image_name" > /dev/null 2>&1; then
            aws ecr create-repository \
                --repository-name "${image_name}" > /dev/null 2>&1
        fi
    fi

    docker tag "${full_image_name}" "${registry_url}/${full_image_name}"
    docker push "${registry_url}/${full_image_name}"

    helm_values_info+="    repository: \"${registry_url}/${image_name}\"\n    tag: \"${image_tag}\"\n"
}

docker_login_aws() {
    local region=""
    local aws_account_id=""

    region=$(aws configure get region)
    aws_account_id=$(aws sts get-caller-identity --query "Account" --output text)

    if [ -z "$region" ] || [ -z "$aws_account_id" ]; then
        echo "Error: AWS region or account ID could not be determined."
        echo "Please login to aws to be able to pull or push images"
        exit 1
    fi

    local ecr_registry_url="${aws_account_id}.dkr.ecr.${region}.amazonaws.com"
    local ecr_password=""
    ecr_password=$(aws ecr get-login-password --region "$region")

    echo "${ecr_password}" | \
    docker login --username AWS --password-stdin "${ecr_registry_url}" > /dev/null 2>&1
    echo "${ecr_registry_url}"
}

build_component() {
    if [[ "$do_build_flag" == false ]]; then
        echo "skip building $*"
        return
    fi

    local component_path=$1
    local dockerfile_path=$2
    local image_name=$3
    local image_tag=$4
    local build_args=${5:-""}

    local full_image_name="${image_name}:${image_tag}"

    cd "${component_path}"

    docker build -t ${full_image_name} ${use_proxy} -f ${dockerfile_path} . ${build_args}
}

do_build_flag=false
do_push_flag=false
setup_registry_flag=false

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
        --help)
            usage
            exit 0
            ;;
        *)
            components_to_build+=("$1")
            ;;
    esac
    shift
done

echo "REGISTRY_NAME = $REGISTRY_NAME"
echo "do_build = $do_build_flag"
echo "do_push = $do_push_flag"
echo "TAG = $TAG"
echo "components_to_build = ${components_to_build[*]}"

if $setup_registry_flag; then
    setup_local_registry
fi

if [ ${#components_to_build[@]} -eq 0 ]; then
    components_to_build=("${default_components[@]}")
fi

for component in "${components_to_build[@]}"; do
    echo "processing the ${component}..."
    case $component in
        gmcManager)
            path="${repo_path}/deployment/microservices-connector"
            if $do_build_flag; then
                cd "$path"
                make docker.build VERSION="$TAG"
            fi

            if $do_push_flag; then
                tag_and_push "$REGISTRY_NAME" opea/gmcmanager "$TAG"
                tag_and_push "$REGISTRY_NAME" opea/gmcrouter "$TAG"
            fi
            ;;

        embedding-usvc)
            path="${repo_path}/src"
            dockerfile="comps/embeddings/impl/microservice/Dockerfile"
            image_name=opea/embedding
            additional_args="--target langchain"

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG "$additional_args";fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        torchserve)
            path="${repo_path}/src/comps/embeddings/impl/model-server/torchserve"
            dockerfile="docker/Dockerfile"
            image_name=opea/torchserve

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        reranking-usvc)
            path="${repo_path}/src"
            dockerfile="comps/reranks/impl/microservice/Dockerfile"
            image_name=opea/reranking

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        dataprep-usvc)
            path="${repo_path}/src"
            dockerfile="comps/dataprep/impl/microservice/Dockerfile"
            image_name=opea/dataprep

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        retriever-usvc)
            path="${repo_path}/src"
            dockerfile="comps/retrievers/impl/microservice/Dockerfile"
            image_name=opea/retriever

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        ingestion-usvc)
            path="${repo_path}/src"
            dockerfile="comps/ingestion/impl/microservice/Dockerfile"
            image_name=opea/ingestion

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        llm-usvc)
            path="${repo_path}/src"
            dockerfile="comps/llms/impl/microservice/Dockerfile"
            image_name=opea/llm

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        in-guard-usvc)
            path="${repo_path}/src"
            dockerfile="comps/guardrails/llm_guard_input_guardrail/impl/microservice/Dockerfile"
            image_name=opea/in-guard

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        out-guard-usvc)
            path="${repo_path}/src"
            dockerfile="comps/guardrails/llm_guard_output_guardrail/impl/microservice/Dockerfile"
            image_name=opea/out-guard

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        ui-usvc)
            path="${repo_path}/src"
            dockerfile="ui/Dockerfile"
            image_name=opea/chatqna-conversation-ui

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

        fingerprint-usvc)
            path="${repo_path}/src"
            dockerfile="comps/system_fingerprint/impl/microservice/Dockerfile"
            image_name=system-fingerprint

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;
 

        otelcol-contrib-journalctl)
            path="${repo_path}"
            dockerfile="deployment/telemetry/helm/charts/logs/Dockerfile-otelcol-contrib-journalctl"
            image_name=otelcol-contrib-journalctl

            if $do_build_flag;then build_component $path $dockerfile $image_name $TAG;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $image_name $TAG;fi
            ;;

    esac
done
