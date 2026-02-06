# OPEA ERAG Namespace Status Watcher Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview

The OPEA ERAG Namespace Status Watcher microservice provides Kubernetes namespace monitoring functionality. It queries the Kubernetes API to retrieve and report the status of all resources deployed in a specified namespace.

### Features

- Real-time status monitoring of Kubernetes resources
- Generic namespace monitoring via configuration
- Comprehensive resource discovery and reporting
- GMC-compatible status format
- Health check endpoint

## 🔗 Related Components

This service integrates with other OPEA ERAG components:
- Provides status information for audio namespace
- Can be deployed alongside any ERAG microservice deployment
- Accessible through NGINX reverse proxy for centralized status monitoring

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2026 Intel Corporation. All rights reserved.