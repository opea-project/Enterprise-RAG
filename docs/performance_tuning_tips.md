# Performance Tuning Tips

This guide provides recommendations for optimizing the performance of your Intel® AI for Enterprise RAG deployment.

## Table of Contents

   - [System Configuration Tips](#system-configuration-tips)
     - [LLM Model Selection](#llm-model-selection)
     - [Vector Database Selection](#vector-database-selection)
     - [Redis Vector Database Performance Settings](#redis-vector-database-performance-settings)
   - [Component Scaling](#component-scaling)
     - [TeiRerank Scaling](#teirerank-scaling)
     - [VLLM Scaling](#vllm-scaling)
     - [LLM-usvc Scaling](#llm-usvc-scaling)
   - [Runtime Parameter Tuning](#runtime-parameter-tuning)
   - [Horizontal Pod Autoscaling](#horizontal-pod-autoscaling)
   - [Balloons Policy](#balloons-policy)
   - [Monitoring and Validation](#monitoring-and-validation)

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
* Intel® AI for Enterprise RAG supports following vector database backends. Choose based on your deployment scale:
  - **redis-cluster**: Multi-node cluster for production and large-scale deployments (1M+ vectors)
  - **mssql**: Microsoft SQL Server 2025 Express Edition for SQL-based vector operations
* Modify the `vector_store` parameter in [config.yaml](../deployment/inventory/sample/config.yaml):

```yaml
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: redis-cluster  # Options: redis-cluster, mssql
```

> [!NOTE]
> Selecting `mssql` requires accepting the Microsoft SQL Server EULA during deployment. Also, role-based access control (RBAC) for vector databases is not supported when using `mssql`. For detailed information about vector database options, see [Vector Database Selection](advanced_configuration.md#vector-database-selection).

### Redis Vector Database Performance Settings

In addition, larger databases might benefit from different vector store index configuration, such as changing the search algorithm from `FLAT` to `HNSW`. This is configurable via `deployment/inventory/**/config.yaml` as follows:

```yaml
edp:
  ingestion:
    config:
      vector_algorithm: "HNSW"
      vector_datatype: "FLOAT32"
      vector_distance_metric: "COSINE"
      # For HNSW Algorithm additional settings are available
      vector_hnsw_m: "32"
      vector_hnsw_ef_construction: "32"
      vector_hnsw_ef_runtime: "32"
      vector_hnsw_epsilon: "0.01"
```

Note that changing those settings requires additional RAM and storage for the vector database, since it creates additional indexes without removing the already existing ones. This operation might be time-consuming, depending on the amount of data already stored in the database.

Ensure the Redis instances have enough resources assigned, both from compute and storage. This is configurable via `deployment/inventory/**/config.yaml` as follows:

```yaml
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: redis-cluster
  redis-cluster:
    persistence:
      size: "30Gi"
    resources:
      requests:
        cpu: 8
        memory: 16Gi
      limits:
        cpu: 16
        memory: 128Gi
```

In case of `redis-cluster`, all above settings are applied for each cluster node.

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

> [!NOTE]
> **Automatic Configuration:** When [Balloons Policy](../deployment/components/nri-plugin/README.md) is enabled (`balloons.enabled: true` in config.yaml), the system automatically discovers node topology and calculates optimal VLLM replica distribution. Manual configuration is only required when `balloons.enabled: false`.

**Manual Configuration:**

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
* Additionally, if your machine has less than 32 physical cores per NUMA node, you need to reduce the number of CPU cores for vLLM:
```yaml
# Example for system with only 24 cores per NUMA node
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

> [!NOTE]
> Performance Tip: Consider enabling Sub-NUMA Clustering (SNC) in BIOS for better VLLM performance. This helps optimize memory access patterns across NUMA nodes.

### LLM-usvc Scaling
* When running more than one vLLM instance and when system is accessed by multiple concurrent users (e.g., 64+ users) use at least 2 replicas of llm-usvc.
* Adjust parameters in [resources-reference-cpu.yaml](../deployment/pipelines/chatqa/resources-reference-cpu.yaml).

```yaml
llm-usvc:
  replicas: 2
```

## Runtime Parameter Tuning

You can adjust microservice parameters (e.g., `top_k` for reranker, `k` for retriever, `max_new_tokens` for LLM) using one of these methods:

1. **Using the Admin Panel UI:**
   * Navigate to the Admin Panel section in the UI
   * Find detailed instructions in [UI features](../docs/UI_features.md#admin-panel)

2. **Using Configuration Scripts:**
   * Utilize [the helper scripts](../src/tests/e2e/benchmarks/chatqa/README.md#helpers-for-configuring-erag)

> [!WARNING]
> Only parameters that don't require a microservice restart can be adjusted at runtime.

---

## Horizontal Pod Autoscaling
* Consider enabling [HPA](../deployment#enabling-horizontal-pod-autoscaling) in order to allow the system to dynamically scale required resources in cluster.
* HPA can be enabled in [config.yaml](../deployment/inventory/sample/config.yaml):

```yaml
hpaEnabled: true
```

---

## Balloons Policy
* [Balloons Policy](../deployment/components/nri-plugin/README.md) is responsible for assigning optimal resources for inference pods such as vLLM, embedding, reranking and it is crucial for the performance of the whole deployment.
* It can be enabled in [config.yaml](../deployment/inventory/sample/config.yaml):

```yaml
balloons:
  enabled: true
  namespace: kube-system # alternatively, set custom namespace for balloons
  wait_timeout: 300 # timeout in seconds to wait for nri-plugin to be in ready state
  throughput_mode: true # set to true to optimize for horizontal scaling
  memory_overcommit_buffer: 0.1 # buffer (% of total memory) for pods using more memory than initially requested
```

---

## Monitoring and Validation

After making performance tuning changes, monitor system performance using:
* The built-in metrics dashboard
* Load testing with sample queries
* Memory and CPU utilization metrics

This will help validate that your changes have had the desired effect.
