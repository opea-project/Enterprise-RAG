# Enabling Multilingual Support for Intel® AI for Enterprise RAG

This guide covers the steps required to configure Intel® AI for Enterprise RAG (ERAG) for multilingual use. It assumes you already have a working ERAG deployment. For base installation instructions, refer to the [Intel AI Software Catalog – Enterprise Chat Q&A](https://aiswcatalog.intel.com/solutions/enterprise-chat-qna) or the [Application Deployment Guide](application_deployment_guide.md).

---

## Overview

By default, ERAG ships with English-only embedding and reranking models. To support additional languages you need to:

1. Switch to multilingual embedding and reranking models.
2. Point the LLM pipeline step at a base model that supports your target language.
3. Redeploy ERAG with updated config.yaml
4. Reingest any data that were ingested with previous embedding model.

> [!IMPORTANT]
> All three components—embedding, reranking, and the LLM—must support the target language for end-to-end multilingual RAG to work correctly.

---

## Prerequisites

- A running ERAG deployment (see the [Quick Start guide](https://aiswcatalog.intel.com/solutions/enterprise-chat-qna)).
- `kubectl` configured with the correct kubeconfig:

  ```bash
  export KUBECONFIG=$KUBECONFIG_DIR/admin.conf
  ```

---

## Step 1 – Update Embedding & Reranking Models in `config.yaml`

Edit your deployment configuration file (e.g., `deployment/inventory/test-cluster/config.yaml`) and update the model names:

```yaml
# Default (English-only):
# embedding_model_name: "BAAI/bge-base-en-v1.5"
# reranking_model_name: "BAAI/bge-reranker-base"

# Multilingual:
embedding_model_name: "intfloat/multilingual-e5-large-instruct"
reranking_model_name: "BAAI/bge-reranker-v2-m3"
```

After saving, redeploy the application so the new models are pulled and served:

```bash
cd deployment
ansible-playbook -u $USER -K playbooks/application.yaml \
  --tags configure,install \
  -e @inventory/test-cluster/config.yaml
```

---

## Step 2 – Configure a Remote / Multilingual LLM Endpoint

If your target language is not supported by the ERAG base model, use a remote (external) LLM endpoint that supports your target language and update the pipeline reference file.

### 2a. Edit the external-endpoint pipeline file

File: `deployment/pipelines/chatqa/reference-external-endpoint.yaml`

Locate the `Llm` step and set `LLM_MODEL_SERVER_ENDPOINT` and `LLM_MODEL_NAME` to point at your multilingual model endpoint:

```yaml
- name: Llm
  data: $response
  dependency: Hard
  internalService:
    serviceName: llm-svc
    config:
      endpoint: /v1/chat/completions
      LLM_MODEL_SERVER: vllm
      LLM_MODEL_SERVER_ENDPOINT: https://$BASE_URL
      LLM_MODEL_NAME: $MODEL_ID
```

> [!TIP]
> Replace the endpoint URL and model name with the values for your multilingual model server.

### 2b. Update the pipeline selection in `config.yaml`

Switch the pipeline to use the external-endpoint reference:

```yaml
pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-external-endpoint.yaml
    resourcesPath: chatqa/resources-reference-cpu.yaml
    modelConfigPath: chatqa/resources-model-cpu.yaml
    type: chatqa
```

---

## Step 3 – Update the LLM Microservice ConfigMap

Apply the following ConfigMap to the `chatqa` namespace so that the LLM microservice knows how to reach the remote model server:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-usvc-config
  namespace: chatqa
data:
  LLM_MODEL_SERVER_ENDPOINT: "https://$BASE_URL"
  LLM_MODEL_NAME: $MODEL_ID
  LLM_TLS_SKIP_VERIFY: "True"
  http_proxy: ""
  https_proxy: ""
  no_proxy: "localhost,.svc,.monitoring,127.0.0.1"
```

```bash
kubectl apply -f llm-usvc-configmap.yaml
```

> [!NOTE]
> Adjust `http_proxy`, `https_proxy`, and `no_proxy` values to match your network environment.

---

## Step 4 – Create or Update the API Key Secret

If the remote model server requires an API key / token, create a Kubernetes secret:

```bash
kubectl create secret generic vllm-api-key-secret \
  --from-literal=LLM_VLLM_API_KEY=<YOUR_TOKEN> \
  -n chatqa
```

To update an existing secret:

```bash
kubectl delete secret vllm-api-key-secret -n chatqa
kubectl create secret generic vllm-api-key-secret \
  --from-literal=LLM_VLLM_API_KEY=<YOUR_NEW_TOKEN> \
  -n chatqa
```

---

## Step 5 – Restart Affected Pods

After updating the ConfigMap and Secret, restart the LLM service pods so they pick up the new configuration:

```bash
kubectl rollout restart deployment/llm-svc -n chatqa
```

Verify all pods are running:

```bash
kubectl get pods -n chatqa
```

---

## Verification

1. **Test the connection:**

   ```bash
   ./scripts/test_connection.sh
   ```

2. **Open the UI** at `https://<your-FQDN>` and ask a question in the target language to confirm multilingual retrieval and generation work end-to-end.

---

## Recommended Multilingual Models

| Component  | Model | Languages |
|------------|-------|-----------|
| Embedding  | `intfloat/multilingual-e5-large-instruct` | 100+ languages |
| Reranking  | `BAAI/bge-reranker-v2-m3` | Multi-language cross-lingual reranking |
| LLM (example) | `Llama-3.2-3B-Instruct` (or any multilingual-capable model) | Depends on model training data |

---

## Further Reading

- [Application Deployment Guide](application_deployment_guide.md)
- [Configure Pipeline](configure_pipeline.md)
- [Switching Pipelines](switching_pipelines.md)
- [Advanced Configuration](advanced_configuration.md)
- [Intel AI Software Catalog – Enterprise Chat Q&A](https://aiswcatalog.intel.com/solutions/enterprise-chat-qna)
