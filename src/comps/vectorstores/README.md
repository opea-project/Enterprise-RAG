# VectorStore
This code implements an interface for connecting to multiple vector store databases. Unified vector store interface allows multiple services to use one storage communication class. This code is not meant to be used as a standalone service, rather as a part for services that require database communication such as ingestion service or retriever service.

## Table of Contents

1. [VectorStore](#vectorstore)
2. [Support Matrix](#support-matrix)
3. [Getting Started](#getting-started)
   - 3.1. [Database setup](#database-setup)
     - 3.1.1. [Redis](#redis)
     - 3.1.2. [Redis Cluster](#redis-cluster)
   - 3.2. [VectorStore implementations](#vectorstore-implementations)
     - 3.2.1. [ConnectorRedis](#connectorredis)
   - 3.3. [Example usage](#example-usage)
4. [VectorStore methods](#vectorstore-methods)
   - 4.1. [search()](#search)
   - 4.2. [add_texts()](#add_texts)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)

## Support Matrix

Support for specific vector databases:

| Vector Database    |  Status   |
| -------------------| :---------: |
| [REDIS](#redis)    | &#x2713; |
| [REDIS-CLUSTER](#redis-cluster) | &#x2713;  |
| [QDRANT](#qdrant) | Experimental |
| [MSSQL](#microsoft-sql-server) | Experimental |
| [PGVECTOR](#pgvector) | Deployment only |

## Getting Started

This code is intended to use by other services as an interface to a selected vector store database.

### Database setup

If you don't run any vector database yet, you can utilize one of already prepared example `docker-compose.yml` files. This will spin up a database instance that you can use for storing vector data.

#### Redis

For more information on this database, refer to https://redis.io/solutions/vector-search/.

To run an instance of this database, run the following code:
```bash
cd impl/redis
docker compose up -d
```
To configure VectorStore to use Redis, please refer to [ConnectorRedis](#ConnectorRedis).

#### Redis Cluster

Configuration is exactly the same as for Redis.

#### Qdrant

For more information on this database, refer to https://qdrant.tech/documentation/

To configure VectorStore to use Qdrant, please refer to [ConnectorQdrant](#connectorqdrant).

#### Microsoft SQL Server

For more information on this database, refer to https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025?view=sql-server-ver17

> [!NOTE]
> Role-based access control (RBAC) for vector databases is not supported when using `mssql`.

For browsing and managing MS SQL it is advised to install [SQL Server Management Studio](https://learn.microsoft.com/en-us/ssms/install/install). Then, to connect to the server directly, use port-forward:

```bash
kubectl port-forward svc/mssql -n vdb --address 0.0.0.0 1433:1433
```

#### PgVector

For more information on this database, refer to https://github.com/pgvector/pgvector

### VectorStore implementations

To use VectorStore with a specific database, you should not only select it as shown in the [example usage](#example-usage). Based on available endpoints defined in the [support matrix](#support-matrix) each database endpoint requires some minimum configuration. Configuration parameters for individual databases are shown below.

#### ConnectorRedis

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

#### ConnectorQdrant

> [!IMPORTANT]
> Qdrant support is EXPERIMENTAL. Backup and restore are not covered.

Configure the full endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| QDRANT_URL           | Not set       | Full URL for the Qdrant endpoint, takes precedence over QDRANT_HOST/QDRANT_HTTPS |

Or use more specific configuration for endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| QDRANT_HOST          | localhost     | Hostname or IP Address of the Qdrant endpoint                                |
| QDRANT_PORT          | 6333          | REST port of the Qdrant endpoint                                             |
| QDRANT_GRPC_PORT     | 6334          | gRPC port of the Qdrant endpoint                                             |
| QDRANT_PREFER_GRPC   | false         | Use gRPC instead of REST where the client supports it                        |
| QDRANT_HTTPS         | false         | Use `https` instead of `http`                                                |
| QDRANT_TIMEOUT       | Not set       | Client timeout in seconds (Optional)                                         |
| QDRANT_API_KEY       | Not set       | The only API key the connector reads, must be provided through a Secret. The deployment decides which privilege level a pod gets: writers receive the read-write key, the retriever receives the read-only key under this same name |

Collection and storage settings:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| QDRANT_COLLECTION_NAME | Not set     | Collection name. When not set, it is derived from `EMBEDDING_MODEL_NAME`, `VECTOR_ALGORITHM`, `VECTOR_DATATYPE`, `VECTOR_DISTANCE_METRIC` and `VECTOR_DIMS` |
| QDRANT_ON_DISK_VECTORS | true        | Keep dense vectors on disk instead of prefaulting them into the page cache   |
| QDRANT_ON_DISK_PAYLOAD | true        | Keep payloads on disk                                                        |
| QDRANT_HNSW_ON_DISK  | false         | Keep the HNSW graph on disk. Not recommended, graph traversal is random access |
| QDRANT_QUANTIZATION  | none          | `none` or `int8` |
| QDRANT_QUANTIZATION_QUANTILE | 0.99  | Quantile used to clip outliers when quantizing                               |
| QDRANT_QUANTIZATION_ALWAYS_RAM | true | Keep the quantized vector copy in RAM                                       |

Qdrant supports a smaller set of vector settings than Redis, and rejects the rest with an error at startup rather than mapping them to a nearest equivalent:

| Setting | Accepted on Qdrant | Rejected on Qdrant |
|---------|--------------------|--------------------|
| `VECTOR_ALGORITHM` | `HNSW`, `FLAT` (`FLAT` maps to `hnsw_config.m = 0`, Qdrant brute force search) | `SVS-VAMANA`, which is a Redis-only index type |
| `VECTOR_DISTANCE_METRIC` | `COSINE`, `L2` | `IP`, because Qdrant returns an unbounded raw inner product, so `vector_distance` values and `distance_threshold` cannot be interpreted |
| `VECTOR_DATATYPE` | `FLOAT32`, `FLOAT16` | - |

Changing any of the accepted values changes the derived collection name, so incompatible vectors cannot be mixed.

#### ConnectorMssql

Configure the full endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| MSSQL_URL            | Not set       | Connection string for MS SQL Server |

Or use more specific configuration for endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| MSSQL_HOST           | localhost     | Hostname or IP Address |
| MSSQL_PORT           | 1433          | Default port |
| MSSQL_DB             | 'vdb'         | Default database name |
| MSSQL_USER           | 'edp'         | Database username |
| MSSQL_PASSWORD       | Not set       | Database password |

#### ConnectorPgVector

Configure the full endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| POSTGRES_URL            | Not set       | Connection string for Postgresql |

Or use more specific configuration for endpoint URL:

| Environment Variable | Default Value | Description                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------------|
| POSTGRES_HOST           | localhost     | Hostname or IP Address |
| POSTGRES_PORT           | 5432          | Default port |
| POSTGRES_DB             | 'vdb'         | Default database name |
| POSTGRES_USERNAME       | 'edp'         | Database username |
| POSTGRES_PASSWORD       | Not set       | Database password |

### Example usage

```bash
cd impl/redis
docker compose up -d
```

```bash
export REDIS_URL='redis://localhost:6379'
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
| `similarity_search_with_siblings` | `similarity_search_with_siblings`        | `k`, `distance_threshold`     |

Additional search parameters that can be added to the query to configure the search:
- `k`: The number of nearest neighbors to retrieve from the database. It determines the size of the result set (default: `10`)
- `distance_treshold`: The maximum distance threshold for similarity search by vector. Documents with a distance greater than the threshold will not be considered as matches. The default value is not specified. (default: `None`)

### add_texts()
This method inserts data directly into the selected vector store database. The input is a list of `EmbedDoc` elements. It returns the list of texts saved into a database.

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of clients for different databases along with example docker compose files for running the database services.

- `utils/`: This directory contains utility scripts and modules that are used by the Vector Store. This also included a common connector class and connectors for each supported vector store database.
