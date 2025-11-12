# Advanced Configuration Guide

This document describes configuration options available when deploying Intel® AI for Enterprise RAG.

## Table of Contents

1. [Configuration File](#configuration-file)
2. [Pipeline Configuration](#pipeline-configuration)
   1. [What are Pipelines?](#what-are-pipelines)
   2. [Default Pipeline Configuration](#default-pipeline-configuration)
   3. [Switching to Gaudi (HPU) Pipeline](#switching-to-gaudi-hpu-pipeline)
   4. [Using external inference endpoint](#using-external-inference-endpoint)
   5. [Resource Configuration Files](#resource-configuration-files)
3. [Multi-Node Support and Storage Requirements](#multi-node-support-and-storage-requirements)
   1. [Checking Your Default Storage Class](#checking-your-default-storage-class)
   2. [Storage Options](#storage-options)
   3. [Persistent Volume Claims (PVC) Configuration](#persistent-volume-claims-pvc-configuration)
4. [Changing AI Models](#changing-ai-models)
   1. [LLM (Large Language Model)](#llm-large-language-model)
   2. [Embedding Model](#embedding-model)
   3. [Reranking Model](#reranking-model)
   4. [Model Compatibility Notes](#model-compatibility-notes)
5. [Performance Tuning Tips](#performance-tuning-tips)
6. [Balloons - Topology-Aware Resource Scheduling](#balloons---topology-aware-resource-scheduling)
7. [Horizontal Pod Autoscaling (HPA)](#horizontal-pod-autoscaling-hpa)
8. [Additional Configuration Options](#additional-configuration-options)
   1. [Additional Pipelines](#additional-pipelines)
   2. [Vector Store Database Storage Settings](#vector-store-database-storage-settings)
   3. [EDP Storage Types](#edp-storage-types)
   4. [Additional Settings for Running Telemetry](#additional-settings-for-running-telemetry)
   5. [Security Settings](#security-settings)
   6. [Trust Domain Extensions (TDX)](#trust-domain-extensions-tdx)
   7. [Registry Configuration](#registry-configuration)
   8. [Local Image Building](#local-image-building)

---

## Configuration File

Multiple options can be changed in the configuration file when deploying Intel® AI for Enterprise RAG. 

For a complete reference of all available configuration options, see the sample configuration file: [inventory/sample/config.yaml](../deployment/inventory/sample/config.yaml)

## Pipeline Configuration

Pipelines are the core component of Intel® AI for Enterprise RAG, defining the AI workflow and resource allocation. This is the most important configuration section to understand.

### What are Pipelines?

Pipelines define the complete AI workflow including:
- **Microservices**: Individual components (LLM, embedding, retrieval, reranking, etc.)
- **Resource definitions**: CPU, memory, and storage requirements for each service
- **Model configurations**: Which AI models to use for each service
- **Service connections**: How components communicate with each other

### Default Pipeline Configuration

**Default**: CPU-optimized ChatQA pipeline

**ChatQA Pipeline:**
```yaml
pipelines:
  - namespace: chatqa                                      # Default: chatqa
    samplePath: chatqa/reference-cpu.yaml                 # Default: CPU reference
    resourcesPath: chatqa/resources-reference-cpu.yaml    # Default: CPU resources
    modelConfigPath: chatqa/resources-model-cpu.yaml      # Default: CPU models
    type: chatqa                                          # Default: chatqa
```

**Document Summarization (Docsum) Pipeline:**

The sample configuration file for Docsum is available at [inventory/sample/config_docsum.yaml](../deployment/inventory/sample/config_docsum.yaml).
```yaml
# Configuration for Docsum
pipelines:
  - namespace: docsum                                      # Namespace: docsum
    samplePath: docsum/reference-cpu.yaml                 # CPU reference for Docsum
    resourcesPath: docsum/resources-reference-cpu.yaml    # CPU resources for Docsum
    modelConfigPath: chatqa/resources-model-cpu.yaml      # CPU models (shared with ChatQA)
    type: docsum                                          # Pipeline type: docsum
```

### Switching to Gaudi (HPU) Pipeline

For Intel Gaudi AI accelerators:

**ChatQA Pipeline:**
```yaml
gaudi_operator: true              # Default: false
habana_driver_version: "1.22.1-6"

pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-hpu.yaml
    resourcesPath: chatqa/resources-reference-hpu.yaml
    modelConfigPath: chatqa/resources-model-hpu.yaml
    type: chatqa
```

**Docsum Pipeline:**
```yaml
gaudi_operator: true              # Default: false
habana_driver_version: "1.22.1-6"

pipelines:
  - namespace: docsum
    samplePath: docsum/reference-hpu.yaml
    resourcesPath: docsum/resources-reference-hpu.yaml
    modelConfigPath: chatqa/resources-model-hpu.yaml
    type: docsum
```

### Using external inference endpoint

External inference endpoint with OpenAI compatible API can be also used:

```yaml
pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-external-endpoint.yaml
    resourcesPath: chatqa/resources-reference-external-endpoint.yaml
    modelConfigPath: chatqa/resources-model-cpu.yaml
    type: chatqa
```

This requires additional configuration in `reference-external-endpoint.yaml` in llm step. I. e.
```yaml
      - name: Llm
        data: $response
        dependency: Hard
        internalService:
          serviceName: llm-svc
          config:
            endpoint: /v1/chat/completions
            LLM_MODEL_SERVER: vllm
            LLM_MODEL_SERVER_ENDPOINT: example.com
            LLM_MODEL_NAME: model-name
```

This supports two types of authentication:
- OAuth
- Api key

Refer to the [llm-usvc-readme](../src/comps/llms/README.md) for configuration.

### Resource Configuration Files

Each pipeline uses three configuration files:

1. **Sample Path** (`reference-cpu.yaml`): Defines pipeline structure and service connections
2. **Resources Path** (`resources-reference-cpu.yaml`): Sets CPU, memory, and storage limits
3. **Model Config Path** (`resources-model-cpu.yaml`): Specifies model loading parameters

> [!NOTE]
> To reduce vLLM resource usage, you can reduce the number of CPUs in your inventory configuration. Keep in mind that vLLM needs to be within a single NUMA node for optimal performance.

## Multi-Node Support and Storage Requirements

> [!NOTE]
> Storage configuration is part of infrastructure setup and should be configured before application deployment.

**Default**: `install_csi: "local-path-provisioner"` (single-node only)

For multi-node Kubernetes clusters, you need storage supporting **ReadWriteMany (RWX)** access mode.

You can use any CSI driver that supports storageClass with RWX. If you don't have such a CSI driver on your K8s cluster, you can install it by following the [Infrastructure Components Guide](infrastructure_components_guide.md), which provides options for NFS and NetApp Trident storage drivers.

### Checking Your Default Storage Class

**Critical**: Intel® AI for Enterprise RAG only works if your chosen storage class is set as the default. Verify this before deployment:

```bash
# Check current default storage class
kubectl get storageclass

# Look for one marked with (default)
NAME                 PROVISIONER                    RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path           rancher.io/local-path          Delete          WaitForFirstConsumer   false                  5d
nfs-csi (default)    nfs.csi.k8s.io                 Delete          Immediate              false                  2d

# If your desired storage class is not default, set it:
kubectl patch storageclass <your-storage-class-name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Remove default from other storage classes if needed:
kubectl patch storageclass <other-storage-class> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

### Storage Options

#### NFS Storage (Recommended for Multi-Node)
```yaml
install_csi: "nfs"                # Default: "local-path-provisioner"
nfs_node_name: "master-1"
nfs_host_path: "/opt/nfs-data"
```

#### NetApp Trident (Enterprise Storage)

```yaml
install_csi: "netapp-trident"
# Configure ONTAP backend settings
ontap_management_lif: "10.0.0.100"
ontap_svm: "your-svm-name"
# ... additional NetApp configuration
```

For detailed NetApp Trident configuration instructions, see: [NetApp Trident Integration Guide](../deployment/roles/infrastructure/netapp_trident_csi_setup/netapp_trident_integration.md)

#### Local Storage (Single-Node Only)
```yaml
install_csi: "local-path-provisioner"  # Default
```

### Persistent Volume Claims (PVC) Configuration

**Default**: ReadWriteOnce

If you are working on multi node cluster change accessMode to `ReadWriteMany`

```yaml
# Optional: Customize PVC settings
gmc:
  pvc:
    accessMode: "ReadWriteMany"        # Default: uses storage class default
    models:
      llm_model:
        name: "llm-pvc"
        storage: "50Gi"
        accessMode: "ReadWriteMany"
      embedding_model:
        name: "embedding-pvc" 
        storage: "20Gi"
```

**Important**: PVCs will only work correctly if your storage class supports the required access mode and is set as default.

## Changing AI Models

Intel® AI for Enterprise RAG provides the ability to change LLM, embedding, and reranking models to suit your specific requirements and performance needs.

### LLM (Large Language Model)

**Default**: `casperhansen/llama-3-8b-instruct-awq`

For CPU deployments, the list of supported models is available in: [deployment/pipelines/chatqa/resources-model-cpu.yaml](../deployment/pipelines/chatqa/resources-model-cpu.yaml)

For Gaudi deployments, the list of supported models is available in: [deployment/pipelines/chatqa/resources-model-hpu.yaml](../deployment/pipelines/chatqa/resources-model-hpu.yaml)

```yaml
# Default for CPU deployments
llm_model: "casperhansen/llama-3-8b-instruct-awq"

# Default for Gaudi deployments  
llm_model_gaudi: "mistralai/Mixtral-8x7B-Instruct-v0.1"
```

**Important**: 
- Ensure your Hugging Face token has access to gated models like Llama
- **When changing LLM models, you might need to update the prompt template** as each model might have their own suggested prompt format described on their Hugging Face model page. Changing prompt might affect multilingual models, as the prompt template is written in English.

### Embedding Model

**Default**: `BAAI/bge-base-en-v1.5`

```yaml
# Default
embedding_model_name: "BAAI/bge-base-en-v1.5"
```

**Important**: 
- Different embedding models have different vector dimensions
- **Check the vector dimensions length** in the embedding model description on Hugging Face
- **Update the `vector_dims` setting** in the `vector_databases` section of your inventory configuration to match the embedding model's output dimensions. Value of `vector_dims` must match `hidden_size` in config.json of the model e.g. https://huggingface.co/BAAI/bge-base-en-v1.5/blob/main/config.json#L11

Example configuration update:
```yaml
# In your inventory config file
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: redis-cluster
  vector_datatype: FLOAT32
  vector_dims: 768  # Update this to match your embedding model's dimensions
```

### Reranking Model

**Default**: `BAAI/bge-reranker-base`
```yaml
# Default
reranking_model_name: "BAAI/bge-reranker-base"
```

### Model Compatibility Notes

When changing models, consider:
- **Resource requirements**: Larger models need more CPU/memory/storage
- **Vector dimensions**: Embedding models must match your vector database configuration
- **Prompt templates**: LLM models may require specific prompt formats
- **Licensing**: Some models require acceptance of license agreements on Hugging Face
- **Performance**: Balance between accuracy and inference speed

## Performance Tuning Tips

For comprehensive performance optimization guidance, see: [Performance Tuning Guide](performance_tuning_tips.md)

## Balloons - Topology-Aware Resource Scheduling

**Default**: Enabled (`balloons.enabled: true`)

Balloons enables CPU pinning and NUMA-aware scheduling for optimal performance:

```yaml
# Default configuration
balloons:
  enabled: true                    # Default: true
  namespace: kube-system          # Default: kube-system
  services:
    vllm:
      resources:
        requests:
          cpu: 32                 # Default: 32 cores
          memory: 64Gi           # Default: 64Gi
```

**Benefits**:
- CPU pinning for consistent performance
- NUMA-aware scheduling
- Reduced context switching
- Better cache locality

**When to customize**:
- You have different CPU topology
- You want to allocate more/fewer cores to specific services
- You need to balance resources across multiple services

For detailed information, refer to: [deployment/components/nri-plugin/README.md](../deployment/components/nri-plugin/README.md)

## Horizontal Pod Autoscaling (HPA)

**Default**: Enabled (`hpaEnabled: true`)

HPA automatically scales pods based on CPU/memory utilization:

```yaml
# Default: enabled
hpaEnabled: true
```

**What it does**:
- Monitors resource usage across pods
- Automatically scales replicas up during high load
- Scales down when load decreases
- Ensures optimal performance during varying workloads

**When to disable**:
- Fixed workload scenarios
- When you prefer manual scaling control
- Resource-constrained environments where scaling isn't beneficial

## Additional Configuration Options

### Additional Pipelines

#### Document Summarization (Docsum) Pipeline

The Document Summarization pipeline provides capabilities to generate summaries of documents. The pipeline processes documents through a sequence of microservices including TextExtractor, TextCompression, TextSplitter, and generates summaries using LLM services.

**Configuration File:** [deployment/inventory/sample/config_docsum.yaml](../deployment/inventory/sample/config_docsum.yaml)

**Pipeline Definition:** [deployment/pipelines/docsum/](../deployment/pipelines/docsum/)

To test the Docsum pipeline after deployment:
```bash
./scripts/test_docsum.sh
```

For more details about the Docsum pipeline architecture and available configurations, refer to the [Docsum Pipeline README](../deployment/pipelines/docsum/README.md).

#### Language Translation Pipeline

> [!NOTE] 
> **Preview Status – not integrated into UI.**
> This is a preview pipeline and is currently in active development. While core functionality is in place, it is not yet integrated into the RAG UI, and development and validation efforts are still ongoing.

This pipeline provides language translation capabilities using advanced Language Models from the ALMA family, where:

- ALMA-7B-R model - recommended for CPU-based execution
- ALMA-13B-R model - recommended for Gaudi-based (Habana) acceleration

To test the translation pipeline, first deploy it by following the instructions in [Deployment Options → Installation](#installation), using a configuration file based on [deployment/inventory/sample/config_language_translation.yaml](../deployment/inventory/sample/config_language_translation.yaml).

Once deployed, run the provided shell script:
```bash
./scripts/test_translation.sh
```

### Vector Store Database Storage Settings

> [!NOTE]
> The default settings are suitable for smaller deployments only (by default, approximately 5GB of data).

You can expand the storage configuration for both the Vector Store and MinIO deployments by modifying their respective configurations:

If using EDP, update the `deployment/edp/values.yaml` file to increase the storage size under the `persistence` section. For example, set `size: 100Gi` to allocate 100GB of storage.

Similarly, for the selected Vector Store, you can increase the persistent storage size. This configuration is available in `deployment/components/vector_databases/values.yaml`. For example, set `persistence.size: 100Gi` to allocate 100GB of storage for Vector Store database data.

> [!NOTE]
> The Vector Store storage should have more storage than file storage due to containing both extracted text and vector embeddings for that data.

### EDP Storage Types

By default, the EDP storage type is set to MinIO, which deploys MinIO and S3 in-cluster. For additional options, refer to the [EDP documentation](../src/edp/README.md).

### Additional Settings for Running Telemetry

Intel® AI for Enterprise RAG includes the installation of a telemetry stack by default, which requires setting the number of iwatch open descriptors on each cluster host. For more information, follow the instructions in [Number of iwatch open descriptors](../deployment/components/telemetry/helm/charts/logs/README.md#1b-number-of-iwatch-open-descriptors).

### Security Settings

Pod Security Standards (PSS) and certificate configuration for secure deployments:

```yaml
# Defaults
enforcePSS: true                    # Default: true (Pod Security Standards enabled)
certs:
  autoGenerated: true               # Default: true (self-signed certificates)
  pathToCert: ""                    # Default: empty (auto-generated)
  pathToKey: ""                     # Default: empty (auto-generated)
```

**Pod Security Standards (PSS)**:
- When `enforcePSS: true`, namespaces are automatically labeled as "restricted" or "privileged" based on their security requirements
- Restricted namespaces enforce stricter security policies (no privileged containers, restricted capabilities)
- Privileged namespaces allow containers with elevated permissions when necessary
- This helps maintain security compliance across the Kubernetes cluster

**Certificate Configuration**:
- `autoGenerated: true`: Uses self-signed certificates for HTTPS endpoints
- `pathToCert` and `pathToKey`: Specify custom SSL certificate and private key paths for production deployments
- Custom certificates are recommended for production environments to avoid browser security warnings

### Trust Domain Extensions (TDX)

Intel® Trust Domain Extensions (Intel® TDX) provides hardware-based trusted execution environments for confidential computing:

```yaml
# Default: disabled (experimental feature)
tdx:
  enabled: false                    # Default: false
  td_type: "one-td"                # Default: "one-td"
  attestation:
    enabled: false                  # Default: false
```

**Configuration Options**:
- `enabled`: Enables Intel TDX protection for microservices
- `td_type`: Deployment type - "one-td" (single Trust Domain) or "coco" (Confidential Containers)
- `attestation.enabled`: Enables TDX-based remote attestation for verification

**Requirements**:
- 4th Gen Intel® Xeon® Scalable processors or later
- Ubuntu 24.04 with TDX enabled
- Compatible Kubernetes version (1.31+)

Only enable TDX if you have compatible Intel hardware and understand the experimental nature of this feature. For detailed TDX deployment instructions, see: [TDX Deployment Guide](tdx.md)

### Registry Configuration
```yaml
# Defaults
registry: "docker.io/opea"          # Default: public OPEA registry
tag: "1.5.0"                        # Default: current release tag
local_registry: false               # Default: false (use public registry)
```

### Local Image Building

Intel® AI for Enterprise RAG provides the ability to build Docker images locally instead of using pre-built images from public registries. This is particularly useful for:

- **Custom modifications** to microservices or components
- **Security requirements** that mandate locally built and verified images
- **Development and testing** of custom pipeline modifications

#### Single Node Clusters

For single node clusters, you can use the `--setup-registry` option in the `update_images.sh` script described in the [Building Images Guide](building_images.md).

```yaml
local_registry: false             # Use script-based registry setup
```

#### Multi-Node Clusters

For multi-node clusters, if you want to build your own images, you need to build a local registry accessible from the cluster. This can be done by setting:

```yaml
local_registry: true                    # Enable local registry pod
insecure_registry: "<node-name>:32000"  # Registry endpoint accessible from cluster
```

Where `<node-name>` is the Kubernetes node name where you want to deploy the registry pod. You can check available node names with:

```bash
kubectl get nodes
```

This option will create a Kubernetes pod with registry functionality and configure Docker and containerd settings to be able to push and pull images to the Kubernetes pod with registry.

> [!NOTE]
> Installation of the local registry pod is performed by running the `infrastructure.yaml` playbook. For detailed instructions, see the [Infrastructure Components Guide](infrastructure_components_guide.md).

For detailed instructions on building images locally, including prerequisites, build processes, and troubleshooting, refer to the [Building Images Guide](building_images.md).
