# OPEA ERAG Text Extractor Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The Text Extractor microservice is designed to extract text from data sent for processing. That data can be sent in form of files and/or links for scraping and further extraction. Result of this microservice can then be passed to text_splitter microservice for splitting into chunks and, later, to embedding microservice in order to ultimately persist in the system.

### Supported File Types

| File Extension | Loader Class |
|----------------|--------------------|
| AsciiDoc       | LoadWithMarkitdown |
| doc, docx      | LoadDoc            |
| txt            | LoadWithMarkitdown |
| json, jsonl    | LoadWithMarkitdown |
| csv            | LoadWithMarkitdown |
| xlsx, xls      | LoadWithMarkitdown |
| pdf            | LoadPdf            |
| html           | LoadWithMarkitdown |
| md             | LoadWithMarkitdown |
| xml            | LoadWithMarkitdown |
| yaml           | LoadWithMarkitdown |
| ppt, pptx      | LoadPpt            |
| tiff, jpg, jpeg, png, svg | LoadImage |

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Text Compression service for compressing loaded data
- Text Splitter service for splitting the loaded data
- Ingestion service for vector database integration
- Embedding service for generating vector representations of documents for semantic search
- EDP Enhanced Dataprep
- Retriever service for accessing processed documents

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.