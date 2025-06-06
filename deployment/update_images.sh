#!/bin/bash
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

REGISTRY_NAME=localhost:5000
REGISTRY_PATH=erag
TAG=latest
_max_parallel_jobs=4

components_to_build=()

default_components=("gmcManager" "gmcRouter" "dataprep-usvc" "embedding-usvc" "reranking-usvc" "prompt-template-usvc" "torchserve-embedding" "torchserve-reranking" "retriever-usvc" "ingestion-usvc" "llm-usvc" "in-guard-usvc" "out-guard-usvc" "ui-usvc" "otelcol-contrib-journalctl" "fingerprint-usvc" "vllm-gaudi" "vllm-cpu" "langdtct-usvc" "edp-usvc" "dpguard-usvc" "hierarchical-dataprep-usvc")

repo_path=$(realpath "$(pwd)/../")
logs_dir="$repo_path/deployment/logs"
mkdir -p $logs_dir

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
    local repo_name=$2
    local image=$3

    local full_image_name
    if $use_alternate_tagging; then
        full_image_name="${repo_name}:${image}_${TAG}"
    else
        full_image_name="${repo_name}/${image}:${TAG}"
    fi

    if [[ "$registry_url" == *"aws"* ]]; then
        if ! aws ecr describe-repositories --repository-names "$repo_name" > /dev/null 2>&1; then
            aws ecr create-repository \
                --repository-name "${repo_name}" > /dev/null 2>&1
        fi
    fi
    echo docker tag "${full_image_name}" "${registry_url}/${full_image_name}"
    docker tag "${full_image_name}" "${registry_url}/${full_image_name}"
    docker push "${registry_url}/${full_image_name}"  &> ${logs_dir}/push_$(basename ${full_image_name}).log

    if [ $? -eq 0 ]; then
        echo "$full_image_name pushed succesfully"
    else
        echo "Push failed. Please check the logs at ${logs_dir}/push_$(basename ${full_image_name}).log for more details."
        return 1
    fi
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
    local repo_name=$3
    local image=$4
    local build_args=${5:-""}

    local full_image_name
    if $use_alternate_tagging; then
        full_image_name="${repo_name}:${image}_${TAG}"
    else
        full_image_name="${repo_name}/${image}:${TAG}"
    fi

    cd "${component_path}"
    docker build -t ${full_image_name} ${use_proxy} -f ${dockerfile_path} . ${build_args} ${no_cache} --progress=plain &> ${logs_dir}/build_$(basename ${full_image_name}).log

    if [ $? -eq 0 ]; then
        echo "$full_image_name built successfully"
    else
        echo "Build failed. Please check the logs at ${logs_dir}/build_$(basename ${full_image_name}).log for more details."
        return 1
    fi
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
                echo "Warning! The input '${1}' is not a valid number. Setting number of max parallel jobs to the default value of ${_max_parallel_jobs}."
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
            components_to_build+=("$1")
            ;;
    esac
    shift
done

