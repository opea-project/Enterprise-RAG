# Document Summarization Pipeline

This directory contains pipeline configurations for the Document Summarization use case. The pipelines process documents through a sequence of microservices to generate summaries.

## Available Pipelines

| Pipeline                                      | Platform | Description                                                                                       |
|----------------------------------------------|----------|---------------------------------------------------------------------------------------------------|
| `reference-cpu.yaml`                         | Xeon     | A Docsum pipeline powered by the Xeon backend that processes documents through TextExtractor, TextCompression, TextSplitter, and generates summaries using VLLM (CPU) and LLM services. |
| `reference-hpu.yaml`                         | Gaudi    | A Docsum pipeline powered by the Gaudi backend that processes documents through TextExtractor, TextCompression, TextSplitter, and generates summaries using VLLMGaudi (HPU) and LLM services. |
