# Chat History Microservice

The Chat History Microservice provides persistent storage and retrieval of chat conversations using MongoDB as the backend database. This microservice enables applications to maintain conversation history, allowing users to access previous interactions and continue conversations seamlessly. The service supports creating, retrieving, updating, and deleting chat conversations with proper user authentication and authorization.

## Table of Contents

1. [Chat History Microservice](#chat-history-microservice)
2. [Configuration Options](#configuration-options)
3. [Getting Started](#getting-started)
   - 3.1. [Prerequisite: Start MongoDB Database Server](#prerequisite-start-mongodb-database-server)
   - 3.2. [🚀 Start Chat History Microservice with Python (Option 1)](#-start-chat-history-microservice-with-python-option-1)
     - 3.2.1. [Install Requirements](#install-requirements)
     - 3.2.2. [Start Microservice](#start-microservice)
   - 3.3. [🚀 Start Chat History Microservice with Docker (Option 2)](#-start-chat-history-microservice-with-docker-option-2)
     - 3.3.1. [Build the Docker Image](#build-the-docker-image)
     - 3.3.2. [Run the Docker Container](#run-the-docker-container)
   - 3.4. [Verify the Chat History Microservice](#verify-the-chat-history-microservice)
     - 3.4.1. [Check Status](#check-status)
     - 3.4.2. [API Endpoints](#api-endpoints)
4. [Additional Information](#additional-information)
   - 4.1. [Project Structure](#project-structure)
   - 4.2. [Tests](#tests)

---

## Configuration Options

The configuration for the Chat History Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable | Default Value | Description                                            |
|---------------------|---------|-------------------------------------------------------|
| `CHAT_HISTORY_MONGO_HOST`        | `127.0.0.1` | MongoDB host address                                  |
| `CHAT_HISTORY_MONGO_PORT`        | `27017`   | MongoDB port number                                   |
| `CHAT_HISTORY_USVC_PORT`        | `6120`       | (Optional) Chat History microservice port            |

## Getting started

There're 2 ways to run this microservice:
  - [via Python](#-start-chat-history-microservice-with-python-option-1)
  - [via Docker](#-start-chat-history-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start MongoDB Database Server
The Chat History Microservice requires a MongoDB database to be operational and accessible. You can start MongoDB using Docker. Check out [MongoDB Readme](./impl/database/mongo/README.md) for more information.

### 🚀 Start Chat History Microservice with Python (Option 1)

To start the Chat History microservice, installing python packages is required.

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
python opea_chat_history_microservice.py
```

### 🚀 Start Chat History Microservice with Docker (Option 2)

#### Build the Docker Image
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/chat_history:latest -f comps/chat_history/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container
```bash
docker run -d --name="chat-history-microservice" \
  -p 6012:6012 \
  --env-file comps/chat_history/impl/microservice/.env \
  --net=host \
  --ipc=host \
  opea/chat_history:latest
```

### Verify the Chat History Microservice

#### Check Status
```bash
curl http://localhost:6012/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### API Endpoints

The Chat History microservice exposes several endpoints to save, get, modify and delete the histories. The authorization happens through JWT token that needs to be added to the header.

**Save a new history**

Example input:

```bash
curl -X 'POST' \
    http://localhost:6012/v1/chat_history/save \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer <jwt_token_here>' \
    -d '{
    "history": [
      {
        "question": "What is capital of France?", "answer": "test2"
      }
    ]
    }'
```

Example output:

```json
{
  "id":"687e6d6d73637d38e1d511db",
  "history_name":"Chat bzl0gdtaxt"
}
```

**Append new pair of question and answer to the history**

Example input:

```bash
curl -X 'POST' \
    http://localhost:6012/v1/chat_history/save \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer <jwt_token_here>' \
    -d '{
    "history": [
      {
        "question": "What is capital of France?", "answer": "The capital of France is Paris."
      }
    ],
    "id": "687e6d6d73637d38e1d511db"
    }'
```

Example output:

```json
{
  "id":"687e6d6d73637d38e1d511db",
  "history_name":"Chat bzl0gdtaxt"
}
```

**Get a list of all histories for the user**

Example input:

```bash
curl -X 'GET' http://localhost:6012/v1/chat_history/get \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <jwt_token_here>'
```

Example output:

```json
[
  {
    "id":"687e4c2375eaed432a03fee5",
    "history_name":"Chat xgktmzm1md"
  },
  {
    "id":"687e6d6d73637d38e1d511db",
    "history_name":"Chat bzl0gdtaxt"
  }
]
```

**Get details of the specific history for the user**

Example input:

```bash
curl -X 'GET' http://localhost:6012/v1/chat_history/get?history_id=687e6d6d73637d38e1d511db \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <jwt_token_here>'
```

Example output:

```json
{
  "_id":"687e6d6d73637d38e1d511db",
  "history":[
    {
      "question":"What is capital of France?",
      "answer":"test2"
    },
    {
      "question":"What is capital of France?",
      "answer":"The capital of France is Paris."
    }
  ],
  "user_id":"ce004cfc-3ae9-4527-ab27-59c37bfc74df",
  "history_name":"Chat bzl0gdtaxt"
}
```

**Change the name of the history**

Example input:

```bash
curl -X 'POST' http://localhost:6012/v1/chat_history/change_name \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt_token_here>' \
  -d '{
    "history_name": "my chat conversation",
    "id": "687e6d6d73637d38e1d511db"
  }'
```

Example output:

```
no output returned. 200 returned in case of succesful change.
```

**Delete history**

Example input:

```bash
curl -X 'DELETE' http://localhost:6012/v1/chat_history/delete?history_id=687e6d6d73637d38e1d511db \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <jwt_token_here>'
```

Example output:

```
no output returned. 200 returned in case of succesful change.
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the Chat History microservice, including the MongoDB integration and API endpoints.

- `utils/`: This directory contains utility scripts and modules used by the Chat History Microservice for database operations and data validation.

#### Tests
- `src/tests/unit/chat_history/`: Contains unit tests for the Chat History Microservice components
