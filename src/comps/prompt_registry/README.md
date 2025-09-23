# Prompt Registry Microservice

Prompt Registry microservice is responsible for storing and retrieving prompts by interfacing with a MongoDB database. It includes the necessary scripts, configurations, and utilities to manage prompt data efficiently.

## Table of Contents

1. [Prompt Registry Microservice](#prompt-registry-microservice)
2. [Configuration Options](#configuration-options)
3. [Getting Started](#getting-started)
   - 3.1. [Prerequisites](#prerequisites)
   - 3.2. [🚀 Start Prompt Registry Microservice with Python (Option 1)](#-start-prompt-registry-microservice-with-python-option-1)
     - 3.2.1. [Install Requirements](#install-requirements)
     - 3.2.2. [Start Microservice](#start-microservice)
   - 3.3. [🚀 Start Prompt Registry Microservice with Docker (Option 2)](#-start-prompt-registry-microservice-with-docker-option-2)
     - 3.3.1. [Build the Docker Service](#build-the-docker-service)
     - 3.3.2. [Run the Docker Container](#run-the-docker-container)
   - 3.4. [Example API Requests](#example-api-requests)
     - 3.4.1. [Health Check](#health-check)
     - 3.4.2. [Get Request](#get-request)
     - 3.4.3. [Create Request](#create-request)
     - 3.4.4. [Delete Request](#delete-request)
4. [Additional Information](#additional-information)
   - 4.1. [Project Structure](#project-structure)

## Configuration options

Configuration is done by specifing MongoDB connection details. Optionally, you can specify microservice's port.

| Environment Variable    | Default Value     | Description |
|-------------------------|-------------------|-------------|
| `PROMPT_REGISTRY_MONGO_HOST` | `127.0.0.1` | MongoDB host |
| `PROMPT_REGISTRY_MONGO_PORT` | `27017` | MongoDB port |
| `PROMPT_REGISTRY_USVC_PORT` | `None` | (Optional) Microservice port |

## Getting started
### Prerequisites

To run this microservice, MongoDB database should be already running. To run the database you can use sample docker-compose file [located here](./impl/database/mongo).

There're 2 ways to run this microservice:
  - [via Python](#-start-prompt-registry-microservice-with-python-option-1)
  - [via Docker](#-start-prompt-registry-microservice-with-docker-option-2) **(recommended)**

### 🚀 Start Prompt Registry Microservice with Python (Option 1)

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
python opea_prompt_registry_microservice.py
```

### 🚀 Start Prompt Registry Microservice with Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t promptregistry_usvc:latest -f comps/prompt_registry/impl/microservice/Dockerfile .
```

#### Run the Docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name=promptregistry-microservice --env-file comps/prompt_registry/impl/microservice/.env --network=host promptregistry_usvc:latest
```

### Example API Requests

Once prompt_registry service is up and running, users can access the database by using API endpoint below. Each API serves different purpose and return appropriate response. Prompt Registry microservice as an input accepts a json and returs a json.

#### Health Check

```bash
curl http://localhost:6012/v1/health_check  \
  -X GET                                    \
  -H 'Content-Type: application/json'
```

#### Get request

There are several possible requests that could be performed to retrieve prompts from the database:

- Retrieve all prompts from the database

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{}'
```

- Retrieve a prompt based on its id

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "prompt_id":"66f19e3dd938ac63a8e72e8f" }'
```

- Retrieve prompts based on provided filename

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "filename": "test.txt" }'
```

- Retrieve prompts based on provided text

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "prompt_text": "What is AMX" }'
```

- Retrieve prompts based on provided filename and text

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "filename": "test2.txt", "prompt_text": "What is AMX" }'
```

If prompts are retrieved successfully, an example output will look as follows:

```bash
{
  "id":"fb97366edb5096e66e852e264d09bfed",
  "prompts":[
    {
      "id":"c6c22dd00368f413c51557310a86a6f4",
      "filename":"test.txt",
      "prompt_id":"66f19e3dd938ac63a8e72e8d",
      "prompt_text":"What is AMX?"
    },
    {
      "id":"d3c22dd00368f529c51557310a86a6g8",
      "filename":"test.txt",
      "prompt_id":"15f19e3dd938a63a8e72ee92",
      "prompt_text":"What is AMX and why is AMX?"
    },
    {
      "id":"7d2fdad3dc6e05d6b492448c4a8762ec",
      "filename":"test2.txt",
      "prompt_id":"66f19e3dd938ac63a8e72e91",
      "prompt_text":"What is AMX and how?"
    }
  ]
}
```

#### Create request

Create endpoint accepts `prompt_text` and `filename` as inputs.
Example request looks as follows:

```bash
curl -X 'POST'                                      \
  http://localhost:6012/v1/prompt_registry/create   \
  -H 'accept: application/json'                     \
  -H 'Content-Type: application/json'               \
  -d '{ "prompt_text": "test prompt", "filename": "test" }'
```

If a prompt is added successfully, an example output will look as follows:

```bash
{"id":"1521111186d5f72a762acf3cdc5e564f","prompt_id":"66f2c021e9c8144058413159"}
```

#### Delete request

Delete endpoint accepts a `prompt_id` provided for the prompt that should be deleted. Example request looks as follows:

```bash
curl -X 'POST' \
  http://localhost:6012/v1/prompt_registry/delete \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "prompt_id":"66f1689ae3995e5691dc1110"}'
```

If the prompt is deleted successfully, the response will not return any output, but the returned status code will be `200`.

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the Prompt Registry service.
- `utils/`: This directory contains scripts that are used by the Prompt Registry Microservice.
