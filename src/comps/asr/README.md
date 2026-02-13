# ASR Microservice

This microservice provides Automatic Speech Recognition (ASR) functionality, converting audio files to text using Whisper or other compatible ASR models. The microservice is designed to work with ASR model servers like vLLM that expose OpenAI-compatible APIs.

## Table of Contents

1. [ASR Microservice](#asr-microservice)
2. [Supported Extension](#supported-extensions)
3. [Configuration Options](#configuration-options)
4. [Getting Started](#getting-started)
   - 4.1. [Prerequisite: Start ASR Model Server](#prerequisite-start-asr-model-server)
   - 4.2. [🚀 Start ASR Microservice with Python (Option 1)](#-start-asr-microservice-with-python-option-1)
     - 4.2.1. [Install Requirements](#install-requirements)
     - 4.2.2. [Start Microservice](#start-microservice)
   - 4.3. [🚀 Start ASR Microservice with Docker (Option 2)](#-start-asr-microservice-with-docker-option-2)
     - 4.3.1. [Build the Docker Image](#build-the-docker-image)
     - 4.3.2. [Run the Docker Container](#run-the-docker-container)
   - 4.4. [Verify the ASR Microservice](#verify-the-asr-microservice)
     - 4.4.1. [Check Status](#check-status)
     - 4.4.2. [Sending a Request](#sending-a-request)
       - 4.4.2.1. [Example Request](#example-request)
       - 4.4.2.2. [Example Output](#example-output)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)
   - 5.2. [Tests](#tests)

## Supported Extensions

| Extension name                 |  Status   |
| ----------------------------------| --------- |
| MP3 | ✓         |
| Wav | ✓         |

## Configuration Options

The configuration for the ASR Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable        | Description                                                          | Default               |
|-----------------------------|----------------------------------------------------------------------|-----------------------|
| `ASR_USVC_PORT`             | The port of the microservice                                         | 9009                  |
| `ASR_MODEL_NAME`            | The name of the ASR model to be used (e.g., "openai/whisper-small")  | openai/whisper-small  |
| `ASR_MODEL_SERVER`          | Specifies the type of model server (e.g., "vllm")                    | vllm                  |
| `ASR_MODEL_SERVER_ENDPOINT` | URL of the model server endpoint                                     | http://localhost:8008 |
| `OPEA_LOGGER_LEVEL`         | Logger level for the microservice                                    | INFO                  |

## Getting Started

There are 2 ways to run this microservice:
  - [via Python](#-start-asr-microservice-with-python-option-1)
  - [via Docker](#-start-asr-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start ASR Model Server

The ASR Microservice interacts with an ASR Model Server, which must be operational and accessible at the the URL specified by the `ASR_MODEL_SERVER_ENDPOINT` env.

Depending on the model server you want to use, follow the approppriate instructions in the [./impl/model_server](./impl/model_server/) directory to set up and start the service.

Refer to `README.md` of a particular library to get more information on starting a model server.

### 🚀 Start ASR Microservice with Python (Option 1)

To start the ASR microservice, installing all the dependencies first is required.

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
python opea_asr_microservice.py
```

The microservice will start and listen on the configured port (default: 9009).

### 🚀 Start ASR Microservice with Docker (Option 2)

#### Build the Docker Image

Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/asr:latest -f comps/asr/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container

```bash
docker run -d --name asr-microservice \
  --net=host \
  --ipc=host \
  opea/asr:latest
```

If the model server is running at a different endpoint than the default, update the `ASR_MODEL_SERVER_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
docker run -d --name asr-microservice \
  -e ASR_MODEL_SERVER_ENDPOINT="http://localhost:8008" \
  -e ASR_MODEL_NAME="openai/whisper-small" \
  -e ASR_MODEL_SERVER="vllm" \
  --net=host \
  --ipc=host \
  opea/asr:latest
```

### Verify the ASR Microservice

#### Check Status

```bash
curl http://localhost:9009/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

##### Example Request

```bash
curl http://localhost:9009/v1/audio/transcriptions \
  -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/audio/file.mp3" \
  -F "language=en" -F "response_format=json"
```

##### Example Output

```json
{
  "text": "The transcribed text from the audio file"
}
```

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the ASR microservice, including model servers integration and Dockerfiles.

- `utils/`: This directory contains utility scripts and modules used by the ASR Microservice for model servers connections.

### Tests
- `src/tests/unit/asr/`: Contains unit tests for the ASR Microservice components
