# OPEA ERAG Hierarchical Dataprep Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The Hierarchical Dataprep microservice is designed to extract text from data sent for processing and also create summaries for hierarchical indexing. That data can be sent in form of files for scraping and further extraction. Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

### Supported File Types

| File Extension | Loader Class |
|----------------|-------------|
| pdf            | LoadPdf      |

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- VLLM model server for summary creation
- Ingestion service for vector database integration
- Embedding service for generating vector representations of documents for semantic search
- EDP Enhanced Dataprep
- Retriever service for accessing processed documents

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.