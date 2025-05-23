# OPEA ERAG Dataprep Guardrail Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Dataprep Guardrail microservice runs scanners on incoming documents and links destined for the dataprep pipeline. It ensures data safety by checking inputs before they proceed to the next stage (e.g., vector database ingestion), informing users whether their uploaded documents or links have passed the scan or have been blocked by the guard. Acting as a protective layer, it prevents invalid or harmful data from propagating downstream in the system.

This microservice implements [LLM Guard](https://llm-guard.com/) scanners, including:
- [BanCode](https://llm-guard.com/input_scanners/ban_code/)
- [BanCompetitors](https://llm-guard.com/input_scanners/ban_competitors/)
- [BanSubstrings](https://llm-guard.com/input_scanners/ban_substrings/)
- [BanTopics](https://llm-guard.com/input_scanners/ban_topics/)
- [Code](https://llm-guard.com/input_scanners/code/)
- [Gibberish](https://llm-guard.com/input_scanners/gibberish/)
- [InvisibleText](https://llm-guard.com/input_scanners/invisible_text/)
- [Language](https://llm-guard.com/input_scanners/language/)
- [PromptInjection](https://llm-guard.com/input_scanners/prompt_injection/)
- [Regex](https://llm-guard.com/input_scanners/regex/)
- [Secrets](https://llm-guard.com/input_scanners/secrets/)
- [Sentiment](https://llm-guard.com/input_scanners/sentiment/)
- [TokenLimit](https://llm-guard.com/input_scanners/token_limit/)
- [Toxicity](https://llm-guard.com/input_scanners/toxicity/)

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