# OPEA ERAG Enhanced Data Preparation Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Enhanced Data Preparation service provides advanced document processing capabilities for the Enterprise RAG system. Designed to operate alongside other ERAG services, EDP ensures seamless, automated data flow from storage to retriever-ready format.

### Storage Endpoints Support Matrix

Support for storage backends for storing and processing files:

| Storage Endpoints  |  Status   |
| -------------------| --------- |
| MinIO              | &#x2713;  |
| AWS S3             | &#x2713;  |
| AWS S3 Compatible  | &#x2713;  |

### Service Roles

This image serves three main service roles:
- `backend`: file management & REST APIs for managing files, storage sync, etc. 
- `celery`: background task distribution
- _(optional)_ `flower`: web ui for celery tasks
- _(optional)_ `sqs`: queue listener for S3 events if using AWS S3

## 🔗 Related Components

This service works with other components:
- Storage service (MinIO, AWS S3 or S3 compatible) for document persistence
- Ingestion service for vector database integration
- Embedding service for generating vector representations of documents for semantic search
- Retriever service for accessing processed documents

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.