# System Fingerprint Microservice

The System Fingerprint microservice is responsible for generating and managing unique fingerprints for different systems and giving user ability to store and update component arguments. It includes the necessary scripts, configurations, and utilities to efficiently handle fingerprint data.

## Table of Contents

1. [System Fingerprint Microservice](#system-fingerprint-microservice)
2. [Configuration Options](#configuration-options)
3. [Getting Started](#getting-started)
   - 3.1. [Prerequisites](#prerequisites)
   - 3.2. [🚀 Start System Fingerprint Microservice with Python (Option 1)](#-start-system-fingerprint-microservice-with-python-option-1)
     - 3.2.1. [Install Requirements](#install-requirements)
     - 3.2.2. [Start Microservice](#start-microservice)
   - 3.3. [🚀 Start System Fingerprint Microservice with Docker (Option 2)](#-start-system-fingerprint-microservice-with-docker-option-2)
     - 3.3.1. [Build the Docker service](#build-the-docker-service)
     - 3.3.2. [Run the Docker container](#run-the-docker-container)
   - 3.4. [Example API Requests](#example-api-requests)
     - 3.4.1. [Health Check](#health-check)
     - 3.4.2. [Change arguments](#change-arguments)
     - 3.4.3. [Append arguments](#append-arguments)
4. [Additional Information](#additional-information)
   - 4.1. [Project Structure](#project-structure)

## Configuration options

Configuration is done by specifying the MongoDB connection details. Optionally, you can specify the microservice's port.

| Environment Variable    | Default Value     | Description |
|-------------------------|-------------------|-------------|
| `SYSTEM_FINGERPRINT_MONGODB_HOST` | `127.0.0.1` | MongoDB host |
| `SYSTEM_FINGERPRINT_MONGODB_PORT` | `27017` | MongoDB port |
| `MONGODB_NAME` | `SYSTEM_FINGERPRINT` | Name of MongoDB |
| `SYSTEM_FINGERPRINT_TEMPLATE_LANGUAGE` | `en` | The language of the default prompt template. Only `en` and `pl` are supported. |
| `SYSTEM_FINGERPRINT_USVC_PORT` | `6012` | (Optional) Microservice port |

## Getting started
### Prerequisites

To run this microservice, the MongoDB database should already be running. To run the database, you can use [the sample docker-compose file](./impl/database/mongo/docker-compose.yaml).

There're 2 ways to run this microservice:
  - [via Python](#-start-system-fingerprint-microservice-with-python-option-1)
  - [via Docker](#-start-system-fingerprint-microservice-with-docker-option-2) **(recommended)**

### 🚀 Start System Fingerprint Microservice with Python (Option 1)

#### Install Requirements
To freeze the dependencies of a particular microservice,[uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python system_fingerprint_microservice.py
```

### 🚀 Start System Fingerprint Microservice with Docker (Option 2)

Using a container is the preferred way to run the microservice.

#### Build the Docker service

Navigate to the `src` directory and use the Docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t systemfingerprint_usvc:latest -f comps/system_fingerprint/impl/microservice/Dockerfile .
```

#### Run the Docker container

Remember, you can pass configuration variables by using the `-e` option with the Docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name=systemfingerprint-microservice --env-file comps/system_fingerprint/impl/microservice/.env --network=host systemfingerprint_usvc:latest
```
### Example API Requests

Once the System Fingerprint service is up and running, users can access the database using the following API endpoint. Each API serves a different purpose and returns an appropriate response. The System Fingerprint microservice accepts JSON as input and returns JSON.

#### Health Check

To perform a health check, use the following command:

```bash
curl http://localhost:6012/v1/health_check  \
  -X GET                                    \
  -H 'Content-Type: application/json'
```

#### Change arguments

This endpoint allows you to change arguments and store them in MongoDB. It accepts input in the following format:

```python
List[ComponentArgument]
```

Where `ComponentArgument` is defined as:

```python
class ComponentArgument(BaseDoc):
    name: str
    data: dict
```

Example curl command:

```bash
curl -X POST http://localhost:6012/v1/system_fingerprint/change_arguments \
-H "Content-Type: application/json" \
-d '[
    {
        "name": "llm",
        "data": {
            "max_new_tokens": 1024,
            "top_k": 10
        }
    }
]'
```

A full set of possible configurations can be found in the file [object_document_mapper.py](utils/object_document_mapper.py).

#### Append arguments

This endpoint accepts input as a dictionary and appends up-to-date arguments based on records in MongoDB.

Example curl command:

```bash
curl -X POST http://localhost:6012/v1/system_fingerprint/append_arguments \
-H "Content-Type: application/json" \
-d '{
    "text": "What is AMX?"
}'
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the System Fingerprint service.
- `utils/`: This directory contains scripts that are used by the System Fingerprint Microservice.
