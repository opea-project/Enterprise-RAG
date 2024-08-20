# TEI Embedding Server

This README provides instructions on how to run a model server using [TEI](https://github.com/huggingface/text-embeddings-inference).

## Start TEI Server

To get started with TEI, follow these steps:

```bash
chmod +x run_tei.sh
./run_tei.sh
```
This Bash script runs a text embeddings inference service in a Docker container, by default, exposing it on port TEI_PORT=8090.
In order to change TEI_PORT please edit bash script.

**Test your TEI model server using the following command**:

```bash
curl localhost:$TEI_PORT/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

## Set up TEI model server along with embedding microservice with Docker Compose

To launch TEI along with the embedding microservice, follow these steps:

1. **Modify the `./docker/.env` file**:

    Modify the `./docker/.env` file in the root directory with the following content:

    ```env
    FRAMEWORK=<langchain or llama_index>
    PORT=<tei-model-server-port>
    MODEL_NAME=<embedding-model-name>
    HUGGINGFACE_API_KEY=<your-hf-api-key>
    NO_PROXY=<your-no-proxy>
    HTTP_PROXY=<your-http-proxy>
    HTTPS_PROXY=<your-https-proxy>
    ```

2. **Start the Services using Docker Compose**:

    Build and start the services using Docker Compose:

    ```bash
    cd docker
    docker-compose up --build -d
    ```

3. **Test the embedding microservice**:

    Get the microservice status:
    ```bash
    curl http://localhost:6000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

    Test the TEI service using the following command:

    ```bash
    curl localhost:6000/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
    ```

4. **Cleanup the Services using Docker Compose**:

    Cleanup the services using Docker Compose:

    ```bash
    cd docker
    docker-compose down
    ```
