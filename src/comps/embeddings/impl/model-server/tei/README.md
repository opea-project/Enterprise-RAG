# TEI Embedding Model Server

This README provides instructions on how to run a model server using [TEI](https://github.com/huggingface/text-embeddings-inference).

## Getting Started

### 🚀 1. Start the TEI Service via script (Option 1)
#### 1.1. Run the script

```bash
chmod +x run_tei.sh
./run_tei.sh
```
The script initiates a Docker container with the text embeddings inference service running on port `TEI_PORT` (default: **8090**). Configuration settings are specified in the environment configuration file [docker/.env]. You can adjust these settings either by modifying the dotenv file or by exporting environment variables.

#### 1.2. Verify the TEI Service

```bash
curl http://localhost:8090/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

### 🚀 2. Deploy TEI Service with Embedding Microservice using Docker Compose (Option 2)

To launch TEI Service along with the Embedding Microservice, follow these steps:

#### 2.1. Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker
docker compose up --build -d
```

By default, the .env file is configured to use the langchain connector. However, switching to llama_index is straightforward. To build the service with the llama_index connector, you can export the `EMBEDDING_CONNECTOR` environment variable before running the command:

```bash
export EMBEDDING_CONNECTOR=llama_index
docker compose up --build -d
```
Alternatively, you can define it inline:
```bash
EMBEDDING_CONNECTOR=llama_index docker compose up --build -d
```

#### 2.3. Verify the Services

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

#### 2.4. Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```
