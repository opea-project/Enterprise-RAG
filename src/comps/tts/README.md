# TTS Microservice

This microservice provides Text-to-Speech (TTS) functionality, converting text into audio message using microsoft/speecht5_tts or other compatible TTS models. The microservice is designed to work with TTS model servers that expose OpenAI-compatible APIs.

## Table of Contents

1. [TTS Microservice](#tts-microservice)
2. [Supported response formats](#supported-response-formats)
3. [Configuration Options](#configuration-options)
4. [Getting Started](#getting-started)
   - 4.1. [Prerequisite: Start TTS Model Server](#prerequisite-start-tts-model-server)
   - 4.2. [🚀 Start TTS Microservice with Python (Option 1)](#-start-tts-microservice-with-python-option-1)
     - 4.2.1. [Install Requirements](#install-requirements)
     - 4.2.2. [Start Microservice](#start-microservice)
   - 4.3. [🚀 Start TTS Microservice with Docker (Option 2)](#-start-tts-microservice-with-docker-option-2)
     - 4.3.1. [Build the Docker Image](#build-the-docker-image)
     - 4.3.2. [Run the Docker Container](#run-the-docker-container)
   - 4.4. [Verify the TTS Microservice](#verify-the-tts-microservice)
     - 4.4.1. [Check Status](#check-status)
     - 4.4.2. [Sending a Request](#sending-a-request)
       - 4.4.2.1. [Example Request](#example-request)
       - 4.4.2.2. [Example Output](#example-output)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)
   - 5.2. [Tests](#tests)

## Supported response formats

| Extension name   |  Status   |
| -----------------| --------- |
| MP3 | ✓         |
| Wav | ✓         |

## Configuration Options

The configuration for the TTS Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                           | Default                  |
|---------------------------------|-------------------------------------------------------|--------------------------|
| `TTS_USVC_PORT`                 | The port of the microservice                          | 9009                     |
| `TTS_MODEL_SERVER`              | Specifies the type of model server (e.g., "fastapi")     | fastapi                  |
| `TTS_MODEL_SERVER_ENDPOINT`     | URL of the model server endpoint                      | http://localhost:8008    |
| `OPEA_LOGGER_LEVEL`             | Logger level for the microservice                     | INFO                     |

## Getting Started

There are 2 ways to run this microservice:
  - [via Python](#-start-llm-microservice-with-python-option-1)
  - [via Docker](#-start-llm-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start TTS Model Server

Before starting the microservice, you need to have an TTS model server running. You can start the vLLM server as follows:

```bash
cd ./impl/model_server/fastapi/docker/
docker compose --env-file=.env -f docker-compose.yaml up --build
```

The server will be accessible at `http://localhost:8008` by default.

### 🚀 Start TTS Microservice with Python (Option 1)

To start the TTS microservice, you need to install python packages first.

#### Install Requirements
To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python opea_tts_microservice.py
```

The microservice will start and listen on the configured port (default: 9009).

### 🚀 Start TTS Microservice with Docker (Option 2)

#### Build the Docker Image

Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/tts:latest -f comps/tts/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container

```bash
docker run -d \
  --name tts-microservice \
  --net=host \
  --ipc=host \
  opea/tts:latest
```

If the model server is running at a different endpoint than the default, update the `TTS_MODEL_SERVER_ENDPOINT` variable accordingly.

### Verify the TTS Microservice

#### Check Status

```bash
curl http://localhost:9009/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

##### Example Requests

```bash
curl http://localhost:9009/v1/audio/speech \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, this is a test of the text to speech system.",
    "voice": "default",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

```bash
curl http://localhost:9009/v1/audio/speech \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": "This is a longer text that will be automatically chunked. The microservice splits it by sentences. Each chunk is processed separately. The results are streamed back progressively. This approach handles long texts efficiently.",
    "voice": "default",
    "response_format": "mp3",
    "streaming": "True"
  }' \
  --output long_speech.mp3
```

##### Example Output

The output is an audio file (MP3, WAV) containing the synthesized speech, that can be received either as a whole or streamed.

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the TTS microservice, including model servers integration and Dockerfiles.

- `utils/`: This directory contains utility scripts and modules used by the TTS Microservice for model servers connections.

### Tests
- `src/tests/unit/tts/`: Contains unit tests for the TTS Microservice components
