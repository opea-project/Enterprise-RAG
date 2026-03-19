# VLLM Audio model server

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The VLLM Audio model server converts audio files to text using Whisper or compatible ASR models. It extends base vllm image to include audio related packages.

### Features

- Converts audio files to text using Whisper ASR models
- Supports multiple audio formats (WAV, MP3)
- OpenAI-compatible API interface
- Configurable language detection and model selection

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- OPEA ERAG ASR Microservice sends the requests to it to convert audio files to text.

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2026 Intel Corporation. All rights reserved.