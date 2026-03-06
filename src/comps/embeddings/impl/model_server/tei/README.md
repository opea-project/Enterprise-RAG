# TEI Embedding Model Server

This README provides instructions on how to run a model server using [TEI](https://github.com/huggingface/text-embeddings-inference).

## Table of Contents

1. [TEI Embedding Model Server](#tei-embedding-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [🚀 Start the TEI Service via script (Option 1)](#-start-the-tei-service-via-script-option-1)
     - 2.1.1. [Run the script](#run-the-script)
   - 2.2. [🚀 Deploy TEI Service with Embedding Microservice using Docker Compose (Option 2)](#-deploy-tei-service-with-embedding-microservice-using-docker-compose-option-2)
     - 2.2.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 2.2.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.2.3. [Service Cleanup](#service-cleanup)
   - 2.3. [Verify the Services](#verify-the-services)

## Getting Started

### 🚀 Start the TEI Service via script (Option 1)
#### Run the script

```bash
chmod +x run_tei.sh
./run_tei.sh
```
The script initiates a Docker container with the text embeddings inference service running on port `TEI_PORT` (default: **8090**). Configuration settings are specified in the environment configuration file [docker/.env]. You can adjust these settings either by modifying the dotenv file or by exporting environment variables.

### 🚀 Deploy TEI Service with Embedding Microservice using Docker Compose (Option 2)

To launch TEI Service along with the Embedding Microservice, follow these steps:

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

- Test the `embedding-tei-model-server` using the following command:
    ```bash
    curl http://localhost:8090/embed \
        -X POST \
        -d '{"inputs":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```

- Check the `embedding-tei-microservice` status:
    ```bash
    curl http://localhost:6000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `embedding-tei-microservice` using the following command:
    ```bash
    curl localhost:6000/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```
