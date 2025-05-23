# OPEA ERAG Reranking Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## Overview

The OPEA ERAG Reranking Microservice, powered by reranking models, enhances search relevance by semantically ranking retrieved documents. This microservice takes a query and a collection of documents as input and reorders them based on their semantic relevance to the query, significantly improving search accuracy.

## Support Matrix

| Model server name          |  Status   |
| ---------------------------| --------- |
| Torchserve                 | &#x2713;  |

## 🔗 Related Components

This service works within the OPEA ERAG ecosystem:
- Retriever service to obtain initial document candidates
- LLM service for generating final responses

## License
OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.