# TEI Reranking Model Server

This document focuses on using the [Text Embeddings Interface (TEI)]((https://github.com/huggingface/text-embeddings-inference)) as a Reranker.

# Table of Contents

1. [TEI Reranking Model Server](#tei-reranking-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the TEI Service via script (Option 1)](#-start-the-tei-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
   - 2.3. [🚀 Deploy TEI Service with OPEA Reranking Microservice using Docker Compose (Option 2)](#-deploy-tei-service-with-opea-reranking-microservice-using-docker-compose-option-2)
     - 2.3.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 2.3.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.3.3. [Service Cleanup](#service-cleanup)
   - 2.4. [Verify the Services](#verify-the-services)

## Getting Started

### Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env.cpu](docker/.env.cpu) or [.env.hpu](docker/.env.hpu) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 Start the TEI Service via script (Option 1)
#### Run the script
Depending on what Hardware you want to run the TEI on, you can either specify `RERANK_DEVICE` to `"cpu"` or `"hpu"`.

```bash
chmod +x run_tei.sh
RERANK_DEVICE="cpu" ./run_tei.sh
```

The run_tei.sh script is a Bash script that starts a Docker container running the TEI model server, which defaults to exposing the service on port `RERANKER_TEI_PORT` (default: **6060**). To change the port or the model (BAAI/bge-reranker-large), please edit the Bash script accordingly.

The script initiates a Docker container with the TEI model server running on port `RERANKER_TEI_PORT` (default: **6060**). Configuration settings are specified in the [.env.cpu](docker/.env.cpu) or [.env.hpu](docker/.env.hpu) file. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

### 🚀 Deploy TEI Service with OPEA Reranking Microservice using Docker Compose (Option 2)

To launch TEI along with the OPEA Reranking Microservice, follow these steps:

#### Modify the environment configuration file to align it to your case

Modify the `./docker/.env.cpu` file or `./docker/.env.hpu`, depending on what Hardware do you want to run the TEI:

```env
#HF_TOKEN=<your-hf-api-key>

## TEI Model Server Settings
RERANKER_TEI_MODEL_NAME="BAAI/bge-reranker-large"
RERANKER_TEI_PORT=6060

## Proxy Settings – Uncomment if Needed
#NO_PROXY=<your-no-proxy>
#HTTP_PROXY=<your-http-proxy>
#HTTPS_PROXY=<your-https-proxy>
```

#### Start the Services using Docker Compose

To build and start the services using Docker Compose

```bash
cd docker

docker compose --env-file=.env.cpu up --build -d
```

#### Service Cleanup
To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```

### Verify the Services

- Test the `reranking-tei-model-server` using the following command:

    ```bash
    curl localhost:6060/rerank \
        -X POST \
        -d '{"query":"What is DL?", "texts": ["DL is not...", "DL is..."]}' \
        -H 'Content-Type: application/json'
    ```

- Check the `reranking-tei-microservice` status:
    ```bash
    curl http://localhost:8000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `reranking-tei-microservice` using the following command:
    ```bash
    curl  http://localhost:8000/v1/reranking \
        -X POST \
        -d '{"initial_query":"What is DL?",
        "retrieved_docs": [{"text":"DL is not..."}, {"text":"DL is..."}]}' \
        -H 'Content-Type: application/json'
    ```
