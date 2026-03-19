# Switching Pipelines in Intel® AI for Enterprise RAG

This document describes how to switch between different pipeline configurations in Intel® AI for Enterprise RAG to optimize for specific workloads and use cases.

> **Experimental feature notice**
>
> The upload-optimized pipeline is an experimental capability and its control-plane and data-plane configuration is still under active stabilization. There are known defects and performance regressions, and the deployment is not yet fully optimized or exhaustively validated across all topologies.
>
> For example, in high‑replica deployments, `embedding-usvc` can encounter upstream timeout/connection reset conditions when the `vllm-embedding` replica count is excessive, due to increased fan‑out, queueing pressure, and downstream saturation.

## Table of Contents

- [Switching Pipelines in Intel® AI for Enterprise RAG](#switching-pipelines-in-intel-ai-for-enterprise-rag)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Purpose](#purpose)
  - [Pipeline Types](#pipeline-types)
    - [ChatQA Full Pipeline](#chatqa-full-pipeline)
    - [Upload-Optimized Pipeline](#upload-optimized-pipeline)
  - [How to Switch Pipelines](#how-to-switch-pipelines)
    - [Switching to Upload Pipeline](#switching-to-upload-pipeline)
    - [Switching Back to ChatQA Pipeline](#switching-back-to-chatqa-pipeline)
  - [Pipeline Configuration Details](#pipeline-configuration-details)
    - [Configuration File Structure](#configuration-file-structure)
    - [Sample Path Files](#sample-path-files)
  - [Use Cases and Best Practices](#use-cases-and-best-practices)
    - [When to Use Upload Pipeline](#when-to-use-upload-pipeline)
  - [Technical Details](#technical-details)
    - [How Pipeline Switching Works](#how-pipeline-switching-works)
    - [Pipeline Architecture](#pipeline-architecture)
    - [Model Configurations](#model-configurations)
    - [Storage and Persistence](#storage-and-persistence)
  - [Related Documentation](#related-documentation)

---

## Overview

Intel® AI for Enterprise RAG supports multiple pipeline configurations that can be dynamically switched based on your workload requirements. The system maintains two distinct pipeline modes:

- **ChatQA Full Pipeline**: Complete RAG (Retrieval-Augmented Generation) workflow including embedding, retrieval, reranking, and LLM inference
- **Upload-Optimized Pipeline**: Streamlined configuration focused solely on document embedding and ingestion for high-throughput upload scenarios

Switching between these pipelines allows you to optimize resource utilization and performance for specific tasks without requiring separate deployments.

### Purpose

Pipeline switching enables:

- **Resource Optimization**: Deploy only the components needed for specific workloads
- **Performance Tuning**: Maximize throughput for embedding-heavy workloads
- **Operational Flexibility**: Switch configurations without redeploying the entire system

---

## Pipeline Types

### ChatQA Full Pipeline

The ChatQA pipeline includes all components necessary for complete RAG operations:

**Components included:**
- **Fingerprint**: Request metadata tracking and system fingerprinting
- **Embedding**: Vector embedding service for document and query processing
- **VLLM Embedding**: Model server for embedding inference
- **Retriever**: Vector search and document retrieval from vector databases
- **Reranking**: Result reranking for improved relevance
- **VLLM Reranking**: Model server for reranking inference
- **Prompt Template**: Prompt construction and templating
- **LLM Guard Input**: Input scanning and guardrails
- **LLM**: Chat completion and text generation service
- **VLLM (LLM)**: Model server for LLM inference

**Use cases:**
- Interactive chat and question answering
- Document summarization with context retrieval
- Full RAG workflows requiring all pipeline stages
- Production workloads with active user queries

**Configuration reference:**
- Sample path: [`chatqa/reference-cpu.yaml`](../deployment/pipelines/chatqa/reference-cpu.yaml) or [`chatqa/reference-hpu.yaml`](../deployment/pipelines/chatqa/reference-hpu.yaml)
- Resources: [`chatqa/resources-reference-cpu.yaml`](../deployment/pipelines/chatqa/resources-reference-cpu.yaml) or [`chatqa/resources-reference-hpu.yaml`](../deployment/pipelines/chatqa/resources-reference-hpu.yaml)

### Upload-Optimized Pipeline

The upload pipeline is a lightweight configuration designed specifically for document ingestion operations:

**Components included:**
- **Fingerprint**: Request metadata tracking
- **Embedding**: Vector embedding service (with increased throughput capacity)
- **VLLM Embedding**: Model server for embedding inference (with higher replica count)

**Components excluded:**
- **Retriever**: Not needed during upload-only operations
- **Reranking**: Not needed during upload-only operations
- **Prompt Template**: Not needed for document ingestion
- **LLM Guard**: Input scanning disabled for upload workloads
- **LLM**: Chat completion disabled during upload mode
- **VLLM**: LLM model server not deployed

**Use cases:**
- Bulk document upload and ingestion
- Initial data population and indexing
- Large-scale document processing
- Scheduled batch data imports
- System initialization and data migration

**Configuration reference:**
- Sample path: [`chatqa/reference-cpu-upload.yaml`](../deployment/pipelines/chatqa/reference-cpu-upload.yaml)
- Resources: [`chatqa/resources-reference-cpu-upload.yaml`](../deployment/pipelines/chatqa/resources-reference-cpu-upload.yaml)

**Resource optimization:**

The upload pipeline significantly reduces resource requirements by focusing on embedding throughput.

## How to Switch Pipelines

### Switching to Upload Pipeline

To enable the upload-optimized pipeline configuration:

**1. Edit your configuration file** ([`inventory/sample/config.yaml`](../deployment/inventory/sample/config.yaml)):

```yaml
# Enable upload-optimized pipeline mode
upload_pipelines: true
```

**2. Switch the pipeline:**

For an existing deployment:
```bash
cd deployment
ansible-playbook -K playbooks/application.yaml --tags update-configuration -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
```

**3. Verify the deployment:**

```bash
# Check that only upload-related pods are running
kubectl get pods -n chatqa

# You should see:
# - fingerprint pods
# - embedding pods (increased count)
# - vllm-embedding pods
# - NO vllm (LLM), retriever, reranking, or llm-guard pods
```

**Alternative: Override via command line**

Upload mode can also be enabled without editing the configuration file:

```bash
ansible-playbook -K playbooks/application.yaml --tags update-configuration \
  -i inventory/test-cluster/inventory.ini \
  -e @inventory/test-cluster/config.yaml \
  -e upload_pipelines=true
```

### Switching Back to ChatQA Pipeline

To return to the full RAG pipeline:

**1. Edit your configuration file:**

```yaml
# Disable upload-optimized pipeline mode
upload_pipelines: false
```

**2. Redeploy the application:**

```bash
cd deployment
ansible-playbook -K playbooks/application.yaml --tags update-configuration -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
```

**3. Verify the deployment:**

```bash
# Check that all pipeline pods are running
kubectl get pods -n chatqa

# You should see all components:
# - fingerprint, embedding, vllm-embedding
# - retriever, reranking, vllm-reranking
# - llm, vllm (LLM), llm-guard, prompt-template
```

**Alternative: Override via command line:**

```bash
ansible-playbook -K playbooks/application.yaml --tags update-configuration \
  -i inventory/test-cluster/inventory.ini \
  -e @inventory/test-cluster/config.yaml \
  -e upload_pipelines=false
```

## Pipeline Configuration Details

### Configuration File Structure

The main configuration file ([`inventory/sample/config.yaml`](../deployment/inventory/sample/config.yaml)) contains two pipeline configuration sections:

```yaml
# Control flag: determines which pipeline configuration to use
upload_pipelines: false  # Set to true for upload mode, false for full mode

# ChatQA pipeline configuration (used when upload_pipelines=false)
pipelines:
  - namespace: chatqa                                  # Kubernetes namespace
    samplePath: chatqa/reference-cpu.yaml             # Pipeline structure definition
    resourcesPath: chatqa/resources-reference-cpu.yaml # Resource requests/limits
    modelConfigPath: chatqa/resources-model-cpu.yaml  # Model configurations
    type: chatqa                                      # Pipeline type identifier

# Upload-optimized pipeline configuration (used when upload_pipelines=true)
upload_pipelines_config:
  - namespace: chatqa                                        # Same namespace as default
    samplePath: chatqa/reference-cpu-upload.yaml            # Upload pipeline structure
    resourcesPath: chatqa/resources-reference-cpu-upload.yaml # Upload resource config
    modelConfigPath: chatqa/resources-model-cpu.yaml        # Same model config
    type: chatqa                                            # Same type identifier
```

### Sample Path Files

Sample path files define the pipeline structure using GMConnector (GenAI Microservices Connector) resources.

**ChatQA Pipeline Example** ([`reference-cpu.yaml`](../deployment/pipelines/chatqa/reference-cpu.yaml)):

```yaml
apiVersion: gmc.opea.io/v1alpha3
kind: GMConnector
metadata:
  name: chatqa
  namespace: chatqa
spec:
  routerConfig:
    name: router
    serviceName: router-service
  nodes:
    root:
      routerType: Sequence
      steps:
      - name: Fingerprint
        dependency: Hard
        internalService:
          serviceName: fgp-svc
          config:
            endpoint: /v1/system_fingerprint/append_arguments
      - name: Embedding
        data: $response
        dependency: Hard
        internalService:
          serviceName: embedding-svc
          config:
            endpoint: /v1/embeddings
      # ... (retriever, reranking, prompt-template, llm-guard, llm, vllm)
```

**Upload Pipeline Example** ([`reference-cpu-upload.yaml`](../deployment/pipelines/chatqa/reference-cpu-upload.yaml)):

```yaml
apiVersion: gmc.opea.io/v1alpha3
kind: GMConnector
metadata:
  name: chatqa
  namespace: chatqa
  labels:
    gmc/platform: xeon
spec:
  routerConfig:
    name: router
    serviceName: router-service
  nodes:
    root:
      routerType: Sequence
      steps:
      - name: Fingerprint
        dependency: Hard
        internalService:
          serviceName: fgp-svc
          config:
            endpoint: /v1/system_fingerprint/append_arguments
      - name: Embedding
        data: $response
        dependency: Hard
        internalService:
          serviceName: embedding-svc
          config:
            endpoint: /v1/embeddings
            EMBEDDING_MODEL_SERVER_ENDPOINT: vllm-embedding-svc
            EMBEDDING_MODEL_SERVER: "vllm"
            EMBEDDING_CONNECTOR: "generic"
      - name: VLLMEmbedding
        dependency: Hard
        internalService:
          serviceName: vllm-embedding-svc
          isDownstreamService: true
      # No retriever, reranking, llm-guard, prompt-template, llm, or vllm (LLM) nodes
```

## Use Cases and Best Practices

### When to Use Upload Pipeline

**Recommended scenarios:**

1. **Initial Data Population**
   - Loading large document collections into the system
   - Migrating data from existing knowledge bases
   - Bulk import operations during system setup

2. **Scheduled Batch Processing**
   - Nightly or periodic document ingestion jobs
   - Automated content updates from external sources
   - Regular data synchronization tasks

3. **Development and Testing**
   - Creating test datasets for development environments
   - Benchmarking embedding throughput
   - Testing data preparation workflows

4. **Maintenance Windows**
   - System maintenance with upload-only operations
   - Database reindexing with new embedding models
   - Data cleanup and re-ingestion

## Technical Details

### How Pipeline Switching Works

**Ansible role behavior:**

The application deployment Ansible role ([`roles/application/pipeline`](../deployment/roles/application/pipeline)) uses conditional logic to select the appropriate pipeline configuration:

```yaml
# From roles/application/pipeline/tasks/main.yaml
- name: Set sample path based on upload_pipelines flag
  set_fact:
    sample_path: "{{
      (upload_pipelines_config | selectattr('type', 'equalto', item.type) | map(attribute='samplePath') | first)
      if (upload_pipelines | default(false) | bool)
      else item.samplePath
    }}"

- name: Set resources path based on upload_pipelines flag
  set_fact:
    resources_path: "{{
      (upload_pipelines_config | selectattr('type', 'equalto', item.type) | map(attribute='resourcesPath') | first)
      if (upload_pipelines | default(false) | bool)
      else item.resourcesPath
    }}"
```

**Compatibility with other features:**

- **Balloons (topology-aware scheduling)**: Automatically disabled for upload pipelines
  ```yaml
  when: balloons.enabled and not (upload_pipelines | default(false) | bool)
  ```
- **HPA (Horizontal Pod Autoscaling)**: Fully supported; upload mode uses aggressive HPA policies
- **Multi-node deployment**: Compatible with both single-node and multi-node clusters
- **Gaudi/HPU acceleration**: Upload pipeline available for both CPU and HPU platforms
- **Telemetry and monitoring**: Full observability maintained in both modes

### Pipeline Architecture

**GMC Router Behavior:**

The GMConnector router dynamically adapts to the deployed pipeline configuration:

- **ChatQA mode**: Routes requests through all pipeline stages (embedding → retrieval → reranking → LLM)
- **Upload mode**: Routes requests only through embedding stage
- **Service discovery**: Automatically discovers available services in the namespace
- **Graceful degradation**: Handles missing services based on dependency configuration

**Service Dependencies:**

| Service | Dependency Type | ChatQA Pipeline | Upload Pipeline |
|---------|-----------------|------------------|-----------------|
| Fingerprint | Hard | Required | Required |
| Embedding | Hard | Required | Required |
| VLLM Embedding | Hard (downstream) | Required | Required |
| Retriever | Hard | Required | N/A |
| Reranking | Hard | Required | N/A |
| Prompt Template | Hard | Required | N/A |
| LLM Guard | Hard | Required | N/A |
| LLM | Hard | Required | N/A |
| VLLM (LLM) | Hard (downstream) | Required | N/A |

**Hard dependencies** mean the pipeline will fail if the service is unavailable. Upload pipeline removes hard dependencies on services not needed for embedding operations.

### Model Configurations

Both pipeline modes share the same model configuration file (`modelConfigPath`):

- **Embedding model**: Used in both modes; no changes required
- **Reranking model**: Ignored in upload mode (service not deployed)
- **LLM model**: Ignored in upload mode (service not deployed)

This sharing allows seamless switching without model reconfiguration.

### Storage and Persistence

**Persistent volumes:**

- Both pipeline modes use the same persistent volume claims (PVCs)
- Embedding model storage: Shared across both modes
- Vector database: Remains accessible; only client services differ
- Model caching: Embedding models remain cached; LLM models released in upload mode

**Data persistence:**

- **Vector store data**: Preserved during pipeline switches
- **User data**: Unaffected by pipeline configuration changes
- **Model weights**: Embedding models kept in storage; LLM models can be garbage collected

---

## Related Documentation

- **[configure_pipeline.md](configure_pipeline.md)**: General pipeline configuration and model selection
- **[advanced_configuration.md](advanced_configuration.md)**: Advanced options including multi-node support and HPU configuration
- **[application_deployment_guide.md](application_deployment_guide.md)**: Complete deployment instructions
- **[performance_tuning_tips.md](performance_tuning_tips.md)**: Performance optimization strategies
