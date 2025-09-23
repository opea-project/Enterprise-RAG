# Text Splitter Microservice

This microservice is designed to split received text into chunks. Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

## Table of Contents

1. [Text Splitter Microservice](#text-splitter-microservice)
2. [Support Matrix](#support-matrix)
3. [Configuration Options](#configuration-options)
4. [Getting Started](#getting-started)
   - 4.1. [🚀 Start Text Splitter Microservice with Python (Option 1)](#-start-text-splitter-microservice-with-python-option-1)
     - 4.1.1. [Install Requirements](#install-requirements)
     - 4.1.2. [Start Microservice](#start-microservice)
   - 4.2. [🚀 Start Text Splitter Microservice with Docker (Option 2)](#-start-text-splitter-microservice-with-docker-option-2)
     - 4.2.1. [Build the Docker service](#build-the-docker-service)
     - 4.2.2. [Run the Docker container](#run-the-docker-container)
   - 4.3. [Verify the Text Splitter Microservice](#verify-the-text-splitter-microservice)
     - 4.3.1. [Example input](#example-input)
     - 4.3.2. [Example output](#example-output)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)
     - 5.1.1. [Tests](#tests)

## Support Matrix

Supported splitter algorithms:

| Algorithm | Class                                                                 |
|----------------|------------------------------------------------------------------|
| default        | [Splitter](./utils/splitter.py)                   |
| semantic_chunking  | [SemanticSplitter](./utils/splitter.py)        |
| markdown_splitter | [MarkdownSplitter](./utils/splitter.py)        |


## Configuration options

Configuration is currently done via environment variables.

| Environment Variable             | Default Value             | Description                                                                                      |
|----------------------------------|---------------------------|--------------------------------------------------------------------------------------------------|
| `OPEA_LOGGER_LEVEL`              | `INFO`                    | Microservice logging output level                                                                |
| `TEXT_SPLITTER_USVC_PORT`        | `9399`                    | (Optional) Text Splitter microservice port                                                       |
| `CHUNK_SIZE`                     | `1500`                    | Size of chunks that the data is split into for further processing                                |
| `CHUNK_OVERLAP`                  | `100`                     | Size of chunks overlapping                                                                       |
| `USE_SEMANTIC_CHUNKING`          | `False`                   | Choose if semantic chunking should be used                                                       |
| `EMBEDDING_SERVICE_ENDPOINT`     | `http://embedding-svc.chatqa.svc:6000/v1/embeddings`  | Endpoint of the embedding microservice used for semantic chunking. For more details about the microservice, see [src/comps/embedding/README.md](../embeddings/README.md)                                  |
| `SEMANTIC_CHUNK_PARAMS`          | `{}`                      | Add semantic chunking parameters such as buffer_size, add_start_index, etc. Check Langchain documentation for SemanticChunker for reference. |


## Getting started

This microservice requires access to external network services for example for downloading models for parsing specific file formats for text extraction.

There're 2 ways to run this microservice:
  - [via Python](#-start-text-splitter-microservice-with-python-option-1)
  - [via Docker](#-start-text-splitter-microservice-with-docker-option-2) **(recommended)**

### 🚀 Start Text Splitter Microservice with Python (Option 1)

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
python opea_text_splitter_microservice.py
```

### 🚀 Start Text Splitter Microservice with Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the Docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/text_splitter:latest -f comps/text_splitter/impl/microservice/Dockerfile .
```

#### Run the Docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

```bash
docker run -d --name="text_splitter" --env-file comps/text_splitter/impl/microservice/.env -p 9399:9399 opea/text_splitter:latest
```

### Verify the Text Splitter Microservice
#### Example input

```bash
curl -X POST -H "Content-Type: application/json"  http://localhost:9399/v1/text_splitter  \
     -d '{"loaded_docs":[{"text":"Example DomainThis domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.More information...","metadata":{"url":"https://example.com/","filename":"index.html","timestamp":1748520579.4694135}}]}'
```

#### Example output

```json
{
  "docs": [
    {
      "text": "content chunk 1",
      "metadata": {
        "url":"https://example.com/",
        "filename": "/tmp/opea_upload/test.txt",
        "timestamp": 1726226461.738807
      }
    },
    {
      "text": "content chunk 2",
      "metadata": {
        "url":"https://example.com/",
        "filename": "/tmp/opea_upload/test.txt",
        "timestamp": 1726226461.738807
      }
    },
    {
      "text": "content chunk 3",
      "metadata": {
        "url":"https://example.com/",
        "filename": "/tmp/opea_upload/test.txt",
        "timestamp": 1726226461.738807
      }
    }
  ]
}
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the Text Splitter microservice, including Dockerfile.

- `utils/`: This directory contains utility scripts and modules used by the Text Splitter Microservice.

#### Tests
- `src/tests/unit/text_splitter/`: Contains unit tests for the Text Splitter Microservice components
