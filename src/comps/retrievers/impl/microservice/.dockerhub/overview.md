# OPEA ERAG Retriever Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## Overview

The OPEA ERAG Retriever service fetches the most relevant context from a vector database based on user queries. This microservice is a core component of the RAG pipeline, efficiently retrieving documents that are semantically similar to the input query to provide accurate and contextually relevant responses.
The Retriever searches and fetches relevant information, documents, or data from a database based on an embedding query. It uses vector search as provided by the selected database. The query algorithm and configuration should be included in the request to this microservice.

### Vector Store Support Matrix

Support for specific vector databases:

| Vector Database |  Status   |
| ----------------| --------- |
| REDIS           | &#x2713;  |

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.