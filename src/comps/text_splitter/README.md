# Text Splitter Microservice

This microservice is designed to split received text into chunks. Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

## Support Matrix

Supported splitter algorithms:

| Algorithm | Class                                                                 |
|----------------|------------------------------------------------------------------|
| RecursiveCharacterTextSplitter   | [Splitter](./utils/splitter.py)                |
| SemanticChunker                  | [SemanticSplitter](./utils/splitter.py)        |


## Configuration options

Configuration is currently done via environment variables.

| Environment Variable             | Default Value             | Description                                                                                      |
|----------------------------------|---------------------------|--------------------------------------------------------------------------------------------------|
| `OPEA_LOGGER_LEVEL`              | `INFO`                    | Microservice logging output level                                                                |
| `TEXT_SPLITTER_USVC_PORT`             | `9399`                    | (Optional) Text Splitter microservice port                                                            |
| `CHUNK_SIZE`                     | `1500`                    | Size of chunks that the data is split into for further processing                                |
| `CHUNK_OVERLAP`                  | `100`                     | Size of chunks overlapping                                                                       |
| `USE_SEMANTIC_CHUNKING`          | `False`                   | Choose if semantic chunking should be used                                                       |
| `EMBEDDING_MODEL_NAME`           | `BAAI/bge-large-en-v1.5`  | Embedding model name for semantic chunking                                                       |
| `EMBEDDING_MODEL_SERVER`         | `torchserve`              | Model server for embeddings used in semantic chunking                                            |
| `EMBEDDING_MODEL_SERVER_ENDPOINT`| `http://localhost:8090`   | Model server endpoint for embeddings used in semantic chunking                                   |
| `SEMANTIC_CHUNK_PARAMS`          | `{}`                      | Add semantic chunking parameters such as buffer_size, add_start_index, etc. Check Langchain documentation for SemanticChunker for reference. |

For semantic chunking, we are using TorchServe embeddings by default, but you can set it to one of your choice. To enable this functionality, you'll need to set up a separate [Embeddings](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/tree/main/src/comps/embeddings/impl/model-server) instance and configure the following environment variables: `EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_SERVER, EMBEDDING_MODEL_SERVER_ENDPOINT`. Once `use_semantic_chunking` is set to `True`, the text_splitter microservice will automatically connect to this instance using the configured endpoint to generate embeddings for semantic chunking operations.

## Getting started

This microservice requires access to external network services for example for downloading models for parsing specific file formats for text extraction.

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
python opea_text_splitter_microservice.py
```

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/text_splitter:latest -f comps/text_splitter/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

```bash
docker run -d --name="text_splitter" --env-file comps/text_splitter/impl/microservice/.env -p 9399:9399 opea/text_splitter:latest
```

### Example input

```bash
curl -X POST -H "Content-Type: application/json"  http://localhost:9399/v1/text_splitter  \
     -d '{"loaded_docs":[{"text":"Example DomainThis domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.More information...","metadata":{"url":"https://example.com/","filename":"index.html","timestamp":1748520579.4694135}}]}'
```

### Example output

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
