# OPEA Ingestion Microservice

This service allows multiple services to save data into a vector database.

This service internally uses VectorStore class which has to be appropriately configureds. For more information on selecting proper vector database and usage please refer to [VectorStore documentation](../vectorstores/README.md).

## Getting started

Since this service is utilizing VectorStore code, you have to configure the undelying implementation by setting an env variable `VECTOR_STORE` along with vector database configuration for the selected endpoint.

### Prerequisites
If running locally, install python requirements:

```bash
pip install -r impl/requirements.txt
```

### Vector Store Support Matrix

Support for specific vector databases:

| Vector Database                             |  Status   |
| --------------------------------------------| --------- |
| [REDIS](../vectorstores/README.md#redis)    | &#x2713;  |
| [MILVUS](../vectorstores/README.md#milvus)  | &#x2717;  |
| [QDRANT](../vectorstores/README.md#qdrant)  | &#x2717;  |

This sample assumes redis as a vector store database. You can run it by [following this documentation](../vectorstores/README.md#redis).

### Running the Ingestion Microservice

Example `docker-compose.yml`:
```
service:
  ingestion:
    build:
      context: .
      dockerfile: ingestion/impl/microservice/Dockerfile
      args: *proxy_args
    environment:
      VECTOR_STORE: redis
      REDIS_URL: 'redis://redis-vector-db'
    container_name: ingestion
    ports:
      - "6120:6120"
```

To run this docker compose file, simply type:
`docker compose build && docker compose up -d`

## Example input

```bash
  curl http://localhost:6120/v1/ingest \
    -X POST \
    -d '{ "text": "What is Intel AVX-512?", "embedding": [...] }' \
    -H 'Content-Type: application/json'
```
## Example output

Output data, if the request is successfull, is the same as input data.
