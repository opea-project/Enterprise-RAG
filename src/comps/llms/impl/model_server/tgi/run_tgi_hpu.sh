#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# todo: consolide run_tgi_cpu.sh and run_tgi_hpu.sh into one script, add 'device' argument to specify cpu or hpu

# Set default values
LLM_TGI_PORT=8009
LLM_TGI_MODEL_NAME="Intel/neural-chat-7b-v3-3"

volume=$PWD/data

hpu_num_cards=1


# Check if 'habana' runtime exists
if ! docker info | grep -q 'Runtimes:.*habana'; then
    echo "Error: 'habana' runtime is not available."
    exit 1
fi

# TODO: confirm what is the way of executing te script is desired - if we want to provide arguments or prefer base on env variables or variables defined in the script
# Check if all required arguments are provided
# if [ "$#" -lt 0 ] || [ "$#" -gt 3 ]; then
#     echo "Usage: $0 [num_cards] [port_number] [model_name]"
#     exit 1
# fi

# Assign arguments to variables
# num_cards=${1:-$default_num_cards}
# port_number=${2:-$default_port}
# model_name=${3:-$default_model}

# Check if num_cards is within the valid range (1-8)
if [ "$hpu_num_cards" -lt 1 ] || [ "$hpu_num_cards" -gt 8 ]; then
    echo "Error: num_cards must be between 1 and 8."
    exit 1
fi

# Set the volume variable
volume=$PWD/data

# Build the Docker run command based on the number of cards
if [ "$hpu_num_cards" -eq 1 ]; then
    docker_cmd="
    docker run -it --name='llm-tgi-cpu' -p $LLM_TGI_PORT:80 -v $volume:/data \
    --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
    --cap-add=sys_nice --ipc=host 
    -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy ghcr.io/huggingface/tgi-gaudi:latest 
    --model-id $model_name --max-input-tokens 1024 --max-total-tokens 2048"
else
    docker_cmd="
    docker run -it --name='llm-tgi-cpu' -p $LLM_TGI_PORT:80 -v $volume:/data 
    --runtime=habana -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true 
    -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none 
    --cap-add=sys_nice --ipc=host -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy ghcr.io/huggingface/tgi-gaudi:latest 
    --model-id $model_name --sharded true --num-shard $hpu_num_cards"
fi

# Execute the Docker run command
eval $docker_cmd
