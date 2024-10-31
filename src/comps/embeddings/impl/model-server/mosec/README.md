# Mosec Embedding Server

This folder contains the implementation of the [Mosec](https://github.com/mosecorg/mosec) server for an embedding model.

## Getting Started

### 0. Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [docker/.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 1. Start the TorchServe Service via script (Option 1)

#### 1.1. Run the script

```bash

chmod +x run_mosec.sh
./run_mosec.sh
```
The script initiates a Docker container with the Mosec model server running on port `MOSEC_PORT` (default: **8000**). Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings either by modifying the dotenv file or by exporting environment variables.

#### 1.2. Verify the Mosec Service

```bash
curl http://localhost:8000/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

### 🚀 2. Deploy Mosec Service with Embedding Microservice using Docker Compose (Option 2)

To launch Mosec Service along with the Embedding Microservice, follow these steps:

#### 2.1. Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker
docker compose up --build -d
```

#### 2.3. Verify the Services

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

#### 2.4. Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```
