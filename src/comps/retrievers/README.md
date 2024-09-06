# OPEA Retriever Microservice

Retirever searches and retrieves relevant information, documents or data from a database based on a given embedding query. It uses vector search provided by the selected database and performs a query. The query algorithm and configuration should be included in the request to this microservice.

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

### Running the Retriever Microservice

Example `docker-compose.yml`:
```
service:
  retriever:
    build:
      context: .
      dockerfile: retrievers/impl/microservice/Dockerfile
      args: *proxy_args
    environment:
      VECTOR_STORE: redis
      REDIS_URL: 'redis://redis-vector-db'
    container_name: retriever
    ports:
      - "6620:6620"
```

To run this docker compose file, simply type:
`docker compose build && docker compose up -d`

### Query parameters

- `text` - contains the text in human readable format that embeddings array was formed from
- `embeddings` - contiants an embedding vector for a query
- `search_type` - configures the type of search algorithm used by the database (default: `similarity`)

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

### Example input

Retriever microservice as an input accepts a json. The input is required to have an already embedded text query along with query configuration type and parameters. An example request can look as follows:

FIXME: add working curl example
```bash
  curl http://localhost:6620/v1/retriever \
    -X POST \
    -d '{"text": "What is Intel AVX-512?", "embeddings": [...], "search_type": "similarity"}' \
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
