# OPEA ERAG Input Guardrail Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Input Guardrail service provides content filtering and safety validation for user inputs in the Enterprise RAG system. This microservice ensures that all input queries adhere to content policies, preventing potentially harmful, inappropriate, or malicious prompts from reaching the underlying LLM components.

This microservice implements [LLM Guard](https://llm-guard.com/) Input Scanners, including:
- [Anonymize](https://llm-guard.com/input_scanners/anonymize/)
- [BanSubstrings](https://llm-guard.com/input_scanners/ban_substrings/)
- [BanTopics](https://llm-guard.com/input_scanners/ban_topics/)
- [Code](https://llm-guard.com/input_scanners/code/)
- [InvisibleText](https://llm-guard.com/input_scanners/invisible_text/)
- [PromptInjection](https://llm-guard.com/input_scanners/prompt_injection/)
- [Regex](https://llm-guard.com/input_scanners/regex/)
- [Secrets](https://llm-guard.com/input_scanners/secrets/)
- [Sentiment](https://llm-guard.com/input_scanners/sentiment/)
- [TokenLimit](https://llm-guard.com/input_scanners/token_limit/)
- [Toxicity](https://llm-guard.com/input_scanners/toxicity/)

### Features

- Real-time filtering of user inputs/questions before processing
- Multiple content policy enforcement options
- Allows upholding organizational policy compliance
- Protects retrieval system from potential exploits

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Pairs with the OPEA ERAG Output Guardrail for complete input/output protection
- Guards OPEA ERAG LLM microservice from inappropriate inputs

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.