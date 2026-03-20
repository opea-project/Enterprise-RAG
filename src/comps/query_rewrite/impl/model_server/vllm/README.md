# vLLM Model Server for Query Rewrite

This folder contains the configuration for a dedicated vLLM model server used by the Query Rewrite microservice.

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving. It delivers state-of-the-art serving throughput with advanced features such as PagedAttention and Continuous batching.

## Table of Contents

1. [vLLM Model Server for Query Rewrite](#vllm-model-server-for-query-rewrite)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Deploy vLLM Service using Docker Compose](#-deploy-vllm-service-using-docker-compose)
     - 2.2.1. [Modify the environment configuration file](#modify-the-environment-configuration-file)
     - 2.2.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.2.3. [Service Cleanup](#service-cleanup)
   - 2.3. [Verify the Services](#verify-the-services)
3. [Additional Information](#additional-information)
   - 3.1. [Pipeline Integration](#pipeline-integration)

## Getting Started

### Prerequisite

Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env](.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 Deploy vLLM Service using Docker Compose

#### Modify the environment configuration file

Modify the [.env](.env) file to suit your use case. Key configuration options:

| Environment Variable           | Default Value                              | Description                                      |
|--------------------------------|--------------------------------------------|--------------------------------------------------|
| `QUERY_REWRITE_VLLM_MODEL_NAME`| `AMead10/Llama-3.2-3B-Instruct-AWQ`       | The model to use for query rewriting             |
| `QUERY_REWRITE_VLLM_PORT`      | `8009`                                     | Port for the vLLM server                         |
| `VLLM_CPU_KVCACHE_SPACE`       | `40`                                       | KV cache space in GB                             |
| `VLLM_MAX_MODEL_LEN`           | `4096`                                     | Maximum model context length                     |
| `VLLM_QUANTIZATION`            | `awq`                                      | Quantization method (awq for default model)      |

#### Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
docker compose --env-file=.env -f docker-compose.yaml up --build -d
```

#### Service Cleanup

To cleanup the services using Docker Compose:

```bash
docker compose -f docker-compose.yaml down
```

### Verify the Services

First, check the logs to confirm the service is operational:

```bash
docker logs -f query-rewrite-vllm-model-server
```

Test the vLLM model server using the following command:

```bash
curl http://localhost:8009/v1/completions \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"model": "AMead10/Llama-3.2-3B-Instruct-AWQ", "prompt": "Rewrite the following query to be more specific: What is it?", "max_tokens": 64}'
```

**NOTICE**: First ensure that the model server is operational. Warming up might take a while, and during this phase, the endpoint won't be ready to serve the query.

## Additional Information

### Pipeline Integration

In the ChatQA pipeline, this vLLM instance is referenced as `vllm-query-rewrite-svc` and the Query Rewrite microservice connects to it via the `QUERY_REWRITE_LLM_ENDPOINT` environment variable.
