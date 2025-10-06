# Resources Scheduling and vLLM CPUs Pinning Based on System Topology and Balloons Policy

> ℹ️ **Info:**  
> This is a **preview** feature and is intended for Intel Xeon-only platforms.
It is not supported on Gaudi or non-NUMA architectures.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [vLLM CPU Allocation Adjustment](#vllm-cpus-allocation-adjustment)
- [Node Topology Discovery and Scheduling](#node-topology-discovery-and-scheduling)
- [Configuration Example](#configuration-example)
- [Calculating maxBalloons](#calculating-maxballoons)
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
- Supports dynamic scaling with Horizontal Pod Autoscaler (HPA).  
  **Note:** When `balloons.enabled` is set, the `maxReplicas` value in HPA is automatically set to the calculated `maxBalloons` value (see [Calculating maxBalloons](#calculating-maxballoons)).

## vLLM CPUs Allocation Adjustment

By default, each vLLM pod reserves `32` CPUs (referred to as **`VLLM_CPU_REQUEST`** throughout this document).  
If the NUMA node size is **less than 32 physical CPUs**, **`VLLM_CPU_REQUEST`** must be changed to match the hardware.
This value is configured in the balloons section of your configuration file.

**Example configuration in [`deployment/inventory/sample/config.yaml`](../../inventory/sample/config.yaml):**
```yaml
# Topology-aware resource scheduling and CPU pinning for vLLM
# For detailed documentation, refer to: deployment/components/nri-plugin/README.md
balloons:
  enabled: true
  namespace: kube-system # alternatively, set custom namespace for balloons
  services:
    vllm:
      resources:
        requests:
          cpu: 32
          memory: 64Gi
        limits:
          cpu: 32
          memory: 100Gi
```
**`VLLM_CPU_REQUEST`** should be set to the number of CPUs to allocate per vLLM pod.

**Note:**
If `edp.vllm.enabled` is set to `true`, **`VLLM_CPU_REQUEST`** should also be adjusted in
[`edp values file`](../edp/values.yaml)
under the `vllm.resources` section.

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

The maximum number of vLLM pods ("balloons") that can run concurrently is determined by the available NUMA nodes and CPU requirements **on each k8s node**:

- Each vLLM pod reserves **`VLLM_CPU_REQUEST`** CPUs, and also blocks the corresponding **`VLLM_CPU_REQUEST`** hyperthreads (sibling threads) from use by other vLLM pods. Effectively, each vLLM pod "reserves" **`VLLM_CPU_REQUEST`** × 2 CPUs (from the perspective of other vLLM pods).
- The number of vLLM pods that can be placed per NUMA node is calculated as:  
  `max vLLM per NUMA node = NUMANodeSize // (VLLM_CPU_REQUEST × 2)`
- Therefore,  
  `maxBalloons = NUMANodes * (NUMANodeSize // (VLLM_CPU_REQUEST × 2))`

Here, the `//` operator means integer (floor) division, i.e., the result is rounded down to the nearest whole number. For example, `130 // 64 = 2`.

**Examples:**  
Assume **`VLLM_CPU_REQUEST`** = 32

- If a k8s node has 2 NUMA nodes, and each NUMA node has 80 logical CPUs:

  ```
  maxBalloons = 2 * (80 // 64) = 2 * 1 = 2
  ```
  *Result: Only one vLLM pod can be scheduled per NUMA node, two in total on that k8s node.*

- If a cluster node has 2 NUMA nodes, and each NUMA node has 128 logical CPUs:

  ```
  maxBalloons = 2 * (128 // 64) = 2 * 2 = 4
  ```
  *Result: Two vLLM pods can be scheduled per NUMA node, four in total on that k8s node.*

## Limitations

- **Xeon only:** Unsupported on Gaudi or non-NUMA platforms.
- **Hyperthreading:** Must be enabled on each node.

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
