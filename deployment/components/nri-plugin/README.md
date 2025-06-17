# vLLM CPUs Allocation Based on Balloons Policy and System Topology

> ℹ️ **Info:**  
> This is **preview** feature and intended only for Intel Xeon platforms. It is not supported on Gaudi, multi-node cluster or non-NUMA architectures.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Configuration Example](#configuration-example)
- [Calculating maxBalloons](#calculating-maxballoons)
- [Limitations](#limitations)
- [Reset Balloons Policy Manually](#reset-balloons-policy-manually)

## Overview

This feature enables optimal vLLM pod distribution across NUMA nodes by assigning resources based on the system's CPU topology, specifically targeting Intel Xeon platforms.

## Key Features

- Automatic detection of NUMA topology (number and size of NUMA nodes) at runtime; no manual configuration required.
- Spread vLLM pods equally between each NUMA node, balancing placement according to the system topology.
- Keep each vLLM pod isolated to a single NUMA node, and avoid spanning across nodes.
- Allocate 32 CPUs per vLLM pod; the sibling (hyperthreads) of those CPUs are available for non-vLLM workloads.
- Supports dynamic scaling with Horizontal Pod Autoscaler (HPA).  
  **Note:** When `balloons.enabled` is set, the `maxReplicas` value in HPA is automatically set to the calculated `maxBalloons` value (see [Calculating maxBalloons](#calculating-maxballoons)).
- **Currently supported only on single-node Kubernetes clusters.**

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

The maximum number of vLLM pods ("balloons") that can run concurrently is determined by the available NUMA nodes and CPU requirements:

- Each vLLM pod reserves 32 CPUs, and also blocks the corresponding 32 hyperthreads (sibling threads) from use by other vLLM pods. Effectively, each vLLM pod "reserves" 64 CPUs (from the perspective of other vLLM pods).
- The number of vLLM pods that can be placed per NUMA node is calculated as:  
  `max vLLM per NUMA node = NUMANodeSize // 64`
- Therefore,  
  `maxBalloons = NUMANodes * (NUMANodeSize // 64)`

Here, the `//` operator means integer (floor) division, i.e., the result is rounded down to the nearest whole number. For example, `130 // 64 = 2`.

**Examples:**  

- If your system has 2 NUMA nodes, and each node has 80 CPUs:

  ```
  maxBalloons = 2 * (80 // 64) = 2 * 1 = 2
  ```
  So only one vLLM pod can be scheduled per NUMA node.

- If your system has 2 NUMA nodes, and each node has 128 CPUs:

  ```
  maxBalloons = 2 * (128 // 64) = 2 * 2 = 4
  ```
  So two vLLM pods can be scheduled per NUMA node, four in total.

This allows for multiple vLLM balloons per NUMA node when resources permit.

## Limitations

- **Xeon only:** Unsupported on Gaudi or non-NUMA platforms.
- **Single-node only:** Currently, this feature is designed for single-node Kubernetes clusters.

## Reset Balloons Policy Manually

```sh
helm upgrade --install nri-balloons nri-plugins/nri-resource-policy-balloons \
  -n kube-system \
  -f deployment/components/nri-plugin/reset-values.yaml
```
