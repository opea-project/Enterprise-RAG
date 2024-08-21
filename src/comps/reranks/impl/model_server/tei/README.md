# TEI Reranking Model Server

This document focuses on using the [Text Embeddings Interface (TEI)]((https://github.com/huggingface/text-embeddings-inference)) as a Reranker.


## Start TEI Model Server
To get started with TEI, follow these steps:

```bash
chmod +x run.sh
./run_tei.sh
```
The run_tei.sh script is a Bash script that starts a Docker container running the TEI model server, which defaults to exposing the service on port `RERANKER_TEI_PORT` (default: **6060**). To change the port or the model (BAAI/bge-reranker-large), please edit the Bash script accordingly.


**Test your TEI model server using the following command**:

```bash
curl localhost:6060/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```
Expected output:
```
[{"index":1,"score":0.9988041},{"index":0,"score":0.02294873}]
```

## 🚀 Set up TEI model server along with reranking microservice with Docker Compose
To launch TEI along with the OPEA Reranking Microservice, follow these steps:

1. **Modify the `./docker/.env` file**:

    Modify the `./docker/.env` file in the root directory with the following content:

    ```env
    RERANKER_TEI_PORT=<tei-model-server-port>
    RERANKER_TEI_MODEL_NAME=<reranking-model-name>
    HUGGINGFACE_API_KEY==<your-hf-api-key>
    NO_PROXY=<your-no-proxy>
    HTTP_PROXY=<your-http-proxy>
    HTTPS_PROXY=<your-https-proxy>

    ## Reranking Microservice Settings ##
    ## Default values are specified in reranks/config.ini.
    ## To override these defaults, uncomment the relevant lines below and provide new values
    # RERANKING_HOST=0.0.0.0
    # RERANKING_PORT=8000
    # RERANKING_NAME=opea_service@reranking
    # RERANKIG_LOG_LEVEL=INFO
    # RERANKING_LOG_PATH=/tmp/opea/microservices/reranking/reranking.log
    ```

2. **Start the Services using Docker Compose**:

    To build and start the services using Docker Compose:

    ```bash
    cd docker
    docker-compose up --build -d
    ```


3. **Test the Services**:

    Test the `reranking-tei-model-server` using the following command:

    ```bash
    curl localhost:6060/rerank \
        -X POST \
        -d '{"query":"What is DL?", "texts": ["DL is not...", "DL is..."]}' \
        -H 'Content-Type: application/json'
    ```

    Check the `reranking-tei-microservice` status:
    ```bash
    curl http://localhost:8000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

    Test the `reranking-tei-microservice` using the following command:
    ```bash
    curl  http://localhost:8000/v1/reranking \
        -X POST \
        -d '{"initial_query":"What is DL?", 
        "retrieved_docs": [{"text":"DL is not..."}, {"text":"DL is..."}]}' \
        -H 'Content-Type: application/json'
    ```

4. **Cleanup the Services using Docker Compose**:

    To cleanup the services:

    ```bash
    cd docker
    docker-compose down
    ```

⚠️ **Notice:** For more details on configuration options and instructions please refer to the [OPEA Reranking Microservice's README](../../../README.md).

