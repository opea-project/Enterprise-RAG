# TGI LLM Model Server

This document focuses on using the [Text Generation Inference (TGI)](https://github.com/huggingface/text-generation-inference) as a LLM.


## Start TGI Model Server
To get started with TGI on device CPU, follow these steps:

```bash
# for cpu device
chmod +x run_tgi_cpu.sh
./run_tgi_cpu.sh


# for hpu device
chmod +x run_tgi_hpu.sh
./run_tgi_hpu.sh

```
The script starts a Docker container running the TGI model server, which defaults to exposing the service on port `LLM_TGI_PORT` (default: **8008**). To change the port or the model (Intel/neural-chat-7b-v3-3), please edit the Bash script accordingly.


**Test your TGI model server using the following command**:

```bash
curl http://localhost:8008/generate -X POST -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json'
```

Expected output:
```
{"generated_text":"\n\nDeep learning is part of a broader family of machine learning methods referred to as"}
```

## 🚀 Set up TGI model server along with LLM microservice with Docker Compose
To launch TGI along with the OPEA LLM Microservice, follow these steps:

1. **Modify the `./docker/.env` file**:

    Modify the `./docker/.env` file in the root directory with the following content:

    ```env
    ## TGI Model Server Settings ##
    LLM_TGI_PORT=8008
    LLM_TGI_MODEL_NAME="Intel/neural-chat-7b-v3-3"
    HUGGINGFACE_API_KEY=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
    # HUGGINGFACE_API_KEY=<your-hf-api-key>

    ## Proxy settings ##
    NO_PROXY=<your-no-proxy>
    HTTP_PROXY=<your-http-proxy>
    HTTPS_PROXY=<your-https-proxy>

    ## LLM Microservice Settings ##
    # Logging
    LOG_LEVEL=INFO
    LOG_PATH=/tmp/opea/microservices/llm/llm.log

    # OPEA Microservice
    USVC_NAME=opea_service@llm
    USVC_HOST=0.0.0.0
    USVC_PORT=9000
    ```

2. **Start the Services using Docker Compose**:

    To build and start the services using Docker Compose:

    ```bash
    cd docker

    # for CPU device
    docker-compose -f docker-compose-cpu.yaml up  --build -d

    # for HPU device (Gaudi)
    docker-compose -f docker-compose-hpu.yaml up  --build -d

    ```


3. **Test the Services**:

    Test the `llm-tgi-model-server` using the following command:

    ```bash
    curl localhost:8008/generate \
        -X POST \
        -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
        -H 'Content-Type: application/json'
    ```

    Check the `llm-tgi-microservice` status:
    ```bash
    curl http://localhost:9000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

    Test the `llm-tgi-microservice` for non-streaming mode using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
        -H 'Content-Type: application/json'
    ```

    Test the `llm-tgi-microservice` for non-streaming mode using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
        -H 'Content-Type: application/json'
    ```

4. **Cleanup the Services using Docker Compose**:

    To cleanup the services:

    ```bash
    cd docker

    # for CPU device
    docker-compose -f docker-compose-cpu.yaml down

    # for HPU device (Gaudi)
    docker-compose -f docker-compose-hpu.yaml down
    ```

⚠️ **Notice:** For more details on configuration options and instructions please refer to the [OPEA LLM Microservice's README](../../../README.md).

