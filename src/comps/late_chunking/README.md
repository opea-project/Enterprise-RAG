# Late Chunking Microservice

The Late Chunking Microservice implements an advanced text processing technique that improves the quality of document embeddings for retrieval-augmented generation (RAG) systems. Traditional chunking methods split text first and then embed each chunk independently, which can lose important contextual information at chunk boundaries. Late chunking addresses this by first encoding the entire document to obtain token-level embeddings, then intelligently chunking the document and applying pooling operations to create semantically richer chunk embeddings.

This implementation is based on the Late Chunking technique developed by Jina AI. The original repository can be found at [https://github.com/jina-ai/late-chunking](https://github.com/jina-ai/late-chunking/tree/main).


**Key Features**

- **Context-Aware Chunking**: Preserves semantic context across chunk boundaries by processing the full document before splitting.
- **Token-Level Embeddings**: Leverages complete document context for more accurate embeddings.
- **Intelligent Pooling**: Applies advanced pooling strategies to create high-quality chunk representations.
- **Seamless Integration**: Works with existing embedding microservices through a standardized interface.
- **Optimized for RAG**: Specifically designed to enhance retrieval accuracy in RAG pipelines.

## Table of Contents

1. [Late Chunking Microservice](#late-chunking-microservice)
2. [Configuration Options](#configuration-options)
3. [Chunking Strategies](#chunking-strategies)
   - 3.1. [Fixed Strategy](#fixed-strategy)
   - 3.2. [Sentences Strategy](#sentences-strategy)
4. [Getting Started](#getting-started)
   - 4.1. [Prerequisite: Start Embedding Microservice](#prerequisite-start-embedding-microservice)
   - 4.2. [🚀 Start Late Chunking Microservice with Python (Option 1)](#-start-late-chunking-microservice-with-python-option-1)
     - 4.2.1. [Install Requirements](#install-requirements)
     - 4.2.2. [Start Microservice](#start-microservice)
   - 4.3. [🚀 Start Late Chunking Microservice with Docker (Option 2)](#-start-late-chunking-microservice-with-docker-option-2)
     - 4.3.1. [Build the Docker Image](#build-the-docker-image)
     - 4.3.2. [Run the Docker Container](#run-the-docker-container)
   - 4.4. [Verify the Late Chunking Microservice](#verify-the-late-chunking-microservice)
     - 4.4.1. [Check Status](#check-status)
     - 4.4.2. [Sending a Request](#sending-a-request)
       - 4.4.2.1. [Example Input](#example-input)
       - 4.4.2.2. [Example Output](#example-output)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)
     - 5.1.1. [Tests](#tests)
6. [Acknowledgment](#acknowledgment)

## Configuration Options

The configuration for the Late Chunking Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable        | Description                                                                |
|-----------------------------|----------------------------------------------------------------------------|
| `LATE_CHUNKING_USVC_PORT`   | The port of the microservice, by default 8003                              |
| `EMBEDDING_ENDPOINT`        | The endpoint of the embedding microservice, e.g., "http://embedding-svc:6000/v1/embeddings" |
| `EMBEDDING_MODEL_NAME`      | The name of the embedding model to use, e.g., "jinaai/jina-embeddings-v2-base-en" |
| `CHUNK_SIZE`                | The target chunk size in tokens, by default 512                           |
| `CHUNK_OVERLAP`             | The number of tokens to overlap between consecutive chunks, by default 0  |
| `LATE_CHUNKING_STRATEGY`    | The chunking strategy to use: "fixed" or "sentences", by default "fixed"  |
| `OPEA_LOGGER_LEVEL`         | The logging level for the microservice (INFO, DEBUG, WARNING, ERROR), by default "INFO" |

## Chunking Strategies

The microservice supports two chunking strategies via `LATE_CHUNKING_STRATEGY`:

- **`fixed`** (default): Token-based chunking with fixed size. Chunks may split mid-sentence. Best for consistent chunk sizes.
- **`sentences`**: Sentence-aware chunking that preserves sentence boundaries. Chunk sizes vary. Best for semantic coherence.

Both strategies support `CHUNK_SIZE` and `CHUNK_OVERLAP` parameters.

## Getting Started

There're 2 ways to run this microservice:
  - [via Python](#-start-reranking-microservice-with-python-option-1)
  - [via Docker](#-start-retranking-microservice-with-docker-option-2) **(recommended)**

There are 2 ways to run this microservice:
  - [via Python](#-start-late-chunking-microservice-with-python-option-1)
  - [via Docker](#-start-late-chunking-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start Embedding Microservice

The Late Chunking Microservice requires an Embedding microservice to be operational and accessible at the URL specified by the `EMBEDDING_ENDPOINT` environment variable. The embedding microservice must support returning token-level embeddings (pooling vectors) rather than just document-level embeddings.

Follow the instructions in the [embeddings microservice documentation](../embeddings/README.md) to set up and start the embedding service with the `return_pooling` capability enabled.

### 🚀 Start Late Chunking Microservice with Python (Option 1)

To start the Late Chunking microservice, you need to install python packages first.

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
python opea_late_chunking_microservice.py
```

### 🚀 Start Late Chunking Microservice with Docker (Option 2)

#### Build the Docker Image
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/late_chunking:latest -f comps/late_chunking/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container
```bash
docker run -d --name="late-chunking-microservice" \
  --net=host \
  --ipc=host \
  opea/late_chunking:latest
```

If the embedding service is running at a different URL than the default, update the `EMBEDDING_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
docker run -d --name="late-chunking-microservice" \
  -e EMBEDDING_ENDPOINT="http://localhost:6000/v1/embeddings" \
  -e EMBEDDING_MODEL_NAME=jinaai/jina-embeddings-v2-base-en \
  -e CHUNK_SIZE=512 \
  -e CHUNK_OVERLAP=0 \
  -e LATE_CHUNKING_STRATEGY=fixed \
  --net=host \
  --ipc=host \
  opea/late_chunking:latest
```

### Verify the Late Chunking Microservice

#### Check Status

```bash
curl http://localhost:8003/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

The Late Chunking Microservice accepts a list of text documents and returns embeddings for each chunk, preserving the contextual information from the full document.

##### Example Input

```bash
curl http://localhost:8003/v1/late_chunking \
  -X POST \
  -d '{"docs": [{"text": "Deep learning is a subset of machine learning that uses neural networks with multiple layers. These neural networks attempt to simulate the behavior of the human brain—albeit far from matching its ability—allowing it to learn from large amounts of data."}], "chunk_size": 512, "chunk_overlap": 0}' \
  -H 'Content-Type: application/json'
```

##### Example Output

The late chunking microservice outputs a JSON containing embedded chunks with their corresponding text and metadata.
```json
[
  {
    "id": "77623db9276a37daea810d8c2485a6e5",
    "text": "deep learning is a subset of machine learning that uses neural networks with multiple layers. these neural networks attempt to simulate the behavior of the human brain — albeit far from matching its ability — allowing it to learn from large amounts of data.",
    "embedding": [
      -0.36829641461372375,
      -0.8913043737411499,
      -0.00337285571731627,
      "..."
    ],
    "search_type": "similarity",
    "k": 10,
    "distance_threshold": null,
    "fetch_k": 20,
    "lambda_mult": 0.5,
    "score_threshold": 0.2,
    "metadata": {},
    "history_id": null
  }
]
```

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the microservice, including the Docker configuration in the `microservice/` subdirectory.

- `utils/`: This directory contains utility scripts and modules that are used by the Late Chunking Microservice, including the core late chunking implementation.

#### Tests
- `src/tests/unit/late_chunking/`: Contains unit tests for the Late Chunking Microservice components

## Acknowledgment

Special thanks to the authors and contributors of the [Late Chunking technique](https://github.com/jina-ai/late-chunking/tree/main). Their research and open-source work have significantly advanced contextual embedding methods and improved retrieval performance in RAG systems. You can read more about the technique in the original paper:

> Günther, Michael, Mohr, Isabelle, Williams, Daniel J., Wang, Bo, and Xiao, Han.
> *Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models.*
> arXiv preprint arXiv:2409.04701, 2024.
> [https://arxiv.org/abs/2409.04701](https://arxiv.org/abs/2409.04701)
