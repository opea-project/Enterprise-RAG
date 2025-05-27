# OPEA ERAG Language Detection Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Language Detection service identifies and classifies the language. It can be run in 2 modes:

1. Pipeline: This mode adds multilingual support to ChatQnA pipelines. The microservice detects the language of the user's query as well as the LLM generated response to set up a prompt for translation.

2. Standalone: This mode supports standalone translation. The microservice detects the language of the provided text. It then sets up a prompt for translating the provided text from the source language (detected language) to the provided target language.

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.