# OPEA ERAG Late Chunking Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## Overview

The OPEA ERAG Late Chunking Microservice enhances embedding quality by applying chunking after token-level embeddings are generated. This microservice takes documents as input, obtains token embeddings from an embedding service, then intelligently chunks the text and pools the token embeddings to create high-quality chunk representations. This approach preserves contextual information better than traditional "chunk-then-embed" methods.


## 🔗 Related Components

This service works within the OPEA ERAG ecosystem:
- Embedding service to obtain token-level embeddings with pooling layer
- Enhanced Dataprep service to store chunked embeddings in vector database

## License
OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.