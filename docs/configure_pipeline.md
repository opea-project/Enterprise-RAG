## This document explains how to configure the Enterprise RAG pipeline

Enterprise RAG pipeline is being configured based on [manifests](../deployment/microservices-connector/config/manifests) and [flow configuration files](../deployment/microservices-connector/config/samples)

`Manifests` show the default component configuration, while `flow configuration files` define how those components are connected together.

When building the pipeline we are passing the `flow configuration files` as an argument to [one_click_chatqa](../deployment/README.md#quickstart-with-oneclick-script)

**Example one_click command:**
./one_click_chatqna.sh -g "<HF Token>" -p $http_proxy -u $https_proxy -n $no_proxy -d gaudi_torch_guard

Based on this configuration K8s knows which POD should be deployed.

The PODs settings like `MODEL_ID`, `EMBEDDING_MODEL` are being set by passing env variables to PODs. Values in `manifests` show default values, however `flow configuration files` allow us to overwrite any env variable.

### Example: 
We want to modify our pipeline and change LLM MODEL_ID from `mistralai/Mixtral-8x22B-Instruct-v0.1` to `meta-llama/Meta-Llama-3-70B`. All we need to do is to add `MODEL_ID: "meta-llama/Meta-Llama-3-70B"` to [chatQnA_gaudi_torch_guard.yaml](../deployment/microservices-connector/config/samples/chatQnA_gaudi_torch_guard.yaml):

```
      - name: Llm
        data: $response
        internalService:
          serviceName: llm-svc
          config:
            endpoint: /v1/chat/completions
            MODEL_ID: "meta-llama/Meta-Llama-3-70B"
            TGI_LLM_ENDPOINT: tgi-gaudi-svc
            LLM_MODEL_SERVER_ENDPOINT: tgi-gaudi-svc
```
Next, re-deploy the pipeline using [quickstart](../deployment/README.md#quick-start-with-one-click-script) passing the modified config file.