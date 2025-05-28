# Retriever Microservice

Retirever searches and retrieves relevant information, documents or data from a database based on a given embedding query. It uses vector search provided by the selected database and performs a query. The query algorithm and configuration should be included in the request to this microservice.

This service internally uses VectorStore class which has to be appropriately configureds. For more information on selecting proper vector database and usage please refer to [VectorStore documentation](../vectorstores/README.md).

## Configuration options

Configuration is done by selecting the desired vector store type. In addition, the specific vector store endpoint connections settings have to be passed.  For more information on selecting proper vector database and usage please refer to [VectorStore documentation](../vectorstores/README.md).

| Environment Variable    | Default Value     | Description                                                                                      |
|-------------------------|-------------------|--------------------------------------------------------------------------------------------------|
| `VECTOR_STORE`          | `redis`           | Vector Store database type                                                                       |
| `RETRIEVER_USVC_PORT`          | `6620`           | (Optional) Retriever microservice port         |
| `USE_HIERARCHICAL_INDICES` | `False`        | Enable/disable Hierarchical Indices Advanced RAG Technique         |

### Vector Store Support Matrix

Support for specific vector databases:

| Vector Database                             |  Status   |
| --------------------------------------------| --------- |
| [REDIS](../vectorstores/README.md#redis)    | &#x2713;  |

## Getting started

Since this service is utilizing VectorStore code, you have to configure the underlying implementation by setting an env variable `VECTOR_STORE` along with vector database configuration for the selected endpoint.

### Prerequisites

To run this microservice, a vector database should be already running. To run one of the [supported vector](#vector-store-support-matrix) databases you can use sample docker-compose files [located here](../vectorstores/impl/).

We offer 2 ways to run this microservice:
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**

### Running the microservice via Python (Option 1)

To freeze the dependencies of a particular microservice, we utilize [uv](https://github.com/astral-sh/uv) project manager. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

Then start the microservice:

```bash
python opea_retriever_microservice.py
```
This sample assumes redis as a vector store database. You can run it by [following this documentation](../vectorstores/README.md#redis).

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/retriever:latest -f comps/retrievers/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name=retriever --network=host --ipc=host --env-file comps/retrievers/impl/microservice/.env opea/retriever:latest
```

### Example input

Retriever microservice as an input accepts a json. The input is required to have an already embedded text query along with query configuration type and parameters.

#### Query parameters

- `text` - contains the text in human readable format that embeddings array was formed from
- `embeddings` - contiants an embedding vector for a query
- `search_type` - configures the type of search algorithm used by the database (default: `similarity`)

Based on the selected `search_type` method, additional arguments should be passed:

| Search type                      | Search method                             | Arguments                     |
| -------------------------------- | ----------------------------------------- | ----------------------------- |
| `similarity`                     | `similarity_search_by_vector`             | `k`                           |
| `similarity_distance_threshold`  | `similarity_search_by_vector`             | `k`, `distance_threshold`     |
Additional search parameters that can be added to the query to configure the search:
- `k`: The number of nearest neighbors to retrieve from the database. It determines the size of the result set (default: `4`)
- `distance_treshold`: The maximum distance threshold for similarity search by vector. Documents with a distance greater than the threshold will not be considered as matches. The default value is not specified. (default: `None`)

An example request can look as follows:

```bash
  curl -v http://localhost:6620/v1/retrieval \
    -X POST \
    -d '{ "text": "What is Intel AVX-512?", "embedding": [0.024471128, 0.047724035, -0.02704641, 0.0013827643], "search_type": "similarity" }' \
    -H 'Content-Type: application/json'
```

Alternatively, you can pass multiple docs but this will limit the retrieval only to the first element.

```bash
  curl http://localhost:6620/v1/retrieval \
    -X POST \
    -d '{ "docs": [ { "text": "What is Intel AVX-512?", "embedding": [0.024471128, 0.047724035, -0.02704641, 0.0013827643], "search_type": "similarity" } ] }' \
    -H 'Content-Type: application/json'
```

### Example output

```bash
  {
    "retrieved_docs": [...],
    "initial_query": "What is Intel AVX-512?",
    "top_n": 1
  }
```

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the retriever service.

- `utils/`: This directory contains scripts that are used by the Retriever Microservice.

The tree view of the main directories and files:
