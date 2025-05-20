# OPEA ERAG OVMS Embedding Model Server

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG OVMS Embedding Model Server hosts embedding models using OpenVINO™ Model Server (OVMS), providing a scalable and efficient endpoint for generating vector embeddings from text or documents. It serves as the backend for the ERAG Embedding Microservice.

[OVMS](https://github.com/openvinotoolkit/model_server) is an open-source model server that provides a scalable and efficient solution for deploying deep learning models in production environments. It is built on top of the OpenVINO™ toolkit, which enables optimized inference across a wide range of hardware platforms.

For detailed information and practical examples of how to use OpenVINO Model Server (OVMS), please refer to the OVMS documentation on the official [OpenVINO Toolkit GitHub page](https://github.com/openvinotoolkit/model_server/blob/main/docs/home.md).

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- OPEA ERAG Embedding Microservice sends requests to this model server to obtain embeddings
- Retriever & Reranker Microservices use embeddings generated here for improved search relevance

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.
