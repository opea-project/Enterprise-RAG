# Reranking Microservice

The Reranking Microservice, fueled by reranking models, stands as a straightforward yet immensely potent tool for semantic search. When provided with a query and a collection of documents, reranking swiftly indexes the documents based on their semantic relevance to the query, arranging them from most to least pertinent. This microservice significantly enhances overall accuracy. In a text retrieval system, either a dense embedding model or a sparse lexical search index is often employed to retrieve relevant text documents based on the input. However, a reranking model can further refine this process by rearranging potential candidates into a final, optimized order.

## Table of Contents

1. [Reranking Microservice](#reranking-microservice)
2. [Support Matrix](#support-matrix)
3. [Configuration Options](#configuration-options)
4. [Getting Started](#getting-started)
   - 4.1. [Prerequisite: Start Reranking Model Server](#prerequisite-start-reranking-model-server)
   - 4.2. [🚀 Start Reranking Microservice with Python (Option 1)](#-start-reranking-microservice-with-python-option-1)
     - 4.2.1. [Install Requirements](#install-requirements)
     - 4.2.2. [Start Microservice](#start-microservice)
   - 4.3. [🚀 Start Retranking Microservice with Docker (Option 2)](#-start-retranking-microservice-with-docker-option-2)
     - 4.3.1. [Build the Docker Image](#build-the-docker-image)
     - 4.3.2. [Run the Docker Container](#run-the-docker-container)
   - 4.4. [Verify the Reranking Microservice](#verify-the-reranking-microservice)
     - 4.4.1. [Check Status](#check-status)
     - 4.4.2. [Sending a Request](#sending-a-request)
       - 4.4.2.1. [Example Input](#example-input)
       - 4.4.2.2. [Example Output](#example-output)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)
     - 5.1.1. [Tests](#tests)

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server name               |  Status   |
| ---------------------------     | --------- |
| [TEI](./impl/model_server/tei/) | &#x2713;  |
| [Torchserve](./impl/model_server/torchserve/) | &#x2713;  |
| OVMS                            | &#x2717;  |


## Configuration Options

The configuration for the Reranking Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable        | Description                                                                |
|-----------------------------|----------------------------------------------------------------------------|
| `RERANKING_USVC_PORT`       | The port of the microservice, by default 8000                              |
| `RERANKING_SERVICE_ENDPOINT`     | The endpoint of the reranking service, e.g., "http://localhost:6060" |
| `RERANKING_MODEL_SERVER`     | The name of model server chose, e.g. "torchserve" |
| `RERANKING_LATE_CHUNKING_ENABLED` | Flag informing if the late chunking is enabled. Default: False |


## Getting started

There're 2 ways to run this microservice:
  - [via Python](#-start-reranking-microservice-with-python-option-1)
  - [via Docker](#-start-retranking-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start Reranking Model Server
The Reranking Microservice interacts with a rerank model endpoint, which must be operational and accessible at the the URL specified by the `RERANKING_SERVICE_ENDPOINT` env.

Depending on the model server you want to use, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service.

### 🚀 Start Reranking Microservice with Python (Option 1)

To start the Reranking microservice, you need to install python packages first.

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
python opea_reranking_microservice.py
```

### 🚀 Start Retranking Microservice with Docker (Option 2)

#### Build the Docker Image
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/reranking:latest -f comps/reranks/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container
```bash
docker run -d --name="reranking-microservice" \
  --net=host \
  --ipc=host \
  opea/reranking:latest
```

If the model server is running at a different URL than the default, update the `RERANKING_SERVICE_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
docker run -d --name="reranking-microservice" \
  -e RERANKING_SERVICE_ENDPOINT=http://localhost:6060 \
  --net=host \
  --ipc=host \
  opea/reranking:latest
```

### Verify the Reranking Microservice

#### Check Status

```bash
curl http://localhost:8000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

The `top_n` parameter allows you to specify the number of results returned by the reranker model. By default, the reranker returns only the top three result (top_n=3). Adding the top_n parameter enables you to retrieve multiple ranked results, with the option to adjust it as needed.

Additionally, you can pass `rerank_score_threshold` to filter received docs based on the model output. Reranking model returns a similarity distance that is mapped to a float value between 0 and 1 using a sigmoid function. For reranker the higher value, the better similarity to the prompt. If rerank_score_threshold is defined, the microservice will ignore all chunks that returned a score equal or lower than this value.

##### Example Input

```bash
curl http://localhost:8000/v1/reranking \
  -X POST \
  -d '{"user_prompt":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}], "top_n":1, "rerank_score_threshold": 0.02}' \
  -H 'Content-Type: application/json'
```

##### Example Output

The reranking microservice outputs a JSON containing the original user question and a list of relevant documents based on reranked top_n results.
```json
{
  "id": "d5d4102b8dc9414866d9c2ee550c9229",
  "data": {
    "user_prompt": "What is Deep Learning?",
    "reranked_docs": [
      {
        "downstream_black_list": [],
        "id": "22c8b1d78b34945003101708494a24b6",
        "text": "Deep learning is...",
        "metadata": {
          "vector_distance": 0.23,
          "reranker_score": 0.82,
          "citation_id": 1
        }
      }
    ]
  },
  "prompt_template": null
}
```

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the supported reranking service. It includes the `model_server` directory, which contains instructions for setting up and running different model servers, for example TEI.

- `utils/`: This directory contains utility scripts and modules that are used by the Reranking Microservice.

#### Tests
- `src/tests/unit/rerankers/`: Contains unit tests for the Reranking Microservice components
