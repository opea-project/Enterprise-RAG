# Chat History Microservice

The Chat History Microservice provides persistent storage and retrieval of chat conversations using MongoDB as the backend database. This microservice enables applications to maintain conversation history, allowing users to access previous interactions and continue conversations seamlessly. The service supports creating, retrieving, updating, and deleting chat conversations with proper user authentication and authorization.

---

## Configuration Options

The configuration for the Chat History Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable | Default Value | Description                                            |
|---------------------|---------|-------------------------------------------------------|
| `CHAT_HISTORY_MONGO_HOST`        | `127.0.0.1` | MongoDB host address                                  |
| `CHAT_HISTORY_MONGO_PORT`        | `27017`   | MongoDB port number                                   |
| `CHAT_HISTORY_USVC_PORT`        | `6120`       | (Optional) Chat History microservice port            |

## Getting started

### Prerequisite: Start MongoDB Database Server
The Chat History Microservice requires a MongoDB database to be operational and accessible. You can start MongoDB using Docker. Check out [MongoDB Readme](./impl/database/mongo/README.md) for more information.

We offer 2 ways to run this microservice:
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**

### 🚀1. Start Chat History Microservice with Python (Option 1)

To start the Chat History microservice, you need to install python packages first.

#### 1.1. Install Requirements
To freeze the dependencies of a particular microservice, we utilize [uv](https://github.com/astral-sh/uv) project manager. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### 1.2. Start Microservice
```bash
python opea_chat_history_microservice.py
```

### 🚀2. Start Chat History Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/chat_history:latest -f comps/chat_history/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:
```bash
docker run -d --name="chat-history-microservice" \
  -p 6012:6012 \
  --env-file comps/chat_history/impl/microservice/.env \
  --net=host \
  --ipc=host \
  opea/chat_history:latest
```

### 3. Verify the Chat History Microservice

#### 3.1. Check Status
```bash
curl http://localhost:6012/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### 3.2. API Endpoints

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
