# OPEA ERAG LLMs Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG LLMs microservice interfaces with various LLMs to process queries and reranked documents by constructing prompts and performing inference.

### Support Matrix

| Model server name |  Status   |
| ------------------| --------- |
| VLLM              | &#x2713;   |

### Features

- Supports streaming and non-streaming LLM inference

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- OPEA ERAG Prompt Template and Retriever & Reranker microservices are components that build the final prompt for the LLM
- It triggers inference requests with vLLM Model Server running on Intel® Xeon® Processors or Intel® Gaudi® AI Accelerators
- Its input is scanned by OPEA ERAG Input Guardrails (if enabled)
- Its output is scanned by OPEA ERAG Output Guardrails (if enabled)

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2026 Intel Corporation. All rights reserved.