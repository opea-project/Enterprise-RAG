# Intel® AI for Enterprise RAG Documentation

Welcome to the Intel® AI for Enterprise RAG documentation! This repository contains detailed guides and references for the Intel® AI for Enterprise RAG project.

## Contents

### Deployment and Configuration

- **[minimum_requirements.md](minimum_requirements.md)**
  Minimum hardware requirements for deploying Intel® AI for Enterprise RAG, including the limited single-user deployment option (32 cores / 64 GB RAM).

- **[cluster_deployment_guide.md](cluster_deployment_guide.md)**
  Step-by-step guide for deploying Kubernetes clusters for Intel® AI for Enterprise RAG with both single-node and multi-node configurations.

- **[eks_deployment.md](eks_deployment.md)**
  Guide for deploying Intel® AI for Enterprise RAG on Amazon Elastic Kubernetes Service (EKS).

- **[application_deployment_guide.md](application_deployment_guide.md)**
  Complete instructions for deploying the Intel® AI for Enterprise RAG application on prepared Kubernetes infrastructure.

- **[infrastructure_components_guide.md](infrastructure_components_guide.md)**
  Guide for installing additional infrastructure components like Gaudi operator, CSI drivers, and Velero on Kubernetes clusters.

- **[advanced_configuration.md](advanced_configuration.md)**
  Advanced configuration options for pipelines, multi-node support, AI models, performance tuning, and additional settings.

- **[configure_pipeline.md](configure_pipeline.md)**
  Guide for configuring Intel® AI for Enterprise RAG processing pipelines and workflow customization.

- **[switching_pipelines.md](switching_pipelines.md)**
  Guide for switching between the ChatQA and upload-optimized pipeline configurations.

- **[multilingual_support.md](multilingual_support.md)**
  Guide for enabling multilingual embedding, reranking, and LLM support in Intel® AI for Enterprise RAG, including remote model endpoint configuration.

- **[building_images.md](building_images.md)**
  Guide for building Docker images locally for Intel® AI for Enterprise RAG components and pushing them to registries.

- **[debug_tool.md](debug_tool.md)**
  Guide for using the Intel® AI for Enterprise RAG Debug Tool to collect comprehensive diagnostic information from your Kubernetes cluster for troubleshooting deployment issues.



### Backup and Recovery

- **[backup.md](backup.md)**
  Comprehensive guide for configuring backup functionality with Velero, creating backups, and restoring user data and configurations.

- **[backup_storage_configuration.md](backup_storage_configuration.md)**
  Instructions for configuring storage including external kind for backup functionality with Velero.

### Performance, Accuracy and Monitoring

- **[performance_tuning_tips.md](performance_tuning_tips.md)**
  Best practices and optimization techniques for improving Intel® AI for Enterprise RAG system performance.

- **[accuracy_tuning_tips.md](accuracy_tuning_tips.md)**
  Advanced techniques for improving Intel® AI for Enterprise RAG system accuracy.

- **[telemetry.md](telemetry.md)**
  Monitoring, logging, and observability setup for Intel® AI for Enterprise RAG deployments with metrics collection.

### Security and Authentication

- **[multifactor_authentication.md](multifactor_authentication.md)**
  Configuration guide for implementing multi-factor authentication in Intel® AI for Enterprise RAG systems.

- **[ad_federation_on_keycloak.md](ad_federation_on_keycloak.md)**
  Instructions for configuring Keycloak user federation using Microsoft Active Directory for enterprise authentication.

### Integrations

- **[sso_and_sharepoint_integration.md](sso_and_sharepoint_integration.md)**
  Guide covering Single Sign-On configuration using Microsoft Entra ID with Keycloak, and SharePoint Online integration for document ingestion into the knowledge base.

### Service Mesh and Security

- **[istio.md](istio.md)**
  Service mesh configuration and management using Istio for Intel® AI for Enterprise RAG microservices architecture.

- **[tdx.md](tdx.md)**
  Instructions for running Intel® AI for Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX) for enhanced security and confidential computing.

### User Interface

- **[UI_features.md](UI_features.md)**
  Comprehensive guide to Intel® AI for Enterprise RAG user interface features, functionality, and usage instructions.

### Reference Documentation

- **[docker_images_list.md](docker_images_list.md)**
  Complete reference of Docker images used in Intel® AI for Enterprise RAG deployments with version information and usage details.

### Architecture

- **[microservices_architecture.png](microservices_architecture.png)**
  Visual diagram showing all the Intel® AI for Enterprise RAG microservices architecture and component relationships.

Each document contains step-by-step instructions with accompanying screenshots where applicable.
