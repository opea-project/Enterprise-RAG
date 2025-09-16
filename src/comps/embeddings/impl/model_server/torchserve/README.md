# TorchServe Embedding Model Server

This folder contains the implementation of the Torchserve server for an embedding model.

[TorchServe](https://pytorch.org/serve/) is a lightweight, scalable, and easy-to-use model serving library for PyTorch models. It provides a RESTful API for serving trained models, allowing users to deploy and serve their models in production environments. Moreover, Torchserve supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.

## Table of Contents

1. [TorchServe Embedding Model Server](#torchserve-embedding-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the TorchServe Service via script (Option 1)](#-start-the-torchserve-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
   - 2.3. [🚀 Deploy TorchServe Service with Embedding Microservice using Docker Compose (Option 2)](#-deploy-torchserve-service-with-embedding-microservice-using-docker-compose-option-2)
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

### 🚀 Start the TorchServe Service via script (Option 1)

#### Run the script

```bash

chmod +x run_torchserve.sh
./run_torchserve.sh
```

The script initiates a Docker container with the TorchServe model server running on port `TORCHSERVE_PORT` (default: **8090**) to handle inference requests. Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

### 🚀 Deploy TorchServe Service with Embedding Microservice using Docker Compose (Option 2)

To launch TorchServe Service along with the Embedding Microservice, follow these steps:


#### Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case. Refer to [Torchserve configuration](https://pytorch.org/serve/configuration.html) for supported variables.

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

- Test the `embedding-torchserve-model-server` using the following command:
    ```bash
    # check status
    curl http://localhost:8090/ping

    # list loaded models
    curl http://localhost:8091/models

    # inference; replace bge-large-en-v1.5 with the desired model identifier from the loaded models
    curl http://localhost:8090/predictions/bge-large-en-v1.5 \
      -H "Content-Type: application/json" \
      -d '{"inputs": ["What is machine learning?"]}'
    ```

- Check the `embedding-torchserve-microservice` status:
    ```bash
    curl http://localhost:6000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `embedding-torchserve-microservice` using the following command:
    ```bash
    curl localhost:6000/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```

## Additional Information
### Folder Structure

- `docker/`: Contains a Dockerfile and support files.
- `model/`: Contains a model handler for Torchserve and its support files.
