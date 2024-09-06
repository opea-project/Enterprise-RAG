# OPEA VectorStore
This code implements an interface for connecting to multiple vector store databases. Unified vector store interface allows multiple services to use one storage communication class. This code is not meant to be used as a standalone service, rather as a part for services that require database communication such as ingestion service or retriever service.

This readme shows how to:
- Run an example database server
- Prepare VectorStore Configuration for selected database
- Use VectorStore with selected database

#### Support Matrix

Support for specific vector databases:

| Vector Database    |  Status   |
| -------------------| --------- |
| [REDIS](#redis)    | &#x2713;  |
| [MILVUS](#milvus)  | &#x2717;  |
| [QDRANT](#qdrant)  | &#x2717;  |

## Getting Started

This code is intended to use by other services as an interface to a selected vector store database.

### Prerequisites
If running locally, install python requirements:

```bash
pip install -r impl/requirements.txt
```

Since this is a library not intended to be running separatly, there is no separate Dockerfile. If you want to see an example usage, check code under `ingestion` or `retriever` folders.

### Vector Store Database Endpoint

If you don't run any vector database yet, you can utilize one of already prepared example `docker-compose.yml` files. This will spin up a database instance that you can use for running OPEA.

#### Redis

For more information on this database, refer to https://redis.io/solutions/vector-search/

To run an instance of this database, run the following code:
```bash
cd impl/redis
docker compose up -d
```
To configure VectorStore to use Redis, please refer to [RedisVectorStore](#redisvectorstore).

#### Milvus

For more information on this database, refer to https://milvus.io/

To run an instance of this database, run the following code:
```bash
cd impl/milvus
docker compose up -d
```

To configure VectorStore to use Milvus, please refer to [MilvusVectorStore](#milvusvectorstore).

#### Qdrant

For more information on this database, refer to  https://qdrant.tech/

To run an instance of this database, run the following code:
```bash
cd impl/qdrant
docker compose up -d
```

To configure VectorStore to use Qdrant, please refer to [QdrantVectorStore](#qdrantvectorstore).

## VectorStore implementations

To use VectorStore with a specific database, you should not only select it as shown in the [example usage](#example-usage). Based on available endpoints defined in the [support matrix](#support-matrix) each database endpoint requires some minimum configuration. Configuration parameters for individual databases are shown below.

### RedisVectorStore

Configuration parameters:
`REDIS_URL` - full url for Redis database endpoint (not set by default)
or individual parts of the connection string:
`REDIS_HOST` - Hostname or IP Address of the endpoint (default: `localhost`)
`REDIS_PORT` - Port of the endpoint (default: `6379`)
`REDIS_SSL` - Schema to use, if `true` is passed, `rediss://` schema is used (default: `false`)
`REDIS_USERNAME` (Optional) - Database username (not set by default)
`REDIS_PASSWORD` (Optional) - Database password (not set by default)

### QdrantVectorStore

Configuration parameters:
`QDRANT_URL` - full url for Qdrant database endpoint (not set by default)
or individual parts of the connection string:
`QDRANT_HOST` - Hostname or IP Address of the endpoint (default: `localhost`)
`QDRANT_PORT` - Port of the endpoint (default: `6333`)

Default schema is `http`.

### MilvusVectorStore

Configuration parameters:
`MILVUS_URL` - full url for Qdrant database endpoint (not set by default)
or individual parts of the connection string:
`MILVUS_HOST` - Hostname or IP Address of the endpoint (default: `localhost`)
`MILVUS_PORT` - Port of the endpoint (default: `19530`)

Default schema is `http`.

### Example usage

```bash
cd impl/redis
docker compose up -d
```

```bash
export REDIS_URL='redis://localhst:6379'
```

```python
from comps.vectorstores.utils.opea_vectorstore import OPEAVectorStore

  vector_store = "redis"
  x = OPEAVectorStore(vector_store)

  x.search(...)
  x.add_text(...)
```

## VectorStore methods

This class offers two methods:

### search(EmbedDoc) -> SearchedDoc
This method allows to search the vector store for similar vectors to the embedding that is passed. Input is an `EmbedDoc` class that included the text embedding for the text query. Based on the predefined embedding, embedding vectors along with the corresponding text is returned. Internal search type and settings are included in the `EmbedDoc` object.

Based on EmbedDoc's `search_type` setting, following methods are passed to individual database implementation (some, might not be available for selected databases):
- `similarity_search_by_vector`
- `similarity_search_with_relevance_scores`
- `max_marginal_relevance_search`

### add_texts(List[EmbedDoc]) -> List[EmbedDoc]
This method inserts data directly into the selected vector store database.
