# Ingestion Microservice

This service allows multiple services to ingest data into a vector database.

## Table of Contents

1. [Ingestion Microservice](#ingestion-microservice)
2. [Configuration Options](#configuration-options)
   - 2.1. [Vector Store Support Matrix](#vector-store-support-matrix)
3. [Getting Started](#getting-started)
   - 3.1. [Prerequisites](#prerequisites)
   - 3.2. [🚀 Start Ingestion Microservice with Python (Option 1)](#-start-ingestion-microservice-with-python-option-1)
     - 3.2.1. [Install Requirements](#install-requirements)
     - 3.2.2. [Start Microservice](#start-microservice)
   - 3.3. [🚀 Start Ingestion Microservice with Docker (Option 2)](#-start-ingestion-microservice-with-docker-option-2)
     - 3.3.1. [Build the Docker service](#build-the-docker-service)
     - 3.3.2. [Run the Docker container](#run-the-docker-container)
   - 3.4. [Verify the Ingestion Microservice](#verify-the-ingestion-microservice)
     - 3.4.1. [Example input](#example-input)
     - 3.4.2. [Example output](#example-output)
4. [Additional Information](#additional-information)
   - 4.1. [Project Structure](#project-structure)

## Configuration options

Configuration is done by selecting the desired vector store type. In addition, the specific vector store endpoint connections settings have to be passed.  For more information on selecting proper vector database and usage please refer to [VectorStore documentation](../vectorstores/README.md).

| Environment Variable    | Default Value     | Description                                                                                      |
|-------------------------|-------------------|--------------------------------------------------------------------------------------------------|
| `VECTOR_STORE`          | `redis`           | Vector Store database type         |
| `INGESTION_USVC_PORT`          | `6120`           | (Optional) Ingestion microservice port         |
| `USE_HIERARCHICAL_INDICES` | `False`        | Enable/disable Hierarchical Indices Advanced RAG Technique         |

### Vector Store Support Matrix

Support for specific vector databases:

| Vector Database                                          |  Status   |
| -------------------------------------------------------- | --------- |
| [REDIS](../vectorstores/README.md#redis)                 | &#x2713;  |
| [REDIS-CLUSTER](../vectorstores/README.md#redis-cluster) | &#x2713;  |

## Getting started

Since this service is utilizing VectorStore code, you have to configure the underlying implementation by setting an env variable `VECTOR_STORE` along with vector database configuration for the selected endpoint.

There're 2 ways to run this microservice:
  - [via Python](#-start-ingestion-microservice-with-python-option-1)
  - [via Docker](#-start-ingestion-microservice-with-docker-option-2) **(recommended)**

### Prerequisites

To run this microservice, a vector database should be already running. To run one of the [supported vector](#vector-store-support-matrix) databases you can use sample docker-compose files [located here](../vectorstores/impl/).

### 🚀 Start Ingestion Microservice with Python (Option 1)

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
python opea_ingestion_microservice.py
```

This sample assumes redis as a vector store database. You can run it by [following this documentation](../vectorstores/README.md#redis).

### 🚀 Start Ingestion Microservice with Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the Docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/ingestion:latest -f comps/ingestion/impl/microservice/Dockerfile .
```

#### Run the Docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name="ingestion" --env-file comps/ingestion/impl/microservice/.env -p 6120:6120 opea/ingestion:latest
```

### Verify the Ingestion Microservice
#### Example input

```bash
  curl http://localhost:6120/v1/ingestion \
    -X POST \
    -d '{ docs: [ { "text": "What is Intel AVX-512?", "embedding": [1,2,3] } ] }' \
    -H 'Content-Type: application/json'
```
#### Example output

Output data, if the request is successfull, is equal to input data.

```json
{
  "docs": [
    {
      "text": "What is Intel AVX-512?",
      "embedding": [1, 2, 3]
    }
  ]
}
```

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the Ingestion service e.g. Dockerfile for the microservice.

- `utils/`: This directory contains scripts that are used by the Ingestion Microservice.
