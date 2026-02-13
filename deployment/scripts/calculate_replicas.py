#!/usr/bin/env python3

import json
import argparse
import sys

def verify_memory_requirements(current_vllm_size, reranking_size, embedding_size, node_memory_size, replicas, edp_enabled, telemetry_enabled, vector_databases_enabled, memory_overcommit_buffer_percent):
    """
    Verify if memory requirements exceed available node memory and adjust replicas if needed.
    
    Args:
        current_vllm_size: Current VLLM CPU size
        reranking_size: Reranking CPU size
        embedding_size: Embedding CPU size
        node_memory_size: Total memory in GiB
        replicas: Number of replicas calculated
        edp_enabled: Boolean flag indicating if EDP is enabled
        telemetry_enabled: Boolean flag indicating if telemetry is enabled
        vector_databases_enabled: Boolean flag indicating if vector databases are enabled
        memory_overcommit_buffer_percent: Memory buffer percentage for pod memory overcommit/burst
        
    Returns:
        Tuple: (verified_replicas_count, memory_usage_percent)
    """

    VLLM_MEMORY = 64 if current_vllm_size > 0 else 0   # [GiB]
    EMBEDDING_MEMORY = 4 if embedding_size > 0 else 0  # [GiB]
    RERANKING_MEMORY = 4 if reranking_size > 0 else 0  # [GiB]

    # Calculate total memory required for initial number of inference group replicas
    inference_memory_sum = VLLM_MEMORY + EMBEDDING_MEMORY + RERANKING_MEMORY

    # Guard against zero division
    if inference_memory_sum == 0:
        return 0, 0.0

    total_memory_needed = inference_memory_sum * replicas

    # Set RAG core services memory request
    CORE_SERVICES_MEMORY = 32  # [GiB]

    # Calculate OPTIONAL_SERVICES_MEMORY based on enabled components
    OPTIONAL_SERVICES_MEMORY = 0
    if edp_enabled:
        OPTIONAL_SERVICES_MEMORY += 17  # memory request for EDP [GiB]
    if vector_databases_enabled:
        OPTIONAL_SERVICES_MEMORY += 13  # memory request for redis [GiB]
    if telemetry_enabled:
        OPTIONAL_SERVICES_MEMORY += 13  # memory request for telemetry [GiB]

    # Calculate memory buffer
    MEMORY_BUFFER_PERCENT = 0.1  # 10% buffer for system, OS, safety margin
    MEMORY_BUFFER = node_memory_size * MEMORY_BUFFER_PERCENT

    # Set additional memory buffer for pod memory overcommit/burst
    MEMORY_OVERCOMMIT_BUFFER = node_memory_size * memory_overcommit_buffer_percent

    # Calculate available memory for inference pods
    max_allocatable_memory = node_memory_size - CORE_SERVICES_MEMORY - OPTIONAL_SERVICES_MEMORY - MEMORY_BUFFER - MEMORY_OVERCOMMIT_BUFFER

    # Check if required memory exceeds available
    if total_memory_needed <= max_allocatable_memory:
        memory_usage_percent = (total_memory_needed / node_memory_size) * 100
        return replicas, memory_usage_percent
    else:
        # Reduce replicas to fit max allocatable memory threshold
        verified_replicas_count = int(max_allocatable_memory // inference_memory_sum)
        # Ensure we don't return more replicas than originally calculated
        verified_replicas_count = min(verified_replicas_count, replicas)
        # Ensure we never return negative replicas
        verified_replicas_count = max(0, verified_replicas_count)
        memory_usage_percent = (verified_replicas_count * inference_memory_sum / node_memory_size) * 100
        return verified_replicas_count, memory_usage_percent

def calculate_replicas(nodes_dict, vllm_size, reranking_size, embedding_size, throughput_mode, edp_enabled, telemetry_enabled, vector_databases_enabled, memory_overcommit_buffer_percent, max_replicas_per_node):
    """
    Calculate optimal replica distribution for VLLM, reranking, and embedding services.

    Args:
        nodes_dict: Dict with node names as keys and values containing: numa_nodes, cpus_per_numa_node, gaudi
        vllm_size: CPU requirement for VLLM (will be multiplied by 2)
        reranking_size: CPU requirement for reranking (will be multiplied by 2)
        embedding_size: CPU requirement for embedding (will be multiplied by 2)
        throughput_mode: Boolean flag for throughput optimization.
        edp_enabled: Boolean flag indicating if EDP is enabled
        telemetry_enabled: Boolean flag indicating if telemetry is enabled
        vector_databases_enabled: Boolean flag indicating if vector databases are enabled
        memory_overcommit_buffer_percent: Memory buffer percentage for pod memory overcommit/burst
        max_replicas_per_node: Maximum replicas per node to avoid exceeding pod limits

    Returns:
        Dict with node names as keys and calculations with metadata as values.

    Algorithm:
        - When all services fit in NUMA node (n > 0) and throughput_mode=True: tries to maximize 
          replicas while keeping VLLM >= 75% of original size
        - When all services fit in NUMA node (n > 0) and throughput_mode=False: uses standard 
          calculation (n * numa_nodes_count) without optimization
        - Throughput mode (n == 0, throughput_mode=True): maximizes replicas with VLLM >= 50% 
          of original size
        - Fallback mode (n == 0 and throughput_mode=False, or cannot fit replicas): allocates
          one replica set per 2 NUMA nodes (replicas = numa_nodes_count // 2), with VLLM taking
          full NUMA node size if needed. Returns 0 replicas if VLLM size < 25% of original
    """

    # Multiply parameters directly by 2 (for hyperthreading consideration)
    vllm_size *= 2
    reranking_size *= 2
    embedding_size *= 2

    # Calculate VLLM size thresholds for different optimization modes
    vllm_75_percent = (vllm_size * 3) // 4  # Minimum for throughput optimization when n > 0
    vllm_50_percent = vllm_size // 2  # Minimum for throughput mode when n == 0
    vllm_25_percent = vllm_size // 4  # Minimum for fallback mode

    results = {}
    total_replicas = 0
    gaudi_nodes_count = 0

    for node_name, node_data in nodes_dict.items():
        numa_nodes_count = node_data['numa_nodes']
        numa_node_size = node_data['cpus_per_numa_node']
        node_memory_size = node_data['total_memory_GiB']

        # Initialize VLLM size for this node (may be adjusted based on calculation mode)
        current_vllm_size = vllm_size

        # Test if all services fit together in one NUMA node
        total_size = current_vllm_size + reranking_size + embedding_size

        # Guard against zero division
        if total_size == 0:
            n = 0
        else:
            n = numa_node_size // total_size

        use_fallback = False

        if n > 0:
            # All services fit in one NUMA node
            if throughput_mode:
                # Check if we can fit more replicas while maintaining VLLM at 75% of original size
                inference_cpu_sum = reranking_size + embedding_size + vllm_75_percent
                if inference_cpu_sum == 0:
                    max_possible_replicas_per_numa = 0
                else:
                    max_possible_replicas_per_numa = numa_node_size // inference_cpu_sum

                if max_possible_replicas_per_numa > n:
                    # We can fit more replicas
                    available_cpu_for_vllm = numa_node_size - max_possible_replicas_per_numa * (reranking_size + embedding_size)
                    max_vllm_size_per_replica = available_cpu_for_vllm // max_possible_replicas_per_numa

                    replicas = max_possible_replicas_per_numa * numa_nodes_count
                    current_vllm_size = max_vllm_size_per_replica
                else:
                    replicas = n * numa_nodes_count
            else:
                replicas = n * numa_nodes_count

        elif n == 0 and throughput_mode:
            # Throughput mode: for the maximum possible replicas per NUMA node, find the maximum VLLM size
            # First, calculate the maximum number of replicas that can fit with minimum VLLM requirements
            inference_cpu_sum = reranking_size + embedding_size + vllm_50_percent
            if inference_cpu_sum == 0:
                max_possible_replicas_per_numa = 0
            else:
                max_possible_replicas_per_numa = numa_node_size // inference_cpu_sum

            if max_possible_replicas_per_numa > 0:
                # Calculate the maximum VLLM size for this replica count
                available_cpu_for_vllm = numa_node_size - max_possible_replicas_per_numa * (reranking_size + embedding_size)
                max_vllm_size_per_replica = available_cpu_for_vllm // max_possible_replicas_per_numa

                replicas = max_possible_replicas_per_numa * numa_nodes_count
                current_vllm_size = max_vllm_size_per_replica
            else:
                use_fallback = True
        else:
            use_fallback = True

        if use_fallback:
            # Fallback mode: allocate one replica set per 2 NUMA nodes
            current_vllm_size = min(current_vllm_size, numa_node_size)
            if current_vllm_size < vllm_25_percent:
                replicas = 0
            else:
                replicas = numa_nodes_count // 2

        # Apply maximum replica limit to prevent exceeding pod limits
        replicas = min(replicas, max_replicas_per_node)

        # Verify memory requirements
        verified_replicas_count, memory_usage_percent = verify_memory_requirements(
            current_vllm_size,
            reranking_size,
            embedding_size,
            node_memory_size,
            replicas,
            edp_enabled,
            telemetry_enabled,
            vector_databases_enabled,
            memory_overcommit_buffer_percent
        )

        # Set per-service replicas to 0 if service has 0 CPU size
        vllm_replicas = verified_replicas_count if current_vllm_size > 0 else 0
        embedding_replicas = verified_replicas_count if embedding_size > 0 else 0
        reranking_replicas = verified_replicas_count if reranking_size > 0 else 0

        results[node_name] = {
            'replicas': verified_replicas_count,
            'adjusted_vllm_size': current_vllm_size // 2,
            'calculation_method': _get_calculation_method(n, numa_node_size, vllm_size, reranking_size, embedding_size, throughput_mode),
            'gaudi': node_data.get('gaudi', False),
            'amx_supported': node_data.get('amx_supported', False),
            'memory_usage_percent': round(memory_usage_percent, 2),
            'vllm': {
                'replicas': vllm_replicas,
                'adjusted_cpu_size': current_vllm_size // 2
            },
            'embedding': {
                'replicas': embedding_replicas,
                'cpu_size': embedding_size // 2
            },
            'torchserve_reranking': {
                'replicas': reranking_replicas,
                'cpu_size': reranking_size // 2
            }
        }

        # Sum replicas only for nodes with amx_supported which are not Gaudi nodes
        if node_data.get('amx_supported', False) and not node_data.get('gaudi', False):
            total_replicas += verified_replicas_count
        # Count Gaudi nodes
        if node_data.get('gaudi', False):
            gaudi_nodes_count += 1

    results['total_replicas'] = total_replicas
    results['gaudi_nodes_count'] = gaudi_nodes_count
    return results

def _get_calculation_method(n, numa_node_size, vllm_size, reranking_size, embedding_size, throughput_mode):
    """Helper function to identify which calculation method was used."""
    if n > 0:
        return "all_services_fit"
    elif n == 0 and throughput_mode:
        return "throughput_mode_adjustment"
    else:
        return "fallback_mode"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate optimal replicas for services')
    parser.add_argument('--nodes-dict', type=str, required=True, help='JSON string of nodes topology')
    parser.add_argument('--vllm-size', type=int, required=True, help='VLLM CPU size')
    parser.add_argument('--reranking-size', type=int, required=True, help='Reranking CPU size')
    parser.add_argument('--embedding-size', type=int, required=True, help='Embedding CPU size')
    parser.add_argument('--throughput-mode', type=lambda x: x.lower() == 'true', required=True, help='Enable throughput mode')
    parser.add_argument('--edp-enabled', type=lambda x: x.lower() == 'true', required=True, help='EDP enabled flag')
    parser.add_argument('--telemetry-enabled', type=lambda x: x.lower() == 'true', required=True, help='Telemetry enabled flag')
    parser.add_argument('--vector-databases-enabled', type=lambda x: x.lower() == 'true', required=True, help='Vector databases enabled flag')
    parser.add_argument('--memory-overcommit-buffer-percent', type=float, default=0.1, help='Memory buffer percentage for pod memory overcommit/burst (default: 0.1)')
    parser.add_argument('--max-replicas-per-node', type=int, default=10, help='Maximum replicas per node to avoid exceeding pod limits (default: 10)')

    args = parser.parse_args()

    nodes_dict = json.loads(args.nodes_dict)

    results = calculate_replicas(
        nodes_dict,
        args.vllm_size,
        args.reranking_size,
        args.embedding_size,
        args.throughput_mode,
        args.edp_enabled,
        args.telemetry_enabled,
        args.vector_databases_enabled,
        args.memory_overcommit_buffer_percent,
        args.max_replicas_per_node
    )
    sys.stdout.write(json.dumps(results))
