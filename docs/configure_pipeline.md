## This document explains how to configure the Enterprise RAG pipeline

Enterprise RAG pipeline is being configured based on [manifests](../deployment/components/gmc/microservices-connector/config/manifests) and [flow configuration files](../deployment/pipelines/chatqa/)

`Manifests` show the default component configuration, while `flow configuration files` define how those components are connected together.

When building the pipeline, we pass the `flow configuration file` to the [configuration file](../deployment/README.md#prepare-configuration-files)

The PODs settings are primarily managed by the appropriate `.env` files for each microservice. The model name can be set in the Helm [`values.yaml`](../deployment/components/gmc/microservices-connector/helm/values.yaml) file and will be propagated further.

Based on this configuration, K8s knows which POD should be deployed.

### Example: 
We want to modify our pipeline and change the LLM `MODEL_ID` from `mistralai/Mixtral-8x22B-Instruct-v0.1` to `meta-llama/Meta-Llama-3-70B`. All we need to do is to update the Helm values file:

```yaml
llm_model_gaudi: &hpu_model "meta-llama/Meta-Llama-3-70B"
...
  vllm_gaudi:
    envfile: "src/comps/llms/impl/model_server/vllm/docker/hpu/.env"
    envs:
      LLM_VLLM_MODEL_NAME: *hpu_model
```

Next, re-deploy the pipeline using [quickstart](../deployment/README.md#quick-start-with-one-click) passing the modified config file.


## Managing Resources in Microservices Deployment

It's possible to update the resource requests and limits in the appropriate YAML file based on environment.

### Resource Files

The resource configurations are defined in separate YAML files:
- [`resources-reference-cpu.yaml`](../deployment/pipelines/chatqa/resources-reference-cpu.yaml)
- [`resources-reference-hpu.yaml`](../deployment/pipelines/chatqa/resources-reference-hpu.yaml)
- [`resources-tdx.yaml`](../deployment/components/gmc/microservices-connector/helm/resources-tdx.yaml)

These files contain the resource requests and limits for each microservice.

#### Example: `resources-reference-hpu.yaml`

```yaml
services:
  dataprep-usvc:
    replicas: 1
    resources:
      requests:
        cpu: 8
        memory: 16Gi
      limits:
        cpu: 8
        memory: 16Gi
...
  vllm_gaudi:
    replicas: 1
    resources:
      limits:
        habana.ai/gaudi: 8
```

> [!NOTE]
From all the resources defined, only those mentioned in the specific [pipeline](../deployment/pipelines/chatqa/) file that the user will run will be used for deployment. Users should take this into account when calculating the resources needed for deployment based on the specific configurations they choose to include.


## Supported list of models

The Enterprise RAG pipeline allows you to select a model from a predefined list of supported models. These lists, along with their configuration options, are maintained in the following files:

- [`resources-model-cpu.yaml`](../deployment/pipelines/chatqa/resources-model-cpu.yaml) (for CPU-based models)
- [`resources-model-hpu.yaml`](../deployment/pipelines/chatqa/resources-model-hpu.yaml) (for Gaudi/HPU-based models)

Each model entry in these files specifies recommended settings such as environment variables and command-line arguments. You can select any model from the list by putting it into your Helm [`values.yaml`](../deployment/components/gmc/microservices-connector/helm/values.yaml) file.

### How to add or modify a model

To use a custom model or adjust the configuration of an existing one:

1. **Open** the appropriate file for your hardware:
   - For CPU: [`resources-model-cpu.yaml`](../deployment/pipelines/chatqa/resources-model-cpu.yaml)
   - For Gaudi/HPU: [`resources-model-hpu.yaml`](../deployment/pipelines/chatqa/resources-model-hpu.yaml)
2. **Add a new entry** under `modelConfigs` with your desired model name and configuration, or **edit the configuration** of an existing model as needed (e.g., change environment variables or command-line arguments).

   Example:
   ```yaml
    modelConfigs:
      "casperhansen/llama-3-8b-instruct-awq":
        configMapValues:
          VLLM_SKIP_WARMUP: "false"
          VLLM_CPU_KVCACHE_SPACE: "40"
          VLLM_DTYPE: "bfloat16"
          VLLM_MAX_NUM_SEQS: "256"
          VLLM_TP_SIZE: "1"
          OMP_NUM_THREADS: "32"
          VLLM_PP_SIZE: "1"
          VLLM_MAX_MODEL_LEN: "4096"
        extraCmdArgs: ["--device", "cpu", "--pipeline-parallel-size", "$(VLLM_PP_SIZE)", "--dtype", "$(VLLM_DTYPE)", "--max_model_len", "$(VLLM_MAX_MODEL_LEN)", "--max-num-seqs", "$(VLLM_MAX_NUM_SEQS)", "--disable-log-requests", "--download-dir", "/data", "--quantization", "awq"]
   ```

3. **Reference the model** in your Helm [`values.yaml`](../deployment/components/gmc/microservices-connector/helm/values.yaml) file:
   ```yaml
   llm_model: &cpu_model "casperhansen/llama-3-8b-instruct-awq"
   ```
   or for Gaudi:
   ```yaml
   llm_model_gaudi: &hpu_model "mistralai/Mixtral-8x7B-Instruct-v0.1"
   ```


> [!NOTE]
> If a model is not found in the list, the pipeline will use the `defaultModelConfigs` settings defined at the bottom of the same YAML file.


<details>
<summary><strong>NOTE</strong>: About YAML anchors and base configs</summary>

Some models in the configuration files use YAML anchors (such as `&generic_base_cpu` or `&generic_base_awq_cpu`) to point to shared base configurations.  
- If you want to change the configuration for all the models that use a particular base, you can edit the base config itself (the section with the anchor).
- If you want to change the configuration for only one model, copy the base config, paste it under your desired model name, and modify it as needed.

This willl help you avoid unintentional changes when only one model needs to be customized.

**Example:**

Suppose you want to customize only the `"casperhansen/llama-3-8b-instruct-awq"` model, which uses the `&generic_base_awq_cpu` anchor:

```yaml
modelConfigs:
  generic-base-awq-cpu: &generic_base_awq_cpu
    configMapValues:
      VLLM_SKIP_WARMUP: "false"
      VLLM_CPU_KVCACHE_SPACE: "40"
      VLLM_DTYPE: "bfloat16"
      VLLM_MAX_NUM_SEQS: "256"
      VLLM_TP_SIZE: "1"
      OMP_NUM_THREADS: "32"
      VLLM_PP_SIZE: "1"
      VLLM_MAX_MODEL_LEN: "4096"
    extraCmdArgs: ["--device", "cpu", "--pipeline-parallel-size", "$(VLLM_PP_SIZE)", "--dtype", "$(VLLM_DTYPE)", "--max_model_len", "$(VLLM_MAX_MODEL_LEN)", "--max-num-seqs", "$(VLLM_MAX_NUM_SEQS)", "--disable-log-requests", "--download-dir", "/data", "--quantization", "awq"]

  "casperhansen/llama-3-8b-instruct-awq":
    <<: *generic_base_awq_cpu
```

To make changes only for `"casperhansen/llama-3-8b-instruct-awq"`, copy the base config and modify it:

```yaml
modelConfigs:
  "casperhansen/llama-3-8b-instruct-awq":
    configMapValues:
      VLLM_SKIP_WARMUP: "false"
      VLLM_CPU_KVCACHE_SPACE: "60"  # changed value
      VLLM_DTYPE: "bfloat16"
      VLLM_MAX_NUM_SEQS: "256"
      VLLM_TP_SIZE: "1"
      OMP_NUM_THREADS: "32"
      VLLM_PP_SIZE: "1"
      VLLM_MAX_MODEL_LEN: "4096"
    extraCmdArgs: ["--device", "cpu", "--pipeline-parallel-size", "$(VLLM_PP_SIZE)", "--dtype", "$(VLLM_DTYPE)", "--max_model_len", "$(VLLM_MAX_MODEL_LEN)", "--max-num-seqs", "$(VLLM_MAX_NUM_SEQS)", "--disable-log-requests", "--download-dir", "/data", "--quantization", "awq"]
```

</details>


### Passing the Model Config File in Ansible Pipelines

The model configuration file is specified under the `pipelines` section of your main [configuration file](./../deployment/README.md#prepare-main-configuration-file).
For example:
```yaml
pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-cpu.yaml
    resourcesPath: chatqa/resources-reference-cpu.yaml
    modelConfigPath: chatqa/resources-model-cpu.yaml
    type: chatqa
```
This allows you to control which model list and configuration are used for each pipeline deployment.
