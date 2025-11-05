#!/usr/bin/env python3

import json
import argparse
import sys

def calculate_replicas(nodes_dict, vllm_size, reranking_size, embedding_size, throughput_mode):
    """
    Calculate optimal replica distribution for VLLM, reranking, and embedding services.

    Args:
        nodes_dict: Dict with node names as keys and values containing: numa_nodes, cpus_per_numa_node, gaudi
        vllm_size: CPU requirement for VLLM (will be multiplied by 2)
        reranking_size: CPU requirement for reranking (will be multiplied by 2)
        embedding_size: CPU requirement for embedding (will be multiplied by 2)
        throughput_mode: Boolean flag for throughput optimization.

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

        # Initialize VLLM size for this node (may be adjusted based on calculation mode)
        current_vllm_size = vllm_size

        # Test if all services fit together in one NUMA node
        total_size = current_vllm_size + reranking_size + embedding_size
        n = numa_node_size // total_size
        use_fallback = False

        if n > 0:
            # All services fit in one NUMA node
            if throughput_mode:
                # Check if we can fit more replicas while maintaining VLLM at 75% of original size
                max_possible_replicas_per_numa = numa_node_size // (reranking_size + embedding_size + vllm_75_percent)
                
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
            max_possible_replicas_per_numa = numa_node_size // (reranking_size + embedding_size + vllm_50_percent)

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
            # Used when: (n == 0 and throughput_mode is False) OR (throughput mode cannot fit replicas)
            current_vllm_size = min(current_vllm_size, numa_node_size)
            # Check if VLLM size meets minimum requirement (25% of original)
            if current_vllm_size < vllm_25_percent:
                replicas = 0
            else:
                replicas = numa_nodes_count // 2

        results[node_name] = {
            'replicas': replicas,
            'adjusted_vllm_size': current_vllm_size // 2,
            'calculation_method': _get_calculation_method(n, numa_node_size, vllm_size, reranking_size, embedding_size, throughput_mode),
            'gaudi': node_data.get('gaudi', False),
            'amx_supported': node_data.get('amx_supported', False),
            'vllm': {
                'replicas': replicas,
                'adjusted_cpu_size': current_vllm_size // 2
            },
            'torchserve_embedding': {
                'replicas': replicas,
                'cpu_size': embedding_size // 2
            },
            'torchserve_reranking': {
                'replicas': replicas,
                'cpu_size': reranking_size // 2
            }
        }

        # Sum replicas only for nodes with amx_supported which are not Gaudi nodes
        if node_data.get('amx_supported', False) and not node_data.get('gaudi', False):
            total_replicas += replicas
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

    args = parser.parse_args()

    nodes_dict = json.loads(args.nodes_dict)

    results = calculate_replicas(
        nodes_dict,
        args.vllm_size,
        args.reranking_size,
        args.embedding_size,
        args.throughput_mode
    )
    sys.stdout.write(json.dumps(results))
