# OPEA ERAG Init-Container Service

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## Overview

The OPEA ERAG Init-Container Service is a reusable container image for deployment workflows. It ensures dependent services are ready before proceeding, using readiness checks via `curl` (HTTP) or `kubectl` (Kubernetes). This service streamlines startup sequences and improves reliability in cloud-native environments.

## 🔗 Related Components

Used in deployments that require checking the status of other services before starting.

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.
