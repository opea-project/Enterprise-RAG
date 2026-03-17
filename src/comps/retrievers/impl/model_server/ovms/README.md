# OVMS NER Model Server

This folder contains the scripts to run a Named Entity Recognition (NER) model with OpenVINO™ Model Server (OVMS) for metadata-aware query filtering in the Retriever microservice.

[OVMS](https://github.com/openvinotoolkit/model_server) is an open-source model server that provides a scalable and efficient solution for deploying deep learning models in production environments. It is built on top of the OpenVINO™ toolkit, which enables optimized inference across a wide range of hardware platforms.

The NER OVMS deployment uses a **dual-process architecture**: OVMS serves the model inference while a lightweight Flask-based NER Gateway handles tokenization, BIO-label post-processing, and entity aggregation. PyTorch is included in the container image because it is required at **export time** (`optimum-cli export openvino`) to convert the HuggingFace model to OpenVINO IR format, but it is **not used at inference time**.

## Table of Contents

- [Architecture](#architecture)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Testing Retriever with OVMS](#testing-retriever-with-ovms)

## Architecture

The NER OVMS container runs two processes:

1. **OVMS** (background): Serves the OpenVINO IR model on internal port 9000 via KServe v2 gRPC/REST protocol.
2. **NER Gateway** (foreground): A Flask HTTP server on port 9001 that:
   - Accepts text input via KServe v2 REST API
   - Tokenizes text using HuggingFace `AutoTokenizer` (no PyTorch required at inference)
   - Forwards token IDs / attention masks to OVMS
   - Decodes BIO labels and aggregates entities
   - Returns structured entity results

**Quantization**: The model is exported to OpenVINO IR format with INT8 weight-only quantization by default (`NER_WEIGHT_FORMAT=int8`), reducing model size ~4x with minimal accuracy loss. FP32 is available via `NER_WEIGHT_FORMAT=fp32`.

## Configuration

### NER OVMS Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NER_MODEL_NAME` | `tanaos/tanaos-NER-v1` | HuggingFace NER model name |
| `NER_WEIGHT_FORMAT` | `int8` | Quantization: `int8` (default) or `fp32` |
| `NER_OVMS_PORT` | `9001` | NER OVMS Port |
| `NER_EXPORT_TIMEOUT` | `600` | Model export timeout (seconds) |
| `HF_TOKEN` | _(unset)_ | HuggingFace API token (for gated models) |

> [!NOTE]
> Retriever-side metadata filtering settings (`METADATA_FILTERING_ENABLED`, `NER_ENDPOINT`, `METADATA_EXTRACTION_MODE`, `METADATA_LANGUAGE`) are configured in the retriever microservice, not here. See the [Retriever README](../../README.md) for details.

### Model: tanaos-NER-v1

[tanaos/tanaos-NER-v1](https://huggingface.co/tanaos/tanaos-NER-v1) is a fine-tuned BERT-based Named Entity Recognition model optimized for metadata extraction from natural language queries. It is the default model used by this deployment.


## Getting Started

### Prerequisite

Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 Start NER OVMS + Retriever with Docker Compose

The docker-compose setup starts both the NER OVMS model server and the retriever microservice:

```bash
cd docker
docker compose up --build -d
```

This starts two services:
- **retriever-ner-ovms** — NER model server on port 9001
- **retriever_usvc** — Retriever microservice on port 6620 (with `network_mode: host`)

The retriever waits for the NER OVMS health check to pass before starting.

To stop:

```bash
cd docker
docker compose down
```

### 🚀 Start NER OVMS Only (via script)

If you want to run only the NER OVMS server (e.g., when the retriever is running separately):

```bash
chmod +x run_ovms.sh
./run_ovms.sh
```

The script initiates a Docker container with the NER OVMS server running on port (`NER_OVMS_PORT`, default: **9001**) for serving NER inference. Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings either by modifying the dotenv file or by exporting environment variables.

### Verify NER OVMS

If you'd like to check whether the endpoint is already running, check the health endpoint:

```bash
curl http://localhost:9001/v2/health/ready
```

Expected output:
```json
{"status": "ready"}
```

Check the model metadata:
```bash
curl http://localhost:9001/v2/models/tanaos-NER-v1
```

Expected output:
```json
{"name": "tanaos-NER-v1", "ready": true, "platform": "openvino"}
```

## Testing Retriever with OVMS

### Test NER Inference Directly

Send a query to the NER OVMS endpoint to verify entity extraction:

```bash
curl -s -X POST http://localhost:9001/v2/models/tanaos-NER-v1/infer \
    -H 'Content-Type: application/json' \
    -d '{"inputs": [{"name": "input_text", "shape": [1], "datatype": "BYTES", "data": ["Show me documents from 2024 by Intel about Gaudi processors"]}]}'
```

Expected output (entities detected — note that `model_version` is always `"1"`):
```json
{
  "model_name": "tanaos-NER-v1",
  "model_version": "1",
  "outputs": [
    {
      "name": "entities",
      "datatype": "BYTES",
      "shape": [3],
      "data": [
        {"entity_group": "DATE", "word": "2024", "score": 0.99, "start": 23, "end": 27},
        {"entity_group": "ORG", "word": "Intel", "score": 0.99, "start": 31, "end": 36},
        {"entity_group": "PRODUCT", "word": "Gaudi", "score": 0.90, "start": 43, "end": 48}
      ]
    }
  ]
}
```

### Test Retriever with Metadata Filtering (End-to-End)

> [!IMPORTANT]
> This test requires Redis with RediSearch running on port `6379` (default). Without it, the retriever will return:
> `"An error while retrieving documents"`
>
> Start it with:
> ```bash
> docker run -d --name edp-redis -p 6379:6379 redis/redis-stack:7.4.0-v2
> ```

#### Seed Test Documents

Use the provided [run_redis_and_seed.sh](run_redis_and_seed.sh) script to start Redis and insert 3 test documents authored by **John Smith** in a single step:

```bash
chmod +x run_redis_and_seed.sh
./run_redis_and_seed.sh
```

```

The script:
1. Starts the `edp-redis`
2. Waits for Redis to be ready
3. Inserts examplary documents

Expected output:
```
[redis] Starting new container 'edp-redis' on port 6379...
[redis] Ready.
[seed] Inserting test documents (DIMS=768)...
  Inserted: erag:a1b2c3...  [Q1 2024 Financial Report]
  Inserted: erag:d4e5f6...  [AI Infrastructure Review Q3 2023]
  Inserted: erag:g7h8i9...  [European Market Outlook 2025]

[seed] Done. 3 documents inserted.
```

The seeded dataset contains documents authored by two people: **John Smith** (2 documents, years 2023–2024) and **Anna Nowak** (1 document, year 2025). The examples below show how the retriever automatically filters results to the right author from a natural-language query — no manual filter construction needed.

First, generate a reusable random embedding (768-dim, matching `VECTOR_DIMS` default):

```bash
EMBEDDING=$(python3 -c "import random,json; print(json.dumps([random.gauss(0,1) for _ in range(768)]))")
```

**Query 1 — Ask about John Smith's reports from 2024:**

```bash
curl -s -X POST http://localhost:6620/v1/retrieval \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"Show me reports by John Smith from 2024\", \"embedding\": $EMBEDDING, \"search_type\": \"similarity\", \"k\": 5}"
```

The retriever extracts `author == "John Smith"` and `creation_date >= 2024-01-01 AND creation_date <= 2024-12-31` from the query text and applies them as Redis filters. Only John Smith's documents from 2024 are returned:

```json
{
  "user_prompt": "Show me reports by John Smith from 2024",
  "top_n": 3,
  "retrieved_docs": [
    {
      "text": "John Smith's Q1 2024 financial report shows revenue growth of 12%.",
      "metadata": {
        "author": "John Smith",
        "file_title": "Q1 2024 Financial Report",
        "creation_date": "1711839600",
        "object_name": "Q1_2024_report.pdf",
        "vector_distance": "1.01984274387"  # Note: The seed script uses random embeddings, so this value has no semantic meaning in presented example
      }
    }
  ]
}
```

> The 2023 document (`AI Infrastructure Review Q3 2023`) is excluded by the date filter, and Anna Nowak's document (`European Market Outlook 2025`) is excluded by the author filter.

**Query 2 — Ask about Anna Nowak's documents:**

```bash
curl -s -X POST http://localhost:6620/v1/retrieval \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"Show me documents by Anna Nowak\", \"embedding\": $EMBEDDING, \"search_type\": \"similarity\", \"k\": 5}"
```

The retriever extracts `author == "Anna Nowak"` and returns only her document, John Smith's documents are completely excluded:

```json
{
  "user_prompt": "Show me documents by Anna Nowak",
  "top_n": 3,
  "retrieved_docs": [
    {
      "text": "Anna Nowak's summary of European market trends and forecasts for 2025.",
      "metadata": {
        "author": "Anna Nowak",
        "file_title": "European Market Outlook 2025",
        "creation_date": "1736892000",
        "object_name": "eu_market_outlook_2025.pdf",
        "vector_distance": "1.01234567890" # Note: The seed script uses random embeddings, so this value has no semantic meaning in presented example
      }
    }
  ]
}
```

Key fields in the response:
- **`user_prompt`** — the original query query received by the retriever.
- **`author`** — extracted from Redis metadata; confirms the NER/regex filter was applied correctly for the requested author
- **`creation_date`** — Unix timestamp (e.g. `1711839600` = 2024-03-31); the date filter limits results to documents from the specified year or period.
- **`vector_distance`** — cosine distance from the query embedding; with random test embeddings it is not semantically meaningful, but metadata filtering works correctly regardless


### Test Retriever without OVMS (Regex-Only Mode)

The NER OVMS container is **optional**. If it is not running (or unreachable), the retriever automatically falls back to regex-based metadata extraction. You can also force this mode explicitly by setting `METADATA_EXTRACTION_MODE=regex_only` or by unsetting `NER_ENDPOINT`.

In regex-only mode, the retriever still extracts metadata such as authors and dates from queries. This works well for structured English queries (e.g., "by John Smith", "from 2024"). However, for genitive forms or queries in other languages—such as Polish ("od Jana Kowalskiego",) NER-based lemmatization is recommended. In these cases, running in hybrid mode with `METADATA_LANGUAGE=pl` will improve extraction accuracy.

### Test Retriever without Metadata Filtering

To disable metadata filtering entirely, set `METADATA_FILTERING_ENABLED=false` in [docker/.env](docker/.env) and restart the retriever. All queries will then perform a plain vector similarity search — no author, date, or title filters are applied.

```bash
# docker/.env
METADATA_FILTERING_ENABLED=false
```

With filtering disabled, the retriever logs will show:

```
Building vector query with filter_expression=None
```

instead of the usual:

```
Building vector query with filter_expression=((@author:("John Smith") ...) | ismissing(@file_id))
```

**Example — same query, no filtering:**

With `METADATA_FILTERING_ENABLED=false`, all 3 seeded documents are returned regardless of author or date. The result set is ranked by vector distance only.


### Full End-to-End Validation Checklist

The examples above test individual components in isolation. 

Comprehensive validation of the full retriever pipeline with metadata filtering (E2E setup) requires:
- **Redis with RediSearch** (`redis-stack:7.4.0-v2`) running on port 6379
- **Document ingestion service** to load test documents with embeddings and metadata into Redis
- **Test documents** with diverse metadata (authors, dates, titles in English and Polish)
- **Multiple query patterns**: author+date filters (EN), Polish genitive name lemmatization, title extraction, and baseline queries without metadata
- **Log verification**: confirm metadata extraction filters appear in retriever logs (`"Filter expression:..."` lines)
- **Polish language testing**: validate `METADATA_LANGUAGE=pl` enables NER-based lemmatization (e.g., "Jana Kowalskiego" → "Jan Kowalski")

For production deployments, ensure your Redis cluster has the RediSearch module enabled and verify hybrid mode fallback behavior (NER failure → automatic regex-only).
