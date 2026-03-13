# OPEA ERAG Docsum Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Docsum microservice is responsible for scheduling summarization pipelines for the documents.

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- OPEA ERAG Text Extractor, Text Compression and Text Splitter load the input data and prepare it before summarization.
- OPEA ERAG LLM Microservice is responsible for connecting to VLLM model server to run the inference on LMM model.

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2026 Intel Corporation. All rights reserved.