# FastAPI TTS Model Server

This document provides instructions on how to run a Text-to-Speech (TTS) model server using with CPU-optimized inference.

The FastAPI TTS Model Server provides an OpenAI-compatible API endpoint for generating speech from text. It supports multiple TTS models and provides flexibility in voice selection, audio format, and generation parameters.

## Supported Models

The FastAPI TTS Model Server has been validated on following models:

| Model | Description | Default voice | Features |
|-------|-------------|------------------|----------|
| [microsoft/speecht5_tts](https://huggingface.co/microsoft/speecht5_tts) **(default)** | Microsoft's SpeechT5 Text-to-Speech model | `awb` | Fastest generation but produces robotic-style voice |
| [Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) | Qwen3 TTS model with custom voice support | `ryan` | Voice customization through instructions parameter |
| [Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) | Larger Qwen3 TTS model with custom voice support | `ryan` | Voice customization through instructions parameter |
| [Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign) | Qwen3 TTS model with voice design capabilities | N/A (voice-agnostic) | Generates voices based on natural language descriptions (instructions) |

## Table of Contents

1. [FastAPI TTS Model Server](#fastapi-tts-model-server)
2. [Supported Models](#supported-models)
3. [Getting Started](#getting-started)
   - 3.1. [Prerequisite](#prerequisite)
   - 3.2. [🚀 Deploy TTS Service using Docker Compose](#-deploy-tts-service-using-docker-compose)
     - 3.2.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 3.2.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 3.2.3. [Service Cleanup](#service-cleanup)
   - 3.3. [Verify the Services](#verify-the-services)

## Getting Started

### Prerequisite

Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the dotenv configuration file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

Also, create a folder to preserve model data on host and ensure proper ownership:

```bash
mkdir -p docker/data/
sudo chown -R 1000:1000 ./docker/data
```

### 🚀 Deploy TTS Service using Docker Compose

To launch the FastAPI TTS Service, follow these steps.


#### Start the Services using Docker Compose

Modify the [./docker/.env](./docker/.env) file to suit your use case. Next, build and start the services using Docker Compose:

```bash
cd docker
docker compose up --build -d
```

**Note:** Due to secure container best practices, the main process is started as a non-privileged user. The volume directory `data/` must be created beforehand and have the appropriate permissions.

#### Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker
docker compose down
```

### Verify the Services

- Check the logs to confirm the service is operational:
    ```bash
    docker logs -f tts-fastapi-model-server
    ```

- Check the service health:
    ```bash
    curl -i http://localhost:8008/health
    ```

- Check which model is currently in use:
    ```bash
    docker logs tts-fastapi-model-server 2>&1 | grep "initialized successfully"
    ```

 - Test the `tts-fastapi-model-server` using the following command:

     - For testing the `microsoft/speecht5_tts` model:

        **WAV format output:**
        ```bash
        curl -X POST http://127.0.0.1:8008/v1/audio/speech \
            -H "Content-Type: application/json" \
            -d '{
                "input": "Hello, this is a test of the text to speech system.",
                "voice": "bdl",
                "response_format": "wav"
            }' --output speech1.wav
        ```

        **WAV format output:**
        ```bash
        curl -X POST http://127.0.0.1:8008/v1/audio/speech \
            -H "Content-Type: application/json" \
            -d '{
                "input": "Hello, this is a test of the text to speech system.",
                "voice": "bdl",
                "response_format": "wav"
            }' --output speech.wav
        ```

     - For testing the `Qwen` family of models:

        **MP3 format output:**
        ```bash
        curl -X POST http://127.0.0.1:8008/v1/audio/speech \
            -H "Content-Type: application/json" \
            -d '{
                "input": "Hello, this is a test of the text to speech system.",
                "voice": "ryan",
                "response_format": "mp3"
            }' --output speech.mp3
