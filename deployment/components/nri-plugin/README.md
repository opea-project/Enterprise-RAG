# Resources Scheduling and vLLM CPUs Pinning Based on System Topology and Balloons Policy


## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Configuration](#configuration)
  - [Resource Requirements](#resource-requirements)
- [Node Topology Discovery and Scheduling](#node-topology-discovery-and-scheduling)
- [Configuration Example](#configuration-example)
- [Calculating maxBalloons](#calculating-maxballoons)
  - [Calculation Algorithm](#calculation-algorithm)
  - [Configuration Parameters](#configuration-parameters)
  - [Calculation Examples](#calculation-examples)
  - [Preview Topology Calculation](#preview-topology-calculation)
- [Limitations](#limitations)
- [Reset Balloons Policy Manually](#reset-balloons-policy-manually)

## Overview

This feature performs node topology discovery and allocates resources accordingly to enable optimal inference pods distribution across k8s nodes and NUMA nodes within them, specifically targeting Intel Xeon platforms.
It incorporates the use of the [NRI Plugin](https://containers.github.io/nri-plugins/stable/docs/resource-policy/policy/balloons.html) to create "balloons", the isolated resources for containers.

## Key Features

- Node topology discovery and scheduling: Inspects each cluster node to determine CPU layout, NUMA configuration, Xeon generation, and other hardware features, and uses this information to optimize resource allocation.
- Automatic detection of NUMA topology (number and size of NUMA nodes) at runtime for each cluster node; no manual configuration required.
- Spread vLLM pods equally between NUMA nodes, balancing placement according to the system topology on each cluster node.
- Keep each vLLM pod isolated to a single NUMA node, and avoid spanning across NUMA nodes.
- Allocate CPUs for vLLM pod; the sibling CPUs are available for non-vLLM workloads.

## Configuration

The balloons feature is configured in your configuration file (e.g., [`deployment/inventory/sample/config.yaml`](../../inventory/sample/config.yaml)):

```yaml
# Topology-aware resource scheduling and CPU pinning for vLLM
# For detailed documentation, refer to: deployment/components/nri-plugin/README.md
balloons:
  enabled: true
  namespace: kube-system
  throughput_mode: true
  wait_timeout: 300
```
**Configuration Options:**
- **`enabled`**: Set to `true` to activate topology-aware resource scheduling
- **`namespace`**: Kubernetes namespace for the NRI balloons plugin (typically `kube-system`)
- **`throughput_mode`**: Enable throughput optimization to maximize replica count (see [Calculation Algorithm](#calculation-algorithm))
- **`wait_timeout`**: Maximum time in seconds NRI managed pods wait for plugin readiness

### Resource Requirements

CPU and memory resources for vLLM, reranking, and embedding services are **automatically read** from the pipeline's resource configuration file (e.g., `pipelines/chatqa/resources-reference-cpu.yaml`). The system uses these values to calculate optimal pod distribution across NUMA nodes.

**Default CPU allocations:**
- **vLLM**: 32 CPUs per pod (referred to as **`VLLM_CPU_REQUEST`**)
- **Reranking**: 4 CPUs per pod
- **Embedding**: 4 CPUs per pod

To adjust these values, modify the resource configuration in your pipeline's `resources-reference-cpu.yaml` file under the `services` section for each component.

**Note:** If `edp.vllm.enabled` is set to `true`, ensure that vLLM resources are also properly configured in the [`edp values file`](../edp/values.yaml) under the `vllm.resources` section.

## Node Topology Discovery and Scheduling

This feature performs node topology discovery for each node in the cluster to gather the following information:

- `numa_nodes`: Number of NUMA nodes on the k8s node
- `cpus_per_numa_node`: Number of CPUs per NUMA node
- `amx_supported`: Whether AMX is supported (Sapphire Rapids or newer Xeon)
- `numa_balanced`: Whether NUMA nodes are balanced
- `maxBalloons`: Maximum number of vLLM pods ("balloons") for the k8s node
- `gaudi`: Whether the Habana (Gaudi) plugin is present

Based on this information, taints and labels are created on each node to determine eligibility for inference workloads. The following pods will prefer nodes with AMX support during scheduling:
- `vllm`
- `edp-vllm`
- `input-scan`
- `torchserve`
- `tei-rerank`

Additionally, an individual balloons policy is created for each k8s node based on its discovered topology, providing flexible and node-specific resource management in multi-node clusters.

## Configuration Example

Check node topology using:
```shell
lscpu
```

Example output:
```
Architecture:        x86_64
CPU(s):              128
On-line CPU(s) list: 0-127
Thread(s) per core:  2
Core(s) per socket:  32
Socket(s):           2
NUMA node(s):        2
NUMA node0 CPU(s):   0-31,64-95
NUMA node1 CPU(s):   32-63,96-127
```
The plugin will automatically detect:
- Number of NUMA nodes (`NUMANodes`): 2
- Size of each NUMA node (`NUMANodeSize`): 64 CPUs (including hyperthreads)

## Calculating maxBalloons

The system calculates the optimal number of inference pod groups (referred to as **maxBalloons**) using the [`calculate_replicas.py`](../../scripts/calculate_replicas.py) script. This calculation considers not only vLLM pods but also the complete inference service group consisting of vLLM, reranking, and embedding services that work together.

### Calculation Algorithm

The calculation employs a multi-mode algorithm that adapts based on hardware topology and configuration:

**Key Considerations:**
- All CPU values account for hyperthreading by multiplying by 2 (e.g., requesting 32 CPUs reserves 64 logical CPUs)
- Each inference group includes: vLLM, torchserve reranking, and torchserve embedding services
- Services should be isolated within a single NUMA node to avoid cross-NUMA communication overhead

**Calculation Modes:**

The algorithm first checks if all services fit in one NUMA node:
```
n = NUMANodeSize // (VLLM_SIZE × 2 + RERANKER_SIZE × 2 + EMBEDDING_SIZE × 2)
```

**Case 1: Services Fit (`n > 0`)**

When all three services fit together in one NUMA node:

- **With `throughput_mode: false`:**
  - Uses standard calculation: `replicas = n × numa_nodes_count`
  - VLLM maintains original size

- **With `throughput_mode: true`:**
  - Attempts to maximize replicas while maintaining VLLM ≥ 75% of original size
  - Calculates maximum replicas possible, then distributes available CPU to VLLM
  - If optimization doesn't help, uses standard calculation

**Case 2: Services Don't Fit (`n == 0`)**

When services cannot fit together with full VLLM size:

- **With `throughput_mode: false`:**
  - **Fallback Mode:** Allocates one inference group per 2 NUMA nodes
  - Formula: `replicas = numa_nodes_count // 2`
  - VLLM can use up to full NUMA node size if needed
  - Returns 0 replicas if VLLM size falls below 25% of original

- **With `throughput_mode: true`:**
  - **Throughput Adjustment:** Maximizes replicas while keeping VLLM ≥ 50% of original size
  - Calculates maximum possible replicas per NUMA node with reduced VLLM
  - Allocates remaining CPU capacity to VLLM
  - If cannot fit any replicas with 50% of original VLLM size, falls back to Case 2 fallback mode

**Note:** Returns 0 replicas if VLLM size falls below 25% of original in fallback mode. (NUMA node size < 25% of original VLLM size)

### Configuration Parameters

The calculation uses CPU resource requirements from the pipeline configuration:
- **`VLLM_CPU_REQUEST`**: CPUs for vLLM pod
- **`RERANKER_CPU_REQUEST`**: CPUs for reranking pod
- **`EMBEDDING_CPU_REQUEST`**: CPUs for embedding pod
- **`throughput_mode`**: Boolean flag enabling throughput optimization

### Calculation Examples

All examples use default service requirements: **VLLM=32, Reranker=4, Embedding=4** CPUs per pod.

**Example 1: Small NUMA Nodes (Services Don't Fit)**
- **Hardware:** 2 NUMA nodes × 64 logical CPUs each
- **Total required per set:** (32 + 4 + 4) × 2 = 80 logical CPUs (accounting for hyperthreading)
- **Check if services fit:** n = 64 // 80 = 0 (services don't fit in one NUMA node)

  **With `throughput_mode: false` (Fallback Mode):**
  - Fallback: allocate 1 inference group per 2 NUMA nodes
  - Result: `replicas = 2 // 2 = 1` inference group total
  - VLLM size: Can use up to 64 CPUs (full NUMA node if needed)

  **With `throughput_mode: true` (Throughput Mode Adjustment):**
  - Try to fit replicas with reduced VLLM (minimum 50% = 16 CPUs)
  - Required per replica: (16 + 4 + 4) × 2 = 48 logical CPUs
  - Max replicas per NUMA: 64 // 48 = 1
  - Available CPU for VLLM: 64 - 1×(8+8) = 48 logical CPUs → 24 CPUs per VLLM
  - Result: `replicas = 1 × 2 = 2` inference groups, VLLM adjusted to 24 CPUs (75% of original)

**Example 2: Medium NUMA Nodes (Exact Fit)**
- **Hardware:** 2 NUMA nodes × 80 logical CPUs each
- **Total required per set:** (32 + 4 + 4) × 2 = 80 logical CPUs
- **Check if services fit:** n = 80 // 80 = 1 (exactly one complete set fits per NUMA node)

  **With `throughput_mode: false` (Standard Mode):**
  - Result: `replicas = 1 × 2 = 2` inference groups total
  - VLLM size: 32 CPUs (original size maintained)

  **With `throughput_mode: true` (All Services Fit Mode with optimization):**
  - Services fit, but no spare capacity to add more replicas while maintaining VLLM ≥ 75%
  - Result: `replicas = 1 × 2 = 2` inference groups total
  - VLLM size: 32 CPUs (original size maintained)

**Example 3: Large NUMA Nodes (Multiple Sets Fit)**
- **Hardware:** 2 NUMA nodes × 128 logical CPUs each
- **Total required per set:** (32 + 4 + 4) × 2 = 80 logical CPUs
- **Check if services fit:** n = 128 // 80 = 1 (one complete set fits per NUMA node)

  **With `throughput_mode: false` (Standard Mode):**
  - Result: `replicas = 1 × 2 = 2` inference groups total
  - VLLM size: 32 CPUs (original size maintained)
  - Unused capacity: 48 logical CPUs per NUMA node

  **With `throughput_mode: true` (All Services Fit Mode with optimization):**
  - Check if we can fit more replicas while maintaining VLLM ≥ 75% (24 CPUs minimum)
  - Required per replica with VLLM=24: (24 + 4 + 4) × 2 = 64 logical CPUs
  - Max replicas per NUMA: 128 // 64 = 2
  - Available CPU for VLLM: 128 - 2×(8+8) = 96 logical CPUs → 48 CPUs per VLLM (96÷2÷2 = 24)
  - 24 CPUs = 75% of original, so this fits the threshold
  - Result: `replicas = 2 × 2 = 4` inference groups total, VLLM adjusted to 24 CPUs (75% of original)

### Preview Topology Calculation

You can preview the topology calculation results without deploying the infrastructure using the **topology-preview** mode. This dry-run mode:

- Discovers node topology for each cluster node
- Calculates optimal replica distribution
- Displays detailed results per node
- Saves output to `deployment/ansible-logs/tmp/inference_pods_distribution.yaml`
- Does not modify real topology state

**To run topology preview:**

```bash
cd deployment
source erag-venv/bin/activate
ansible-playbook -u $USER -K playbooks/application.yaml \
  --tags topology-preview \
  -e @inventory/sample/config.yaml
```

**Sample Output:**

```
====== Topology Calculation Summary ======
Node: node1
  Inference Groups: 2
  Adjusted VLLM Size: 32
  Calculation Method: all_services_fit
  Gaudi: false
  AMX Supported: true
  VLLM Replicas: 2
  VLLM CPU Size: 32
  Embedding Replicas: 2
  Embedding CPU Size: 4
  Reranking Replicas: 2
  Reranking CPU Size: 4
------------------------------------------
Total Inference Groups: 2
Gaudi Nodes Count: 0
==========================================
```

The output file contains per-node breakdowns showing:
- Number of inference groups (replicas) per node
- Adjusted VLLM CPU size (may differ from original if optimized)
- Calculation method used (`all_services_fit`, `throughput_mode_adjustment`, or `fallback_mode`)
- Hardware features (Gaudi, AMX support)
- Individual service replica counts and CPU allocations

This information helps validate your cluster topology and resource configuration before actual deployment.

## Limitations

- **Hyperthreading:** Must be enabled on each node.
- **Minimum NUMA node size:** Each NUMA node must have at least 16 vCPUs (logical CPUs including hyperthreads) to accommodate the minimum vLLM CPU requirement.

## Reset Balloons Policy Manually

To remove all balloons policies from the cluster, run:
```shell
kubectl delete BalloonsPolicy --all -A
```
Then, overwrite obsolete policies by running:
```sh
helm upgrade --install nri-balloons nri-plugins/nri-resource-policy-balloons \
  -n kube-system \
  -f deployment/components/nri-plugin/reset-values.yaml
```
