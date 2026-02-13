# vLLM Embedding Model Server

This folder contains the implementation of the vLLM server for an embedding model.

[vLLM](https://github.com/vllm-project/vllm) is a high-performance inference engine designed for serving large language models efficiently. While it is commonly used for text generation, vLLM can also be used to serve embedding models with very high throughput and low latency.

## Table of Contents

1. [vLLM Embedding Model Server](#vllm-embedding-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the vLLM Service via script (Option 1)](#-start-the-vllm-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
   - 2.3. [🚀 Deploy vLLM Service with Embedding Microservice using Docker Compose (Option 2)](#-deploy-vllm-service-with-embedding-microservice-using-docker-compose-option-2)
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

Also, create a folder to preserve model data on host and change the ownership to the id that would match user in the image:
```bash
mkdir -p docker/data/
sudo chown -R 1000:1000 ./docker/data
```

### 🚀 Start the vLLM Service via script (Option 1)

#### Run the script

```bash

chmod +x run_vllm.sh
./run_vllm.sh
```
The script initiates a Docker container with the vLLM model server running on port `EMBEDDING_VLLM_PORT` (default: **8108**). Configuration settings are specified in the[docker/.env](docker/.env) file. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.


### 🚀 Deploy vLLM Service with Embedding Microservice using Docker Compose (Option 2)

To launch vLLM Service along with the Embedding Microservice, follow these steps:


#### Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

#### Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker
mkdir -p data
export UID && docker compose --env-file=.env up --build -d
```

Note: Due to secure container best practices, main process is started as non-privileged user.
Due to the fact it uses volume mounts, the volume directory `data/` must be created beforehand.

#### Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```

### Verify the Services

- Test the `embedding-vllm-model-server` using the following command:
    ```bash
    # Replace BAAI/bge-base-en with the desired model identifier. Please note that the full model name, including the organization/namespace is expected.
 
    curl http://localhost:8108/v1/embeddings \
        -H "Content-Type: application/json" \
        -d '{
            "model": "BAAI/bge-base-en",
            "input": "What is Deep Learning?"
        }'
    ```

- Check the `embedding-vllm-microservice` status:
    ```bash
    curl http://localhost:6000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `embedding-vllm-microservice` using the following command:
    ```bash
    curl localhost:6000/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```

## Additional Information
### Folder Structure

- `docker/`: Contains a Dockerfile and support files.
- `model/`: Contains a model handler for vLLM and its support files.
