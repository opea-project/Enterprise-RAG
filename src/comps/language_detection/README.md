# Language Detection Microservice

The Language Detection microservice can be run in 2 modes:

1. Pipeline: This mode adds multilingual support to ChatQnA pipelines. The microservice detects the language of the user's query as well as the LLM generated response to set up a prompt for translation.

2. Standalone: This mode supports standalone translation. The microservice detects the language of the provided text. It then sets up a prompt for translating the provided text from the source language (detected language) to the provided target language.

## Table of Contents

1. [Language Detection Microservice](#language-detection-microservice)
2. [Configuration Options](#configuration-options)
3. [Getting Started](#getting-started)
   - 3.1. [🚀 Start Language Detection Microservice with Python (Option 1)](#-start-language-detection-microservice-with-python-option-1)
     - 3.1.1. [Install Requirements](#install-requirements)
     - 3.1.2. [Start Microservice](#start-microservice)
   - 3.2. [🚀 Start Language Detection Microservice with Docker (Option 2)](#-start-language-detection-microservice-with-docker-option-2)
     - 3.2.1. [Build the Docker Image](#build-the-docker-image)
     - 3.2.2. [Run the Docker Container](#run-the-docker-container)
   - 3.3. [Verify the Language Detection Microservice](#verify-the-language-detection-microservice)
     - 3.3.1. [Check Status](#check-status)
     - 3.3.2. [Sending a Request](#sending-a-request)
       - 3.3.2.1. [Pipeline Mode](#pipeline-mode)
       - 3.3.2.2. [Standalone Mode](#standalone-mode)
4. [Additional Information](#additional-information)
   - 4.1. [Project Structure](#project-structure)

## Configuration Options

The configuration for the Language Detection Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable                 | Description                                                                |
|--------------------------------------|----------------------------------------------------------------------------|
| `LANGUAGE_DETECTION_USVC_PORT`       | The port of the microservice, by default 8001                              |
| `LANG_DETECT_STANDALONE`             | Set this to `True` for Standalone mode                                     |


## Getting started

There're 2 ways to run this microservice:
  - [via Python](#-start-language-detection-microservice-with-python-option-1)
  - [via Docker](#-start-language-detection-microservice-with-docker-option-2) **(recommended)**

### 🚀 Start Language Detection Microservice with Python (Option 1)

To start the Language Detection microservice, installing following python packages is required.

#### Install Requirements

```bash
pip install -r impl/microservice/requirements.txt
```

#### Start Microservice

```bash
python opea_language_detection_microservice.py
```

### 🚀 Start Language Detection Microservice with Docker (Option 2)

#### Build the Docker Image
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/language_detection:latest -f comps/language_detection/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container
```bash
docker run -d --name="language-detection-microservice" \
  --net=host \
  --ipc=host \
  opea/language_detection:latest
```

### Verify the Language Detection Microservice

#### Check Status

```bash
curl http://localhost:8001/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  Sending a Request

##### Pipeline Mode

The input request consists of the answer that has to be translated and a prompt containing the user's query.

**Example Input**

```bash
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:8001/v1/language_detection <<JSON_DATA
{
  "text": "Hi. I am doing fine.",
  "prompt": "### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results:   \n
### Question: 你好。你好吗？ \n
### Answer:"
}
JSON_DATA
```

**Example Output**

The output contains the answer, prompt template, source language and target language.

```json
{
  "id":"1b16e065a1fcbdb4d999fd3d09a619cb",
  "data": {"text":"Hi. I am doing fine.","source_lang":"English","target_lang":"Chinese"},
  "prompt_template":"\n Translate this from {source_lang} to {target_lang}:\n   {source_lang}:\n   {text}\n\n  {target_lang}: \n "
}
```

##### Standalone Mode

The input request consists of the text that has to be translated and the target language.

**Example Input**

```bash
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:8001/v1/language_detection <<JSON_DATA
{
  "text": "Hi. I am doing fine.",
  "target_language": "Chinese"
}
JSON_DATA
```

**Example Output**

The output contains the original text, prompt template, source language and target language.

```json
{
  "id":"1b16e065a1fcbdb4d999fd3d09a619cb",
  "data": {"text":"Hi. I am doing fine.","source_lang":"English","target_lang":"Chinese"},
  "prompt_template":"\n Translate this from {source_lang} to {target_lang}:\n   {source_lang}:\n   {text}\n\n  {target_lang}: \n "
}
```

## Additional Information
### Project Structure


The project is organized into several directories:

- `impl/`: This directory contains the implementation of the service e.g. Dockerfile for the microservice.

- `utils/`: This directory contains utility scripts and modules that are used by the Language Detection Microservice.
