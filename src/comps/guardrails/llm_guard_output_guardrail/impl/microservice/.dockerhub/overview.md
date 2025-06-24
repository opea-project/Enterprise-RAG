# OPEA ERAG Output Guardrail Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Output Guardrail service provides content filtering and and privacy-related capabilities for LLM-generated responses in the Enterprise RAG system. This microservice ensures all output content adheres to content policies, preventing potentially harmful, inappropriate, or inaccurate responses from reaching end users.

This microservice implements [LLM Guard](https://llm-guard.com/) Output Scanners, including:
- [BanSubstrings](https://llm-guard.com/output_scanners/ban_substrings/)
- [BanTopics](https://llm-guard.com/output_scanners/ban_topics/)
- [Bias](https://llm-guard.com/output_scanners/bias/)
- [Code](https://llm-guard.com/output_scanners/code/)
- [Deanonymize](https://llm-guard.com/output_scanners/deanonymize/)
- [JSON](https://llm-guard.com/output_scanners/json/)
- [MaliciousURLs](https://llm-guard.com/output_scanners/malicious_urls/)
- [NoRefusal](https://llm-guard.com/output_scanners/no_refusal/)
- [NoRefusalLight](https://llm-guard.com/output_scanners/no_refusal_light/)
- [ReadingTime](https://llm-guard.com/output_scanners/reading_time/)
- [FactualConsistency](https://llm-guard.com/output_scanners/factual_consistency/)
- [Regex](https://llm-guard.com/output_scanners/regex/)
- [Relevance](https://llm-guard.com/output_scanners/relevance/)
- [Sensitive](https://llm-guard.com/output_scanners/sensitive/)
- [Sentiment](https://llm-guard.com/output_scanners/sentiment/)
- [Toxicity](https://llm-guard.com/output_scanners/toxicity/)
- [URLReachability](https://llm-guard.com/output_scanners/url_reachability/)

### Features

- Real-time filtering of LLM outputs before reaching end users
- Allows to upholds organizational policy compliance

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Pairs with the OPEA ERAG Input Guardrail for complete input/output protection
- Guards OPEA ERAG LLM service against providing inappropriate responses

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.