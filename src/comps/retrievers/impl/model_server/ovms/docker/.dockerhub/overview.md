# OPEA ERAG OVMS NER Model Server

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG OVMS NER Model Server hosts Named Entity Recognition (NER) models using OpenVINO™ Model Server (OVMS), providing a scalable and efficient endpoint for extracting metadata entities (authors, dates, titles) from user queries. It serves as the backend for the ERAG Retriever Microservice's metadata filtering pipeline.

[OVMS](https://github.com/openvinotoolkit/model_server) is an open-source model server that supports efficient inference on Intel hardware using the OpenVINO™ toolkit. A lightweight NER gateway translates KServe v2 inference requests into structured entity annotations used for query-time metadata filtering.

## 🔗 Related Components
- OPEA ERAG Retriever Microservice sends NER inference requests to this model server for metadata-aware query filtering
- Embedding and Reranker Microservices work alongside the retriever to deliver relevant search results

## License
OPEA ERAG is licensed under the Apache License, Version 2.0.
Copyright © 2026 Intel Corporation. All rights reserved.
