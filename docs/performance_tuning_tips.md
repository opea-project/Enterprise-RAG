# Performance Tuning Tips

This guide provides recommendations for optimizing the performance of your deployment.

## Table of Contents

   - [System Configuration Tips](#system-configuration-tips)
     - [LLM Model Selection](#llm-model-selection)
     - [Vector Database Selection](#vector-database-selection)
   - [Component Scaling](#component-scaling)
     - [TeiRerank Scaling](#teirerank-scaling)
     - [VLLM Scaling](#vllm-scaling)
     - [LLM-usvc Scaling](#llm-usvc-scaling)
   - [Runtime Parameter Tuning](#runtime-parameter-tuning)
   - [Monitoring and Validation](#monitoring-and-validation)
   - [Horizontal Pod Autoscaling](#horizontal-pod-autoscaling)

---

## System Configuration Tips

### LLM Model Selection
* To modify the LLM model, change the `llm_model` in [config.yaml](../deployment/inventory/sample/config.yaml) before deploying the pipeline.
* All supported LLM models are listed [here](../deployment/pipelines/chatqa/resources-model-cpu.yaml).

```yaml
# Example configuration
llm_model: "casperhansen/llama-3-8b-instruct-awq"
```

### Vector Database Selection
* For large-scale deployments (e.g., 1M+ vectors), use `redis-cluster` instead of standard redis.
* Modify the `vector_store` parameter in [config.yaml](../deployment/inventory/sample/config.yaml):

```yaml
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: redis-cluster  # Options: redis, redis-cluster
```

---

## Component Scaling

### TeiRerank Scaling
* Match the number of TeiRerank replicas to the number of CPU sockets on your machine for optimal performance.
* Adjust parameters in [resources-reference-cpu.yaml](../deployment/pipelines/chatqa/resources-reference-cpu.yaml).

```yaml
# Example for a 2-socket system
teirerank:
  replicas: 2  # Set to number of CPU sockets
```

### VLLM Scaling
* For machines with ≤64 physical cores per socket: use 1 replica per socket
* For machines with >64 physical cores per socket (e.g., 96 or 128): use 2 replicas per socket
* Adjust in [resources-reference-cpu.yaml](../deployment/pipelines/chatqa/resources-reference-cpu.yaml).

```yaml
# Example for a 2-socket system with ≤64 cores per socket
vllm:
  replicas: 2  # 1 replica per socket × 2 sockets
```

```yaml
# Example for a 2-socket system with >64 cores per socket
vllm:
  replicas: 4  # 2 replicas per socket × 2 sockets
```
* Additionally, If your machine has less then 32 physical cores per numa node, you need to reduce the number of CPU cores for vLLM:
```yaml
# Example for system with only 24 cores per numa node
  vllm:
    replicas: 1
    resources:
      requests:
        cpu: 24
        memory: 64Gi
      limits:
        cpu: 24
        memory: 100Gi
```

> **Performance Tip:** Consider enabling Sub-NUMA Clustering (SNC) in BIOS for better VLLM performance. This helps optimize memory access patterns across NUMA nodes.

### LLM-usvc Scaling
* When running more then one vLLM instance and when system is accessed by multiple concurrent users (e.g., 64+ users) use at least 2 replicas of llm-usvc
* Adjust parameters in [resources-reference-cpu.yaml](../deployment/pipelines/chatqa/resources-reference-cpu.yaml).

```yaml
llm-usvc:
  replicas: 2
```

---

## Runtime Parameter Tuning

You can adjust microservice parameters (e.g., `top_k` for reranker, `k` for retriever, `max_new_tokens` for LLM) using one of these methods:

1. **Using the Admin Panel UI:**
   * Navigate to the Admin Panel section in the UI
   * Find detailed instructions in [UI features](../docs/UI_features.md#admin-panel)

2. **Using Configuration Scripts:**
   * Utilize [the helper scripts](../src/tests/benchmark/e2e/README.md#helpers-for-configuring-erag)

> **Warning:** Only parameters that don't require a microservice restart can be adjusted at runtime.

---

## Horizontal Pod Autoscaling
* Consider enabling [HPA](../deployment#enabling-horizontal-pod-autoscaling) in order to allow the system to dynamically scale required resources in cluster
* HPA can be enabled in [config.yaml](../deployment/inventory/sample/config.yaml):

```yaml
hpaEnabled: true
```

---

## Monitoring and Validation

After making performance tuning changes, monitor system performance using:
* The built-in metrics dashboard
* Load testing with sample queries
* Memory and CPU utilization metrics

This will help validate that your changes have had the desired effect.
