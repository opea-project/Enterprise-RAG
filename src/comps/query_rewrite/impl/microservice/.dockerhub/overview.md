# OPEA ERAG Query Rewrite Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Query Rewrite Microservice is designed to improve retrieval quality in RAG (Retrieval Augmented Generation) pipelines by rewriting user queries. It processes input queries and generates refined versions that are more effective for document retrieval, using a dedicated LLM to rewrite queries in a single call—contextualizing them with conversation history when available and optimizing them for search.

### Key Features

- **Contextualization**: When chat history is available, queries are rewritten to be self-contained by resolving pronouns and references using conversation context (e.g., "How does it work?" → "How does Retrieval Augmented Generation work?")
- **Query Refinement**: Optimizes queries for better retrieval by expanding acronyms (e.g., "RAG" → "Retrieval Augmented Generation"), fixing typos and abbreviations, while preserving proper nouns and technical terms
- **Single LLM Call**: Efficient processing that handles both contextualization and refinement in one request
- **Pipeline Resilience**: On timeout, the original query is passed through unchanged to ensure system reliability

### Support Matrix

| Model server  | Status    |
| ------------- | --------- |
| vLLM          | &#x2713;  |

Default model: `AMead10/Llama-3.2-3B-Instruct-AWQ` (3B parameters, AWQ quantized)

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Chat History Service provides conversation context for query contextualization
- vLLM Model Server performs the actual query rewriting using an LLM
- Retriever Microservice uses the rewritten queries for improved document retrieval
- Embedding Microservice benefits from better queries for more accurate semantic search

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2026 Intel Corporation. All rights reserved.
