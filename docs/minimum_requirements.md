# Minimum Requirements Configuration Guide

This guide describes how to configure Intel® AI for Enterprise RAG for a **minimum hardware setup** (60 CPU logical cores / 128 GB RAM).

> [!NOTE]
> All CPU core counts in this guide refer to **logical cores** (also known as hardware threads or vCPUs), not physical cores.

## Standard Minimum Requirements

| CPU Logical Cores | RAM | Disk |
|---|---|---|
| 60 logical cores | 128 GB | 200 GB |

> [!NOTE]
> A **limited single-user deployment** is also possible with as little as **32 logical cores and 64 GB RAM**.
> This configuration is only suitable for a single concurrent user and requires additional tuning.
> See [Limited Single-User Deployment (32 logical cores / 64 GB)](#limited-single-user-deployment-32-logical-cores--64-gb) below for required config changes.

---

## Quick Start: Use the Minimal Sample Config

For a single-user minimum deployment, use the pre-configured sample as your starting point:

```bash
cp deployment/inventory/sample/config_minimal.yaml deployment/inventory/<your-inventory>/config.yaml
```

[`deployment/inventory/sample/config_minimal.yaml`](../deployment/inventory/sample/config_minimal.yaml) is pre-configured for minimum deployments. It already:

- Disables telemetry traces and log collection
- Disables HPA (`hpaEnabled: false`)
- Disables balloons CPU pinning (`balloons.enabled: false`)
- Sets `minimal_configuration: true` which automatically reduces resource requests across all components and switches the pipeline to `minimal-resources-reference-cpu.yaml` (VLLM limited to 16 CPU cores, 1 replica, 16 GB memory)

> [!IMPORTANT]
> After copying, fill in the required fields in your `config.yaml` before deploying:
> - `kubeconfig` — absolute path to your kubeconfig file (e.g. `/home/user/.kube/config`)
> - `httpProxy` / `httpsProxy` — your HTTP/HTTPS proxy URLs (leave empty if not behind a proxy)
> - `additionalNoProxy` — any extra no-proxy entries for your environment
>
> The only remaining manual step is reducing the VLLM KV cache size — see [KV Cache Size](#kv-cache-size-required-manual-step) below.

---

## KV Cache Size (Required Manual Step)

> [!IMPORTANT]
> You **must** manually reduce the VLLM KV cache size in
> [`deployment/pipelines/chatqa/resources-model-cpu.yaml`](../deployment/pipelines/chatqa/resources-model-cpu.yaml)
> to avoid out-of-memory errors on minimum hardware.

Model definitions and their `VLLM_CPU_KVCACHE_SPACE` settings are in
[`deployment/pipelines/chatqa/resources-model-cpu.yaml`](../deployment/pipelines/chatqa/resources-model-cpu.yaml).
You have two options:

### Option 1: Change KV cache for your specific model only

Find your model entry in the file and override `VLLM_CPU_KVCACHE_SPACE` directly:

```yaml
# deployment/pipelines/chatqa/resources-model-cpu.yaml
  "meta-llama/Llama-3.1-8B-Instruct":
    <<: *generic_base_cpu
    configMapValues:
      VLLM_CPU_KVCACHE_SPACE: "1"   # override for this model only
```

### Option 2: Change KV cache for all models (generic anchors)

Update the base anchors used by all models — this affects every model that inherits from them.

For **non-AWQ models** (`generic-base-cpu`):

```yaml
# deployment/pipelines/chatqa/resources-model-cpu.yaml
modelConfigs:
  generic-base-cpu: &generic_base_cpu
    configMapValues:
      VLLM_CPU_KVCACHE_SPACE: "1"   # <-- change from "10" to "1"
      ...
```

For **AWQ models** (`generic-base-awq-cpu`):

```yaml
  generic-base-awq-cpu: &generic_base_awq_cpu
    configMapValues:
      VLLM_CPU_KVCACHE_SPACE: "1"   # <-- change from "10" to "1"
      ...
```

> [!NOTE]
> `VLLM_CPU_KVCACHE_SPACE` defines the memory (in GB) reserved for the KV cache.
> Reducing it from the default `10` to `1` significantly lowers VLLM memory usage,
> which is critical for a 128 GB RAM system.
> This reduces the number of concurrent requests that can be held in cache but is acceptable for minimum deployments.

---

## Limited Single-User Deployment (32 logical cores / 64 GB)

> [!WARNING]
> This configuration is intended **only for single-user use** (e.g., evaluation, development, or demo environments).
> It is **not suitable for production or multi-user workloads**.

It is possible to run Intel® AI for Enterprise RAG on hardware with as few as **32 CPU logical cores** and **64 GB of RAM**.
To achieve this, the following options in your `config.yaml` and pipeline resource files must be adjusted to reduce resource consumption:

### Required config.yaml changes

| Option | Value | Purpose |
|---|---|---|
| `hpaEnabled` | `false` | Disables Horizontal Pod Autoscaling (eliminates replica overhead) |
| `balloons.enabled` | `false` | Disables NRI CPU pinning balloon policy |
| Telemetry / log collection | disabled | Reduces sidecar memory pressure |

### Required pipeline resource changes

In [`deployment/pipelines/chatqa/resources-model-cpu.yaml`](../deployment/pipelines/chatqa/resources-model-cpu.yaml):

```yaml
modelConfigs:
  generic-base-cpu: &generic_base_cpu
    configMapValues:
      VLLM_CPU_KVCACHE_SPACE: "1"   # Reduce KV cache to 1 GB
    resources:
      limits:
        cpu: "16"                   # Limit VLLM to 16 logical cores
        memory: "16Gi"              # Limit VLLM memory to 16 GB
      replicas: 1                   # Single replica only
```

Use `deployment/inventory/sample/config_minimal.yaml` as a starting base — it already applies most of the above settings.
Copy it to your inventory and apply the KV cache change as described in [KV Cache Size](#kv-cache-size-required-manual-step).

---

## Deploying the Application

Once your `config.yaml` is ready, run the application deployment playbook from the `deployment/` directory:

```bash
cd deployment
ansible-playbook playbooks/application.yaml \
  -e @inventory/<your-inventory>/config_minimal.yaml \
  --tags install
```

> [!NOTE]
> Replace `<your-inventory>` with your actual inventory directory name (e.g. `cluster` or `sample`).

