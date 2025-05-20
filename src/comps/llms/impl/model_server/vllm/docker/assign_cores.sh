#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

echo "trying to bind VLLM pod to physical cores - verifying env"

if [ -z "$VLLM_POD_INDEX" ]; then
	echo "VLLM_POD_INDEX not set, quitting"
	return 1
fi

if [ -z "$OMP_NUM_THREADS" ]; then
	echo "OMP_NUM_THREADS not set, quitting"
	return 1
fi

if [ "$VLLM_TP_SIZE" -ne 1 ]; then
	echo "VLLM_TP_SIZE not equal to 1, qutting"
	return 1
fi

if [ "$VLLM_TP_SIZE" -ne 1 ]; then
	echo "VLLM_PP_SIZE not equal to 1, qutting"
	return 1
fi

numa_cnt=$(lscpu | grep "NUMA node(s)" | awk '{print $3}')
pod_idx=$(($VLLM_POD_INDEX % $numa_cnt))
to_skip=$(($VLLM_POD_INDEX / $numa_cnt * $OMP_NUM_THREADS))
# This code ensures that we are evenly distributing the pods between:
# a) sockets
# b) numa nodes within socket (for SNC systems)
target_numa=$(while IFS=',' read -r main_index abs_index; do
    if [[ "$main_index" == "$previous_main_index" ]]; then
        ((relative_index++))
    else
        relative_index=0
    fi
    echo "$main_index,$abs_index,$relative_index"
    previous_main_index="$main_index"
done < <(lscpu -p=Socket,Node | grep -v '^#' | sort | uniq) | sort -t ',' -k 3 -r | cut -d ',' -f2 | head -n $(($pod_idx + 1)) | tail -n 1)

echo "trying to bind VLLM pod to $OMP_NUM_THREADS physical cores on NUMA node $target_numa"

cpu_list=()
while IFS=',' read -r cpu core node; do
	if [ "$cpu" -eq "$core" ] && [ "$node" == "$target_numa" ]; then
		if [ "$to_skip" -eq 0 ]; then
			cpu_list+=("$cpu")
		else
			to_skip=$(($to_skip - 1))
		fi
	fi
	if [ ${#cpu_list[@]} -eq "$OMP_NUM_THREADS" ]; then
		break
	fi
done < <(lscpu -p=CPU,CORE,NODE | grep -v '^#')

if [ ${#cpu_list[@]} -ne "$OMP_NUM_THREADS" ]; then
	echo "not enough physical cores on selected NUMA node"
	return 1
fi

export VLLM_CPU_OMP_THREADS_BIND=$(echo "${cpu_list[*]}" | sed 's/ /,/g')

echo "binding VLLM pod to cores: $VLLM_CPU_OMP_THREADS_BIND"
