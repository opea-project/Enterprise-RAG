# OPEA ERAG Text Compression Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

This microservice is designed to compress text from loaded documents. Result of this microservice can then be passed to Data Splitter microservice and, later, to Embedding microservice and ultimately persisted in the system.

## Support Matrix

The microservice supports following compression techniques:

| Name | Short description                                                                 |
|----------------|------------------------------------------------------------------|
| header_footer_stripper   | Removes common boilerplate text like footers, confidentiality notices, and signatures to focus on the meaningful content.             |
| ranking_aware_deduplication   | Removes duplicate or near-duplicate content while intelligently preserving the highest-quality version of each segment.             |


## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Text Extractor supplies loaded input data
- Text Splitter service for splitting the loaded data
- Ingestion service for vector database integration
- Embedding service for generating vector representations of documents for semantic search
- EDP Enhanced Dataprep
- Retriever service for accessing processed documents

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.
