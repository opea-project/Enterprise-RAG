# vLLM Reranking Model Server

This folder contains the implementation of the [vLLM](https://github.com/vllm-project/vllm) server for a reranking model.

vLLM is a fast and easy-to-use library for LLM inference and serving. It exposes an OpenAI-compatible HTTP server and, for reranking, the `/v1/score` endpoint, which scores the relevance of a query against one or more documents. This implementation runs vLLM on CPU (`VLLM_TARGET_DEVICE="cpu"`).

# Table of Contents

1. [vLLM Reranking Model Server](#vllm-reranking-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the vLLM Service via script (Option 1)](#-start-the-vllm-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
   - 2.3. [🚀 Deploy vLLM Service with Reranks Microservice using Docker Compose (Option 2)](#-deploy-vllm-service-with-reranks-microservice-using-docker-compose-option-2)
     - 2.3.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 2.3.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.3.3. [Service Cleanup](#service-cleanup)
   - 2.4. [Verify the Services](#verify-the-services)
3. [Additional Information](#additional-information)
   - 3.1. [Folder Structure](#folder-structure)

## Getting Started

### Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 Start the vLLM Service via script (Option 1)

#### Run the script

```bash

chmod +x run_vllm.sh
./run_vllm.sh
```

The script initiates a Docker container with the vLLM model server running on port `RERANKING_VLLM_PORT` (default: **8109**) to handle inference requests. Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

### 🚀 Deploy vLLM Service with Reranks Microservice using Docker Compose (Option 2)

To launch the vLLM Service along with the Reranks Microservice, follow these steps:

#### Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

```env
#HF_TOKEN=<your-hf-api-key>

## VLLM Model Server Settings For Reranking ##
RERANKING_VLLM_MODEL_NAME="BAAI/bge-reranker-base"
RERANKING_VLLM_PORT=8109

## VLLM Settings ##
VLLM_CPU_KVCACHE_SPACE=0
VLLM_DTYPE=bfloat16

## Proxy Settings – Uncomment if Needed ##
#NO_PROXY=<your-no-proxy>
#HTTP_PROXY=<your-http-proxy>
#HTTPS_PROXY=<your-https-proxy>
```

The following variables are supported:

| Variable                    | Default                  | Description                                                            |
| --------------------------- | ------------------------ | ---------------------------------------------------------------------- |
| `RERANKING_VLLM_MODEL_NAME` | `BAAI/bge-reranker-base` | Hugging Face model name served for reranking.                          |
| `RERANKING_VLLM_PORT`       | `8109`                   | Host port on which the vLLM server is exposed.                         |
| `VLLM_CPU_KVCACHE_SPACE`    | `0`                      | KV cache space in GB. Reranking does not use a KV cache, so it is `0`. |
| `VLLM_DTYPE`                | `bfloat16`               | Data type used to load the model.                                      |
| `HF_TOKEN`                  | _(empty)_                | Hugging Face token, required for gated models.                         |

#### Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker

docker compose --env-file=.env up --build -d
```

#### Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```

### Verify the Services

- Test the `reranking-vllm-model-server` using the following command:
    ```bash
    curl http://localhost:8109/v1/score \
        -X POST \
        -d '{"model":"BAAI/bge-reranker-base", "text_1":"What is Deep Learning?", "text_2": ["Deep Learning is not...", "Deep learning is..."]}' \
        -H 'Content-Type: application/json'
    ```

    The response contains a relevance score for each document:
    ```json
    {
      "data": [
        {"index": 0, "score": 0.12},
        {"index": 1, "score": 0.95}
      ]
    }
    ```

- Check the `reranking-vllm-microservice` status:
    ```bash
    curl http://localhost:8000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `reranking-vllm-microservice` using the following command:
    ```bash
    curl  http://localhost:8000/v1/reranking \
        -X POST \
        -d '{"initial_query":"What is DL?", "retrieved_docs": [{"text":"DL is not..."}, {"text":"DL is..."}]}' \
        -H 'Content-Type: application/json'
    ```

## Additional Information
### Folder Structure

- `docker/`: Contains the Docker Compose definition and the `.env` configuration file.
- `entrypoint.sh`: Container entrypoint that launches `vllm serve`.
- `run_vllm.sh`: Helper script that reads `docker/.env` and starts the model server via Docker Compose.