__pcidev=$(grep PCI_ID /sys/bus/pci/devices/*/uevent | grep -i 1da3: || echo "")
if echo $__pcidev | grep -qE '1000|1001|1010|1011|1020|1030|1060'; then
    if_gaudi_flag=true
fi

echo "if_gaudi_flag = $if_gaudi_flag"
echo "REGISTRY_NAME = $REGISTRY_NAME"
echo "do_build = $do_build_flag"
echo "max parallel jobs = $_max_parallel_jobs"
echo "do_push = $do_push_flag"
echo "TAG_VERSION = $TAG"
echo "REGISTRY_PATH = $REGISTRY_PATH"
echo "components_to_build = ${components_to_build[*]}"

if $setup_registry_flag; then
    setup_local_registry
fi

if [ ${#components_to_build[@]} -eq 0 ]; then
    components_to_build=("${default_components[@]}")
fi

count_current_jobs=0

for component in "${components_to_build[@]}"; do
    echo "processing the ${component}..."
    (
    case $component in
        gmcManager)
            path="${repo_path}/deployment/components/gmc/microservices-connector"
            dockerfile="manager/Dockerfile"
            image=erag-gmcmanager

            if $do_build_flag; then build_component $path $dockerfile $REGISTRY_PATH $image; fi
            if $do_push_flag; then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image; fi
            ;;

        gmcRouter)
            path="${repo_path}/deployment/components/gmc/microservices-connector"
            dockerfile="router/Dockerfile"
            image=erag-gmcrouter

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        embedding-usvc)
            path="${repo_path}/src"
            dockerfile="comps/embeddings/impl/microservice/Dockerfile"
            image=erag-embedding

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        torchserve-embedding)
            path="${repo_path}/src/comps/embeddings/impl/model-server/torchserve"
            dockerfile="docker/Dockerfile"
            image=erag-torchserve_embedding

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        torchserve-reranking)
            path="${repo_path}/src/comps/reranks/impl/model_server/torchserve"
            dockerfile="docker/Dockerfile"
            image=erag-torchserve_reranking

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;


        reranking-usvc)
            path="${repo_path}/src"
            dockerfile="comps/reranks/impl/microservice/Dockerfile"
            image=erag-reranking

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        prompt-template-usvc)
            path="${repo_path}/src"
            dockerfile="comps/prompt_template/impl/microservice/Dockerfile"
            image=erag-prompt_template

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        dataprep-usvc)
            path="${repo_path}/src"
            dockerfile="comps/dataprep/impl/microservice/Dockerfile"
            image=erag-dataprep

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;
        
        hierarchical-dataprep-usvc)
            path="${repo_path}/src"
            dockerfile="comps/hierarchical_dataprep/impl/microservice/Dockerfile"
            image=hierarchical_dataprep

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        retriever-usvc)
            path="${repo_path}/src"
            dockerfile="comps/retrievers/impl/microservice/Dockerfile"
            image=erag-retriever

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        ingestion-usvc)
            path="${repo_path}/src"
            dockerfile="comps/ingestion/impl/microservice/Dockerfile"
            image=erag-ingestion

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        llm-usvc)
            path="${repo_path}/src"
            dockerfile="comps/llms/impl/microservice/Dockerfile"
            image=erag-llm

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        in-guard-usvc)
            path="${repo_path}/src"
            dockerfile="comps/guardrails/llm_guard_input_guardrail/impl/microservice/Dockerfile"
            image=erag-in-guard

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        out-guard-usvc)
            path="${repo_path}/src"
            dockerfile="comps/guardrails/llm_guard_output_guardrail/impl/microservice/Dockerfile"
            image=erag-out-guard

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        dpguard-usvc)
            path="${repo_path}/src"
            dockerfile="comps/guardrails/llm_guard_dataprep_guardrail/impl/microservice/Dockerfile"
            image=erag-dpguard

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        ui-usvc)
            path="${repo_path}/src"
            dockerfile="ui/Dockerfile"
            image=erag-chatqna-conversation-ui

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        fingerprint-usvc)
            path="${repo_path}/src"
            dockerfile="comps/system_fingerprint/impl/microservice/Dockerfile"
            image=erag-system-fingerprint

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;
 
        otelcol-contrib-journalctl)
            path="${repo_path}"
            dockerfile="deployment/components/telemetry/helm/charts/logs/Dockerfile-otelcol-contrib-journalctl"
            image=erag-otelcol-contrib-journalctl

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        vllm-gaudi)
            path="${repo_path}/src/comps/llms/impl/model_server/vllm"
            dockerfile="docker/Dockerfile.hpu"
            image=erag-vllm-gaudi

            if $if_gaudi_flag;then
                if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
                if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            else
                echo "Skipping $component as it is not supported on this platform"
            fi
            ;;

        vllm-cpu)
            path="${repo_path}/src/comps/llms/impl/model_server/vllm"
            dockerfile="docker/Dockerfile.cpu"
            image=erag-vllm-cpu

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        langdtct-usvc)
            path="${repo_path}/src"
            dockerfile="comps/language_detection/impl/microservice/Dockerfile"
            image=erag-language-detection

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;

        edp-usvc)
            path="${repo_path}/src"
            dockerfile="edp/Dockerfile"
            image=erag-enhanced-dataprep

            if $do_build_flag;then build_component $path $dockerfile $REGISTRY_PATH $image;fi
            if $do_push_flag;then tag_and_push $REGISTRY_NAME $REGISTRY_PATH $image;fi
            ;;
    esac
    ) &

    count_current_jobs=$((count_current_jobs + 1))
    if [ "$count_current_jobs" -ge "$_max_parallel_jobs" ]; then
        wait -n
        current_jobs=$((current_jobs - 1))
    fi

done

wait
