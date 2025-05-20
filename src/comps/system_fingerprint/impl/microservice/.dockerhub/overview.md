# OPEA ERAG Fingerprint Microservice

Part of the Intel® AI for Enterprise RAG (ERAG) ecosystem.

## 🔍 Overview
The System Fingerprint microservice is responsible for generating and managing unique fingerprints for different systems and giving user ability to store and update component arguments. It enables system-aware behavior in distributed environments by tracking configuration changes, enforcing consistency and preventing repeated invalid values for faster failure responses. All configuration changes are persistently stored in **MongoDB**.

## 🔗 Related Components
The System Fingerprint microservice is tightly integrated with all other components in the Enterprise RAG architecture. It plays a critical role in managing and distributing configuration across the system:
 - UI/API Layer sends updated configuration parameters associated with an unique fingerprint.
 - All Runtime Components (e.g., dataprep, embedding, prompt-template, others) receive and apply component-specific configuration from the fingerprint service. This also ensures they operate with valid parameters (fast failure). 
 - MongoDB acts as the persistent store for all configuration changes and fingerprint metadata, enabling version control, auditing, and rollback capabilities.

## License
OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.