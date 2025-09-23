# OPEA ERAG Mosec Embedding Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Mosec Embedding Model Server hosts embedding models using [Mosec](https://github.com/mosecorg/mosec) server for an embedding model. It serves as the backend for the ERAG Embedding Microservice.

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- OPEA ERAG Embedding Microservice sends requests to this model server to obtain embeddings
- Retriever & Reranker Microservices use embeddings generated here for improved search relevance

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.
