## This document explains how to configure the Enterprise RAG pipeline

Enterprise RAG pipeline is being configured based on [manifests](../deployment/components/gmc/microservices-connector/config/manifests) and [flow configuration files](../deployment/components/gmc/microservices-connector/config/samples)

`Manifests` show the default component configuration, while `flow configuration files` define how those components are connected together.

When building the pipeline we are passing the `flow configuration files` as `PIPELINE` argument to [one_click_chatqa](../deployment/README.md#quickstart-with-oneclick-script)

**Example one_click command:**

```
./one_click_chatqna.sh -g <your HF token> -d gaudi_torch_guard 
```

Where `gaudi_torch_guard` points to [chatqa_gaudi_torch.yaml](../deployment/components/gmc/microservices-connector/config/samples/chatQnA_gaudi_torch.yaml)

The PODs settings are primarily managed by appropriate `.env` files for each microservice. The model name can be set in the Helm [`values.yaml`](../deployment/components/gmc/microservices-connector/helm/values.yaml) file and will be propagated further.

Based on this configuration K8s knows which POD should be deployed.

### Example: 
We want to modify our pipeline and change the LLM `MODEL_ID` from `mistralai/Mixtral-8x22B-Instruct-v0.1` to `meta-llama/Meta-Llama-3-70B`. All we need to do is to update the Helm values file:

```yaml
llm_model_gaudi: &hpu_model "mistralai/Mixtral-8x7B-Instruct-v0.1"
...
  vllm_gaudi:
    envfile: "src/comps/llms/impl/model_server/vllm/docker/.env.hpu"
    envs:
      LLM_VLLM_MODEL_NAME: *hpu_model
```

Next, re-deploy the pipeline using [quickstart](../deployment/README.md#quick-start-with-one-click-script) passing the modified config file.


## Managing Resources in Microservices Deployment

It's possible to update the resource requests and limits in the appropriate YAML file based on environment.

### Resource Files

The resource configurations are defined in separate YAML files:
- [`resources-cpu.yaml`](../deployment/components/gmc/microservices-connector/helm/resources-cpu.yaml)
- [`resources-gaudi.yaml`](../deployment/components/gmc/microservices-connector/helm/resources-gaudi.yaml)
- [`resources-tdx.yaml`](../deployment/components/gmc/microservices-connector/helm/resources-tdx.yaml)

These files contain the resource requests and limits for each microservice.

#### Example: `resources-gaudi.yaml`

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
  tgi_gaudi:
    replicas: 1
    resources:
      limits:
        habana.ai/gaudi: 8
```

> [!NOTE]
From all the resources defined, only those mentioned in the specific [config/samples](../deployment/components/gmc/microservices-connector/config/samples) file that the user will run will be used for deployment. Users should take this into account when calculating the resources needed for deployment based on the specific configurations they choose to include.
