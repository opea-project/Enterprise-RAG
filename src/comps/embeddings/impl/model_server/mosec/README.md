# Mosec Embedding Server

This folder contains the implementation of the [Mosec](https://github.com/mosecorg/mosec) server for an embedding model.

## Table of Contents

1. [Mosec Embedding Server](#mosec-embedding-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the TorchServe Service via script (Option 1)](#-start-the-torchserve-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
   - 2.3. [🚀 Deploy Mosec Service with Embedding Microservice using Docker Compose (Option 2)](#-deploy-mosec-service-with-embedding-microservice-using-docker-compose-option-2)
     - 2.3.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 2.3.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.3.3. [Service Cleanup](#service-cleanup)
   - 2.4. [Verify the Services](#verify-the-services)

## Getting Started

### Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [docker/.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 Start the TorchServe Service via script (Option 1)

#### Run the script

```bash

chmod +x run_mosec.sh
./run_mosec.sh
```
The script initiates a Docker container with the Mosec model server running on port `MOSEC_PORT` (default: **8000**). Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings either by modifying the dotenv file or by exporting environment variables.

### 🚀 Deploy Mosec Service with Embedding Microservice using Docker Compose (Option 2)

To launch Mosec Service along with the Embedding Microservice, follow these steps:

#### Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

#### Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker
docker compose up --build -d
```

#### Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```

### Verify the Services

- Test the `embedding-mosec-model-server` using the following command:
    ```bash
    curl http://localhost:8000/embed \
        -X POST \
        -d '{"inputs":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```

- Check the `embedding-mosec-microservice` status:
    ```bash
    curl http://localhost:6000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `embedding-mosec-microservice` using the following command:
    ```bash
    curl localhost:6000/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```
