# vLLM ASR Model Server

This document focuses on using the vLLM as an ASR (Automatic Speech Recognition) endpoint.

[vLLM](https://github.com/vllm-project/vllm) is a high-performance inference engine primarily designed for serving large language models. In addition to text generation, vLLM can also be used to efficiently serve automatic speech recognition (ASR) models, such as [OpenAI Whisper](https://openai.com/index/whisper/).

## Table of Contents

1. [vLLM ASR Model Server](#vllm-asr-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the vLLM Service via script (Option 1)](#-start-the-vllm-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
     - 2.2.2. [Verify the vLLM Service](#verify-the-vllm-service)
   - 2.3. [🚀 Deploy vLLM Service with ASR Microservice using Docker Compose (Option 2)](#-deploy-vllm-service-with-asr-microservice-using-docker-compose-option-2)
     - 2.3.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 2.3.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.3.3. [Service Cleanup](#service-cleanup)
   - 2.4. [Verify the Services](#verify-the-services)

## Getting Started

### Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the dotenv configuration files.
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
The script initiates a Docker container with the vLLM model server running on port `ASR_VLLM_PORT` (default: **8008**). Configuration settings are specified in the environment configuration [docker/cpu/.env](docker/cpu/.env) file. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

#### Verify the vLLM Service
Below examples are presented for hpu device.

First, check the logs to confirm the service is operational:
```bash
docker logs -f asr-vllm-model-server
```

The following log messages indicate that the startup of model server is completed:
```bash
(APIServer pid=1) INFO 01-28 17:52:29 [api_server.py:1346] Starting vLLM API server 0 on http://0.0.0.0:8008
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:38] Available routes are:
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /openapi.json, Methods: HEAD, GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /docs, Methods: HEAD, GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /docs/oauth2-redirect, Methods: HEAD, GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /redoc, Methods: HEAD, GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /scale_elastic_ep, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /is_scaling_elastic_ep, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /tokenize, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /detokenize, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /inference/v1/generate, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /pause, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /resume, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /is_paused, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /metrics, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /health, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /load, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/models, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /version, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/responses, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/responses/{response_id}, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/responses/{response_id}/cancel, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/messages, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/chat/completions, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/completions, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/audio/transcriptions, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/audio/translations, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /ping, Methods: GET
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /ping, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /invocations, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /classify, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/embeddings, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /score, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/score, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /rerank, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v1/rerank, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /v2/rerank, Methods: POST
(APIServer pid=1) INFO 01-28 17:52:29 [launcher.py:46] Route: /pooling, Methods: POST
(APIServer pid=1) INFO:     Started server process [1]
(APIServer pid=1) INFO:     Waiting for application startup.
(APIServer pid=1) INFO:     Application startup complete.
(APIServer pid=1) INFO:     127.0.0.1:41746 - "GET /health HTTP/1.1" 200 OK
(APIServer pid=1) INFO:     127.0.0.1:48680 - "GET /health HTTP/1.1" 200 OK
(APIServer pid=1) INFO:     127.0.0.1:39782 - "GET /health HTTP/1.1" 200 OK
(APIServer pid=1) INFO:     127.0.0.1:57528 - "GET /health HTTP/1.1" 200 OK

```

### 🚀 Deploy vLLM Service with ASR Microservice using Docker Compose (Option 2)

To launch vLLM Service along with the ASR Microservice, follow these steps:

#### Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

#### Start the Services using Docker Compose

To build and start the services using Docker Compose

```bash
cd docker
mkdir -p data
export UID && docker compose --env-file=.env up --build -d
```

#### Service Cleanup

To cleanup the services using Docker Compose:

```bash
cd docker
docker compose -f docker-compose.yaml down
```

### Verify the Services

- Test the `asr-vllm-model-server` using the following command:
    ```bash
    curl http://localhost:8008/v1/audio/transcriptions \
        -X POST \
        -H "Content-Type: multipart/form-data" \
        -F "file=@/path/to/audio/file.mp3" \
        -F "language=en"
    ```
    **NOTICE**: First ensure that the model server is operational. Warming up might take a while, and during this phase, the endpoint won't be ready to serve the query.

- Check the `asr-microservice` status:

    ```bash
    curl http://localhost:9009/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `asr-microservice` using the following command:
    ```bash
    curl http://localhost:9009/v1/audio/transcriptions \
        -X POST \
        -H "Content-Type: multipart/form-data" \
        -F "file=@/path/to/audio/file.mp3" \
        -F "language=en" -F "response_format=json"
    ```