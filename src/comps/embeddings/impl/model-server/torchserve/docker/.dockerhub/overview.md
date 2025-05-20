# OPEA ERAG TorchServe Embedding Model Server

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG TorchServe Embedding Model Server hosts embedding models using TorchServe, providing a scalable and efficient endpoint for generating vector embeddings from text or documents. It serves as the backend for the ERAG Embedding Microservice.

[TorchServe](https://pytorch.org/serve/) is a lightweight, scalable, and easy-to-use model serving library for PyTorch models. It provides a RESTful API for serving trained models, allowing users to deploy and serve their models in production environments. Moreover, Torchserve supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- OPEA ERAG Embedding Microservice sends requests to this model server to obtain embeddings
- Retriever & Reranker Microservices use embeddings generated here for improved search relevance

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.
