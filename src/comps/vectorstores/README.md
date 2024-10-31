# VectorStore
This code implements an interface for connecting to multiple vector store databases. Unified vector store interface allows multiple services to use one storage communication class. This code is not meant to be used as a standalone service, rather as a part for services that require database communication such as ingestion service or retriever service.

## Support Matrix

Support for specific vector databases:

| Vector Database    |  Status   |
| -------------------| --------- |
| [REDIS](#redis)    | &#x2713;  |
| [MILVUS](#milvus)  | &#x2717;  |
| [QDRANT](#qdrant)  | &#x2717;  |

## Getting Started

This code is intended to use by other services as an interface to a selected vector store database.

### Database setup

If you don't run any vector database yet, you can utilize one of already prepared example `docker-compose.yml` files. This will spin up a database instance that you can use for storing vector data.

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

### VectorStore implementations

To use VectorStore with a specific database, you should not only select it as shown in the [example usage](#example-usage). Based on available endpoints defined in the [support matrix](#support-matrix) each database endpoint requires some minimum configuration. Configuration parameters for individual databases are shown below.

#### RedisVectorStore

Configure the full endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| REDIS_URL            | Not set       | Full URL for Redis database endpoint                                        |

Or use more specific configuration for endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| REDIS_HOST           | localhost     | Hostname or IP Address of the Redis endpoint                                |
| REDIS_PORT           | 6379          | Port of the Redis endpoint                                                  |
| REDIS_SSL            | false         | Schema to use, if `true` is passed, `rediss://` schema is used              |
| REDIS_USERNAME       | Not set       | Database username (Optional)                                                |
| REDIS_PASSWORD       | Not set       | Database password (Optional)                                                |

#### QdrantVectorStore

Configure the full endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| QDRANT_URL           | Not set       | Full URL for Qdrant database endpoint                                       |

Or use more specific configuration for endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| QDRANT_HOST          | localhost     | Hostname or IP Address of the Qdrant endpoint                               |
| QDRANT_PORT          | 6333          | Port of the Qdrant endpoint                                                 |


Default schema is `http`.

#### MilvusVectorStore

Configure the full endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| MILVUS_URL           | Not set       | Full URL for Milvus database endpoint                                       |

Or use more specific configuration for endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| MILVUS_HOST          | localhost     | Hostname or IP Address of the Milvus endpoint                               |
| MILVUS_PORT          | 19530         | Port of the Milvus endpoint                                                 |

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

This class offers two main methods:

### search()
This method allows to search the vector store for similar vectors to the embedding that is passed. Input is an `EmbedDoc` class that included the text embedding for the text query. Based on the predefined embedding, embedding vectors along with the corresponding text is returned. Internal search type and settings are included in the `EmbedDoc` object.

Based on the selected `search_type` method, additional arguments should be passed:

| Search type                      | Search method                             | Arguments                     |
| -------------------------------- | ----------------------------------------- | ----------------------------- |
| `similarity`                     | `similarity_search_by_vector`             | `k`                           |
| `similarity_distance_threshold`  | `similarity_search_by_vector`             | `k`, `distance_threshold`     |
| `similarity_score_threshold`     | `similarity_search_with_relevance_scores` | `k`, `score_threshold`        |
| `mmr`                            | `max_marginal_relevance_search`           | `k`, `fetch_k`, `lambda_mult` |

Additional search parameters that can be added to the query to configure the search:
- `k`: The number of nearest neighbors to retrieve from the database. It determines the size of the result set (default: `4`)
- `distance_treshold`: The maximum distance threshold for similarity search by vector. Documents with a distance greater than the threshold will not be considered as matches. The default value is not specified. (default: `None`)
- `score_threshold`: The minimum relevance score required for a document to be considered a match in similarity search with relevance scores (default: `None`)
- `fetch_k`: The number of additional documents to fetch for each retrieved document in max marginal relevance search (default: `20`)
- `lambda_mult`: A parameter that controls the trade-off between relevance and diversity in max marginal relevance search (default: `0.5`)

### add_texts()
This method inserts data directly into the selected vector store database. The input is a list of `EmbedDoc` elements. It returns the list of texts saved into a database. 

## Additional Information
   
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of clients for different databases along with example docker compose files for running the database services.

- `utils/`: This directory contains utility scripts and modules that are used by the Vector Store. This also included a common wrapper class and wrappers for each supported vector store database.

The tree view of the main directories and files:

```bash
.
├── impl
│   ├── milvus
│   │   ├── docker-compose.yml
│   │   ├── opea_milvus.py
│   ├── qdrant
│   │   ├── docker-compose.yml
│   │   ├── opea_qdrant.py
│   ├── redis
│   │   ├── docker-compose.yml
│   │   ├── opea_redis.py
│   └── requirements.txt
├── README.md
└── utils
    ├── opea_vectorstore.py
    └── wrappers
        ├── wrapper_milvus.py
        ├── wrapper.py
        ├── wrapper_qdrant.py
        └── wrapper_redis.py
```
