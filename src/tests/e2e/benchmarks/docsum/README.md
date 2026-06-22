# DocSum Pipeline Benchmark

End-to-end performance benchmark for the eRAG Document Summarization pipeline. Measures latency, throughput, and scaling characteristics under continuous load.

## Scope

This benchmark targets the full DocSum pipeline path:
```
Client -> APISIX Gateway -> DocSum Microservice -> TextSplitter -> vLLM (map phase, concurrent) -> LLM reduce -> Response (SSE stream)
```

It measures:
- **E2E latency** -- total time from request to final token
- **TTFT** -- time to first token (dominated by map phase)
- **TPOT** -- time per output token (LLM generation speed)
- **Tokens/sec** -- generation throughput

## Prerequisites

- Deployed eRAG cluster with DocSum pipeline active
- Network access (HTTPS) to the eRAG FQDN and Keycloak (or custom `ERAG_DOMAIN_NAME`)
- Python 3.11+ with packages: `pip install -r requirements.txt`
- HuggingFace tokenizer cached locally (or `HF_TOKEN` for download)
- Keycloak credentials: both `KEYCLOAK_ERAG_ADMIN_PASSWORD` and `KEYCLOAK_REALM_ADMIN_PASSWORD`

Export credentials from deployment defaults (if not changed after install):
```bash
source ../../../../../deployment/ansible-logs/default_credentials.txt && export KEYCLOAK_ERAG_ADMIN_PASSWORD=$KEYCLOAK_ERAG_ADMIN_PASSWORD
export KEYCLOAK_REALM_ADMIN_PASSWORD=$(cat ../../../../../deployment/ansible-logs/default_credentials.yaml | grep KEYCLOAK_REALM_ADMIN_PASSWORD | awk '{print $2}')
```

## Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Prepare test documents (downloads pubmed, generates target-size docs)
python3 prepare_pubmed_docs.py

# 3. Generate bearer token (reuse chatqa script)
../chatqa/generate_uat_to_file.sh .bearer 1

# 4. Validate environment
./preflight_check.sh

# 5. Smoke test
./run_smoke.sh
```

## Test documents

Generated from PubMed article abstracts via `prepare_pubmed_docs.py`. The text is scientific/medical prose that exercises the map_reduce summarization pipeline with realistic content.

| File | Tokens | Purpose |
|------|--------|---------|
| docs/pubmed_3k.txt | ~3,000 | Quick smoke test (1 map chunk, <1 min) |
| docs/pubmed_67k.txt | ~67,000 | Standard benchmark (~11 map chunks at CHUNK_SIZE=6500) |
| docs/pubmed_139k.txt | ~139,000 | Stress test (~22 map chunks) |

Source: PubMed article abstracts from the MedRAG dataset (HuggingFace: `MedRAG/pubmed`). Public domain biomedical literature.

To regenerate:
```bash
python3 prepare_pubmed_docs.py --force
```

## Tokenizer

The `-m` flag specifies the HuggingFace model name used for token counting. It must match the model deployed in eRAG so that input/output token counts are accurate.

```bash
# Use the exact model deployed in your eRAG cluster:
python3 benchmark.py -f docs/pubmed_67k.txt -m casperhansen/llama-3-8b-instruct-awq ...
```

The tokenizer is optional -- without the `transformers` package or with `--no-tokenizer`, the benchmark falls back to a word-count approximation (`words * 1.3`).

## Running

### Quick smoke test (~1 min)

```bash
./run_smoke.sh
```

Runs a single request with the small document (3k tokens).

### Duration-based benchmark (recommended)

Sends continuous requests for a fixed time period. Each worker thread loops independently, producing steady load without batching pauses.

```bash
python3 benchmark.py \
    -f docs/pubmed_67k.txt \
    -d 30m \
    -c 16 \
    -m casperhansen/llama-3-8b-instruct-awq \
    -x 67000 \
    --max-tokens 1024 \
    --json-summary
```

### Repetition-based benchmark (quick runs)

Sends a fixed number of batched requests. Useful for quick validation or A/B comparisons.

```bash
python3 benchmark.py \
    -f docs/pubmed_67k.txt \
    -r 3 \
    -c 1 \
    -m casperhansen/llama-3-8b-instruct-awq \
    -o results/my_run.csv \
    --json-summary
```

### Controlling input and output size

Both input and output token counts are configurable for consistent benchmarking:

```bash
# Fixed 67k input tokens, max 1024 output tokens
python3 benchmark.py -f docs/pubmed_139k.txt -x 67000 --max-tokens 1024 -d 30m -c 8 -m <model>

# Fixed 3k input tokens, max 256 output tokens (lighter load)
python3 benchmark.py -f docs/pubmed_67k.txt -x 3000 --max-tokens 256 -d 30m -c 32 -m <model>
```

### benchmark.py arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `-s URL` | `ERAG_DOCSUM_URL` or `https://erag.com/api/v1/docsum` | DocSum API endpoint |
| `-f FILE` | (required) | Document to summarize |
| `-c N` | 1 | Concurrent workers (threads) |
| `-r N` | 3 | Repetitions -- batched mode (mutually exclusive with -d) |
| `-d DURATION` | - | Run for duration: 30m, 1h, 90s -- continuous mode (mutually exclusive with -r) |
| `-t TYPE` | map_reduce | Strategy: map_reduce, stuff, refine |
| `-m MODEL` | `BENCHMARK_TOKENIZER` or llama-3-8b-awq | HuggingFace model for tokenizer (must match deployed model) |
| `-x N` | - | Truncate document to N input tokens |
| `--max-tokens N` | 1024 | Max output tokens per request |
| `-b PATH` | .bearer | Bearer token file |
| `--no-tokenizer` | off | Skip tokenizer, use word-count approximation |
| `-o PATH` | results/docsum_bench_TIMESTAMP.csv | Output CSV |
| `--quiet` | off | Suppress progress output |
| `--json-summary` | off | Print JSON metrics at end |

## Output format

CSV columns: `source_file, concurrency, run, input_tokens, output_tokens, e2e_latency, ttft, tpot, tokens_per_sec, map_chunks, reduce_chunks, error`

With `--json-summary`, a JSON object is printed to stdout after completion with aggregate metrics.

## Model configuration

Models are configured at deployment time via the pipeline resource files. The benchmark assumes eRAG is already deployed with the desired model -- to change the LLM model, redeploy eRAG.
