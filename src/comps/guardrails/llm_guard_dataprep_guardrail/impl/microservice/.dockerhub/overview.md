# OPEA ERAG Dataprep Guardrail Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Dataprep Guardrail microservice runs scanners on incoming documents and links destined for the dataprep pipeline. It ensures data safety by checking inputs before they proceed to the next stage (e.g., vector database ingestion), informing users whether their uploaded documents or links have passed the scan or have been blocked by the guard. Acting as a protective layer, it prevents invalid or harmful data from propagating downstream in the system.

This microservice implements [LLM Guard](https://protectai.github.io/llm-guard/) scanners, including:
- [BanSubstrings](https://protectai.github.io/llm-guard/input_scanners/ban_substrings/)
- [BanTopics](https://protectai.github.io/llm-guard/input_scanners/ban_topics/)
- [Code](https://protectai.github.io/llm-guard/input_scanners/code/)
- [InvisibleText](https://protectai.github.io/llm-guard/input_scanners/invisible_text/)
- [PromptInjection](https://protectai.github.io/llm-guard/input_scanners/prompt_injection/)
- [Regex](https://protectai.github.io/llm-guard/input_scanners/regex/)
- [Secrets](https://protectai.github.io/llm-guard/input_scanners/secrets/)
- [Sentiment](https://protectai.github.io/llm-guard/input_scanners/sentiment/)
- [TokenLimit](https://protectai.github.io/llm-guard/input_scanners/token_limit/)
- [Toxicity](https://protectai.github.io/llm-guard/input_scanners/toxicity/)

### Features

- Real-time filtering of user-submitted documents and links before next-step processing (ingestion, embedding, etc.)
- Multiple content policy enforcement options
- Protects the dataprep system from potentially harmful data


## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- The ERAG Dataprep service processes only data that has passed the dataprep guardrail scans, ensuring safety and policy compliance before vector search ingestion.


## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.