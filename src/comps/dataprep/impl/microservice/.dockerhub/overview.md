# OPEA ERAG Dataprep Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The Dataprep microservice is designed to extract text from data sent for processing. That data can be sent in form of files and/or links for scraping and further extraction. Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

### Supported File Types

| File Extension | Loader Class |
|----------------|-------------|
| AsciiDoc       | LoadAsciiDoc |
| doc, docx      | LoadDoc      |
| txt            | LoadTxt      |
| json, jsonl    | LoadJson     |
| csv            | LoadCsv      |
| xlsx, xls      | LoadXls      |
| pdf            | LoadPdf      |
| html           | LoadHtml     |
| md             | LoadMd       |
| xml            | LoadXml      |
| yaml           | LoadYaml     |
| ppt, pptx      | LoadPpt      |
| tiff, jpg, jpeg, png, svg | LoadImage |

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Ingestion service for vector database integration
- Embedding service for generating vector representations of documents for semantic search
- EDP Enhanced Dataprep 
- Retriever service for accessing processed documents

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.