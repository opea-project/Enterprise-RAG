# Hierarchical Dataprep Microservice

Hierarchical indices in an advanced Retrieval-Augmented Generation (RAG) technique that involves a structured indexing approach where data is organized in a multi-level hierarchy to improve the efficiency and relevance of information retrieval. This method is particularly useful when dealing with large-scale or complex datasets, as it allows the retrieval system to narrow down the search space progressively. This dataprep microservice implementation supports a two-level hierarchy where the first level stores pagewise summaries whereas the next level stores actual page content chunks. Each user query is processed by retrieving the k-nearest page summaries from level one followed by retrieval of corresponding page content chunks from level two. 

This microservice is designed to extract text from data sent for processing. That data can be sent in form of .pdf files for further processing. The following operations are performed on the uploaded files.
* The file is read as a list of pages.
* Summaries are generated for individual pages.
* Pages are then broken down into chunks.
* Both summaries as well as chunks are returned as the Result.

The Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

# Support Matrix

This microservice supports .pdf files only.

## Configuration options

Configuration is currently done via environment variables.

| Environment Variable    | Default Value     | Description                                                                                      |
|-------------------------|-------------------|--------------------------------------------------------------------------------------------------|
| `CHUNK_SIZE`            | `1000`            | Size of chunks that the data is split into for further processing                                |
| `CHUNK_OVERLAP`         | `200`             | Size of chunks overlapping                                                                       |
| `VLLM_SERVER_ENDPOINT`         | `http://localhost:8008`            | VLLM server endpoint url for summary generation                                            |
| `SUMMARY_MODEL_NAME`| `Intel/neural-chat-7b-v3-3`            | LLM to be used for summary generation                                          |
| `MAX_NEW_TOKENS`           | `100`| Max new tokens for summary generation                                                                  |
| `UPLOAD_PATH`           | `/tmp/opea_upload`| Path to where the data is saved                                                                  |
| `DATAPREP_USVC_PORT`    | `9399`              | (Optional) Dataprep microservice port |

By default, files are saved to a directory under this container. Save path can be changed by setting the `UPLOAD_PATH` environment variable. It is advised to mount an additional volume for the files saved by dataprep. Files are persisted as a point in time reference to the data that is embedded and ultimately ingested into the vector database. 

## Getting started

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
python opea_hierarchical_dataprep_microservice.py
```

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/hierarchical_dataprep:latest -f comps/hierarchical_dataprep/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

```bash
docker run -d --name="hierarchical-dataprep" --env-file comps/hierarchical_dataprep/impl/microservice/.env -p 9399:9399 opea/hierarchical_dataprep:latest
```

### Example input

Hierarchical Dataprep microservice as an input accepts a json containing .pdf files encoded in base64. Example requests can be found in followings paragraphs.

#### File(s) dataprep

Files have to be encoded into Base64. This cURL format allows sending more data than using `-d`.

```bash
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:9399/v1/hierarchical_dataprep <<JSON_DATA
{
  "files": [
    {
      "filename": "ia_spec.pdf",
      "data64": "$(base64 -w 0 ia_spec.pdf)"
    }
  ]
}
JSON_DATA
```

### Example output

As mentioned above, for each file, summaries are generated for pages and then the page is broken down into chunks.
Text is chunked depenting on `CHUNK_SIZE` and `CHUNK_OVERLAP` parameters. Here's a sample response for a file with 2 pages. Note that the summary docs have `summary: 1` whereas the chunk docs have `summary: 0`.

```json
{
  "docs": [
    {
      "text": "page 0 summary",
      "metadata": {
        "doc_id": "abcdef",
        "page": 0,
        "summary": 1,
      }
    },
    {
      "text": "page 1 summary",
      "metadata": {
        "doc_id": "abcdef",
        "page": 1,
        "summary": 1,
      }
    },
    {
      "text": "page 0 chunk 0",
      "metadata": {
        "doc_id": "abcdef",
        "page": 0,
        "summary": 0,
      }
    },
    {
      "text": "page 0 chunk 1",
      "metadata": {
        "doc_id": "abcdef",
        "page": 0,
        "summary": 0,
      }
    },
    {
      "text": "page 1 chunk 0",
      "metadata": {
        "doc_id": "abcdef",
        "page": 1,
        "summary": 0,
      }
    },
    {
      "text": "page 1 chunk 1",
      "metadata": {
        "doc_id": "abcdef",
        "page": 1,
        "summary": 0,
      }
    }
  ]
}
```
