# Query Rewrite Microservice

The Query Rewrite Microservice is designed to improve retrieval quality in RAG (Retrieval Augmented Generation) pipelines by rewriting user queries. It processes input queries and generates refined versions that are more effective for document retrieval. The service uses a dedicated LLM to rewrite queries in a single call — contextualizing them with conversation history when available and optimizing them for search.

## Table of Contents

1. [Query Rewrite Microservice](#query-rewrite-microservice)
2. [Configuration Options](#configuration-options)
3. [How It Works](#how-it-works)
4. [Getting Started](#getting-started)
   - 4.1. [Prerequisite: Start vLLM Model Server](#prerequisite-start-vllm-model-server)
   - 4.2. [🚀 Start Query Rewrite Microservice with Python (Option 1)](#-start-query-rewrite-microservice-with-python-option-1)
     - 4.2.1. [Install Requirements](#install-requirements)
     - 4.2.2. [Start Microservice](#start-microservice)
   - 4.3. [🚀 Start Query Rewrite Microservice with Docker (Option 2)](#-start-query-rewrite-microservice-with-docker-option-2)
     - 4.3.1. [Build the Docker Image](#build-the-docker-image)
     - 4.3.2. [Run the Docker Container](#run-the-docker-container)
   - 4.4. [Verify the Query Rewrite Microservice](#verify-the-query-rewrite-microservice)
     - 4.4.1. [Check Status](#check-status)
     - 4.4.2. [Sending a Request](#sending-a-request)

## Configuration Options

The configuration for the Query Rewrite Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable              | Default Value                                      | Description                                                                 |
|-----------------------------------|----------------------------------------------------|-----------------------------------------------------------------------------|
| `QUERY_REWRITE_LLM_ENDPOINT`      | `http://localhost:8009`                            | URL of the vLLM model server endpoint for query rewriting                   |
| `CHAT_HISTORY_ENDPOINT`           | _(not set)_                                        | Chat History service endpoint for retrieving conversation context           |
| `QUERY_REWRITE_TIMEOUT`           | `30`                                               | Timeout in seconds for LLM requests                                          |
| `QUERY_REWRITE_MAX_NEW_TOKENS`    | `256`                                              | Maximum new tokens for LLM response                                           |
| `QUERY_REWRITE_MAX_CONCURRENCY`   | `8`                                                | Maximum concurrent requests to LLM                                           |
| `QUERY_REWRITE_TEMPERATURE`       | `0.1`                                              | Temperature for LLM generation (lower = more deterministic)                  |
| `QUERY_REWRITE_USVC_PORT`         | `6626`                                             | Port for the Query Rewrite microservice                                      |
| `OPEA_LOGGER_LEVEL`               | `INFO`                                             | Log level for the microservice. Supported: DEBUG, INFO, WARNING, ERROR       |

## How It Works

The Query Rewrite Microservice rewrites user queries in a **single LLM call** that handles both contextualization and refinement:

- **Contextualization** (when chat history is available):
  - If a `history_id` is provided and chat history exists, the query is rewritten to be self-contained
  - Resolves pronouns and references (e.g., "it", "that", "the above") using conversation context
  - Example: "How does it work?" → "How does Retrieval Augmented Generation work?"

- **Query Refinement**:
  - Optimizes the query for better retrieval performance
  - Expands acronyms (e.g., "RAG" → "Retrieval Augmented Generation")
  - Fixes typos and abbreviations
  - Preserves proper nouns, product names, and technical terms unchanged
  - Example: "explain transformers" → "explain transformer models (neural network architecture)"

- **LLM Warmup**: On startup, a minimal request is sent to the LLM to warm up the connection and verify connectivity, preventing slow first user requests.

Non-timeout errors (e.g., max input tokens exceeded) are propagated to the caller. On timeout, the original query is passed through unchanged, ensuring pipeline resilience.

## Getting Started

There are 2 ways to run this microservice:
  - [via Python](#-start-query-rewrite-microservice-with-python-option-1)
  - [via Docker](#-start-query-rewrite-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start vLLM Model Server

The Query Rewrite Microservice requires a vLLM model server for LLM inference. You can start it using the docker compose available in [impl/model_server/vllm](impl/model_server/vllm/):

```bash
cd impl/model_server/vllm
docker compose --env-file=.env -f docker-compose.yaml up -d
```

The default model is `AMead10/Llama-3.2-3B-Instruct-AWQ` (3B parameters, AWQ quantized).

### 🚀 Start Query Rewrite Microservice with Python (Option 1)

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
python opea_query_rewrite_microservice.py
```

### 🚀 Start Query Rewrite Microservice with Docker (Option 2)

#### Build the Docker Image

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../../
docker build -t opea/query-rewrite:latest -f comps/query_rewrite/impl/microservice/Dockerfile .
```

Please note that the building process may take a while to complete.

#### Run the Docker Container

```bash
docker run -d --name="query-rewrite-microservice" \
  -e QUERY_REWRITE_LLM_ENDPOINT=http://localhost:8009 \
  -e https_proxy=${https_proxy} \
  -e http_proxy=${http_proxy} \
  -e no_proxy=${no_proxy} \
  --net=host \
  --ipc=host \
  opea/query-rewrite:latest
```

### Verify the Query Rewrite Microservice

#### Check Status

```bash
curl http://localhost:6626/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

##### Basic Query Rewrite

```bash
curl http://localhost:6626/v1/query_rewrite \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text": "What is RAG?"}'
```

**Example Output:**
```json
{
  "text": "What is Retrieval Augmented Generation (RAG)?",
  "metadata": {
    "original_query": "What is RAG?",
    "rewritten": true
  }
}
```

##### Query Rewrite with History Context

When `history_id` is provided and chat history exists, the query will be contextualized:

```bash
curl http://localhost:6626/v1/query_rewrite \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"text": "How does it work?", "history_id": "abc123"}'
```
