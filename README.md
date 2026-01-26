# Intel® AI for Enterprise RAG

Intel® AI for Enterprise RAG simplifies transforming your enterprise data into actionable insights. Powered by Intel® Xeon® processors and Intel® Gaudi® AI accelerators, it integrates components from industry partners to offer a streamlined approach to deploying enterprise solutions.

## Why use Intel® AI for Enterprise RAG?

Enable intelligent AI experiences that understand your business context:

* **Domain-Specific Intelligence** - Enrich conversations and document processing with your organizational knowledge without training or fine-tuning models
* **Multiple Use Cases** - Support for ChatQ&A for conversational AI and Document Summarization for extracting key insights from documents
* **Rapid Deployment** - Transform enterprise documents into AI-powered experiences in minutes, not months
* **Enterprise-Ready Scale** - Deploy secure, compliant AI solutions that grow with your business needs

## Core Features
* **One-Click Enterprise Deployment** - Fully automated Kubernetes cluster provisioning with Ansible playbooks, supporting both single-node and multi-node configurations with comprehensive infrastructure setup.
* **Optimized AI Hardware Support** - Native support for Intel® Xeon® processors and Intel® Gaudi® AI accelerators with Horizontal Pod Autoscaling (HPA), balloons policy for CPU pinning on NUMA architectures, and performance-tuned configurations.
* **Enterprise-Grade Security & Compliance** - Integrated Identity and Access Management (IAM) with Keycloak, programmable guardrails for fine-grained control, Pod Security Standards (PSS) enforcement for secure enterprise operations, role-based access control for vector databases, and Intel® Trust Domain Extensions (TDX) support for confidential computing.
* **Comprehensive Monitoring & Observability** - Integrated telemetry stack with Prometheus, Grafana dashboards, distributed tracing with Tempo, and centralized logging with Loki for full pipeline visibility.

If you're interested in getting a glimpse of how Intel® AI for Enterprise RAG works, check out following demo.

<br/>
<div align="center">
  <a href="https://www.youtube.com/watch?v=wWcUNle1kkg">
    <img alt="Enterprise RAG Demo ChatQ&A" src="./docs/images/yt_thumbnail.png">
  </a>
</div>
&nbsp;

> [!NOTE]
> The video provided below showcases the beta release of our project. As we've transitioned to next releases, users can anticipate an improved UI design, improved installation process along with other enhancements.

### Pipeline Architecture
Our system consists of two primary processing pipelines, each built on top of a shared microservices architecture. However, only one pipeline can be deployed at once. 

* ChatQnA – enabling retrieval-augmented question answering through conversational interaction.
* Document Summarization (DocSum) – responsible for generating concise summaries from input documents.

The pipeline architecture for ChatQnA is shown below.
For the detailed microservices architecture, refer [here](./docs/microservices_architecture.png).

Document Summarization's pipeline architecture is available [here](./docs/images/architecture_docsum.svg).

<div align="center">
   <img alt="ChatQnA Architecture" src="./docs/images/architecture_chatqna.svg" width="900">
</div>

# Table of Contents <!-- omit from toc -->


1. [Intel® AI for Enterprise RAG](#intel-ai-for-enterprise-rag)
   - [Why use Intel® AI for Enterprise RAG?](#why-use-intel-ai-for-enterprise-rag)
   - [Core Features](#core-features)
     - [Pipeline Architecture](#pipeline-architecture)
2. [Requirements](#requirements)
   - [System Requirements](#system-requirements)
   - [Software Prerequisites](#software-prerequisites)
   - [Hardware Requirements](#hardware-requirements)
     - [Deployment on Xeon only](#deployment-on-xeon-only)
     - [Deployment on Xeon + Gaudi Accelerator](#deployment-on-xeon--gaudi-accelerator)
3. [Getting Started](#getting-started)
   - [Validate Hardware Requirements](#validate-hardware-requirements)
   - [Intel Enterprise RAG Deployment - Standalone](#intel-enterprise-rag-deployment---standalone)
     - [Install a Kubernetes cluster (optional - if you don't have one)](#install-a-kubernetes-cluster-optional---if-you-dont-have-one)
     - [Install infrastructure components (storage, operators, backup tools)](#install-infrastructure-components-storage-operators-backup-tools)
     - [Deploy the Intel® AI for Enterprise RAG application on top of the prepared infrastructure](#deploy-the-intel-ai-for-enterprise-rag-application-on-top-of-the-prepared-infrastructure)
4. [Intel AI Enterprise RAG Deployment - Partner Solutions](#intel-ai-enterprise-rag-deployment---partner-solutions)
   - [Nutanix AI & Intel® AI for Enterprise RAG](#nutanix-ai--intel-ai-for-enterprise-rag)
5. [Documentation](#documentation)
6. [Support](#support)
7. [Publications](#publications)
8. [License](#license)
9. [Security](#security)
10. [Intel's Human Rights Principles](#intels-human-rights-principles)
11. [Model Card Guidance](#model-card-guidance)
12. [Contributing](#contributing)
13. [Trademark Information](#trademark-information)

# Requirements

## System Requirements

| Category            | Details                                                                                                           |
|---------------------|-------------------------------------------------------------------------------------------------------------------|
| Operating System    | Ubuntu 22.04/24.04                                                                                                |
| Hardware Platforms  | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors<br>6th Gen Intel® Xeon® Scalable processors<br>3rd Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator<br>4th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator <br>6th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 3 AI Accelerator|
| Kubernetes Version  | 1.32.9 <br> 1.33.5                                                                  |
| Python              | 3.11                                                                                                              |

## Software Prerequisites
- **Hugging Face Model Access**: Ensure you have the necessary access to download and use the chosen Hugging Face model. Default models can be inspected in [config.yaml](deployment/inventory/sample/config.yaml).
- For **multi-node clusters** CSI driver with StorageClass supporting accessMode ReadWriteMany (RWX) is required. NFS server with CSI driver that supports RWX can be installed via [deployment guide](deployment/README.md).

## Hardware Requirements

These are minimal requirements to run Intel® AI for Enterprise RAG with default settings. In case of more(or less) resources available, feel free to adjust the parameters in the resource configuration files for your chosen pipeline:
- ChatQA: [resources-reference-cpu.yaml](deployment/pipelines/chatqa/resources-reference-cpu.yaml) or [resources-reference-hpu.yaml](deployment/pipelines/chatqa/resources-reference-hpu.yaml)
- Docsum: [resources-reference-cpu.yaml](deployment/pipelines/docsum/resources-reference-cpu.yaml) or [resources-reference-hpu.yaml](deployment/pipelines/docsum/resources-reference-hpu.yaml)

### Deployment on Xeon only
To deploy the solution using Xeon only, you will need access to any platform with Intel® Xeon® Scalable processor that meet below requirements:
-  **logical cores**: A minimum of `88` logical cores
-  **RAM memory**: A minimum of `250GB` of RAM
-  **Disk Space**: `200GB` of disk space is generally recommended, though this is highly dependent on the model size

> [!NOTE]
> By default, Intel® AI for Enterprise RAG uses the NRI plugin for performance optimization. For more info: [NRI plugin](deployment/components/nri-plugin/README.md)

### Deployment on Xeon + Gaudi Accelerator

To deploy the solution on a platform with Gaudi® AI Accelerator you need to have access to instance with minimal requirements:

-  **logical cores**: A minimum of `56` logical cores
-  **RAM memory**: A minimum of `250GB` of RAM though this is highly dependent on database size
-  **Disk Space**: `500GB` of disk space is generally recommended, though this is highly dependent on the model size and database size
-  **Gaudi cards**: `8`
-  **Gaudi driver**: `1.22.1`

# Getting Started

Install the prerequisites.

```sh
cd deployment/
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yaml --upgrade
```
## Validate Hardware Requirements

Before proceeding with the deployment, it's recommended to validate that your hardware meets the requirements for Intel® AI for Enterprise RAG. To perform hardware validation, you need to create an inventory.ini file first.

An example inventory.ini file structure and detailed instructions are provided in the [Cluster Deployment Guide](docs/cluster_deployment_guide.md).

Once you have created the inventory.ini file, you can validate your hardware resources using the validate playbook located at `playbooks/validate.yaml`:

```sh
ansible-playbook playbooks/validate.yaml --tags hardware -i inventory/test-cluster/inventory.ini
```

> [!NOTE]
> If this is a Gaudi deployment, add the additional flag `-e is_gaudi_platform=true`

## Intel AI Enterprise RAG Deployment - Standalone

### Install a Kubernetes cluster (optional - if you don't have one)

Intel® AI for Enterprise RAG offers ansible automation for creating a K8s cluster. If you want to set up a K8s cluster, follow the [Cluster Deployment Guide](docs/cluster_deployment_guide.md).

### Install infrastructure components (storage, operators, backup tools)

The Intel® AI for Enterprise RAG repository offers installation of additional infrastructure components on the deployed K8s cluster:
- **Gaudi_operator** - dedicated for K8s clusters with nodes that use Gaudi AI accelerators
- **CSI drivers** - need to dynamically provision storage for PODs
- **Velero** - installing Velero backup tool

If your K8s cluster requires installing any of these tools, please follow the [Infrastructure Components Guide](docs/infrastructure_components_guide.md).

### Deploy the Intel® AI for Enterprise RAG application on top of the prepared infrastructure

Once you have a K8s cluster with all infrastructure components installed, you can install the Intel® AI for Enterprise RAG application on top of it. Please follow the [Application Deployment Guide](docs/application_deployment_guide.md).

# Intel AI Enterprise RAG Deployment - Partner Solutions

## Nutanix AI & Intel® AI for Enterprise RAG

Follow documentation to deploy Nutanix AI with Intel® AI for Enterprise RAG using the [Nutanix AI Deployment Guide](docs/nutanix/README.md).

# Documentation

Refer to [deployment/README.md](deployment/README.md) or [docs](docs/) for more detailed deployment guide or in-depth instructions on Intel® AI for Enterprise RAG components.

# Support

Submit questions, feature requests, and bug reports on the GitHub Issues page.

# Publications

Feel free to checkout articles about Intel® AI for Enterprise RAG:
* [Securing Enterprise RAG Deployments](https://www.intel.com/content/www/us/en/content-details/870124/securing-enterprise-rag-deployments.html)
* [Document Summarization: Transforming Enterprise Content with Intel® AI for Enterprise RAG](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Document-Summarization-Transforming-Enterprise-Content-with/post/1728252)
* [Scaling Intel® AI for Enterprise RAG Performance: 64-Core vs 96-Core Intel® Xeon®](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Scaling-Intel-AI-for-Enterprise-RAG-Performance-64-Core-vs-96/post/1723234)
* [Comprehensive Analysis: Intel® AI for Enterprise RAG Performance](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Comprehensive-Analysis-Intel-AI-for-Enterprise-RAG-Performance/post/1723226)
* [Monitoring and Debugging RAG Systems in Production](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Monitoring-and-Debugging-RAG-Systems-in-Production/post/1720292)
* [NetApp AIPod Mini – Deployment Automation](https://community.netapp.com/t5/Tech-ONTAP-Blogs/NetApp-AIPod-Mini-Deployment-Automation/ba-p/463257)
* [Multi-node deployments using Intel® AI for Enterprise RAG](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Multi-node-deployments-using-Intel-AI-for-Enterprise-RAG/post/1710214)
* [Rethinking AI Infrastructure: How NetApp and Intel Are Unlocking the Future with AIPod Mini](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Rethinking-AI-Infrastructure-How-NetApp-and-Intel-Are-Unlocking/post/1705557)
* [Deploying Scalable Enterprise RAG on Kubernetes with Ansible Automation](https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Deploying-Scalable-Enterprise-RAG-on-Kubernetes-with-Ansible/post/1701296)
<br/>

------

# License

Intel® AI for Enterprise RAG is licensed under the [Apache License Version 2.0](LICENSE). Refer to the "[LICENSE](LICENSE)" file for the full license text and copyright notice.

This distribution includes third-party software governed by separate license terms. This third-party software, even if included with the distribution of the Intel software, may be governed by separate license terms, including without limitation, third-party license terms, other Intel software license terms, and open-source software license terms. These separate license terms govern your use of the third-party programs as set forth in the "[THIRD-PARTY-PROGRAMS](THIRD-PARTY-PROGRAMS)" file.

Please note: component(s) depend on software subject to non-open source licenses. If you use or redistribute this software, it is your sole responsibility to ensure compliance with such licenses.

# Security

The [Security Policy](SECURITY.md) outlines our guidelines and procedures for ensuring the highest level of security and trust for our users who consume Intel® AI for Enterprise RAG.

# Intel's Human Rights Principles

Intel is committed to respecting human rights and avoiding causing or contributing to adverse impacts on human rights. See [Intel's Global Human Rights Principles](https://www.intel.com/content/dam/www/central-libraries/us/en/documents/policy-human-rights.pdf). Intel's products and software are intended only to be used in applications that do not cause or contribute to adverse impacts on human rights.

# Model Card Guidance

You, not Intel, are responsible for determining model suitability for your use case. For information regarding model limitations, safety considerations, biases, or other information consult the model cards (if any) for models you use, typically found in the repository where the model is available for download. Contact the model provider with questions. Intel does not provide model cards for third party models.

# Contributing

If you want to contribute to the project, please refer to the guide in [CONTRIBUTING.md](CONTRIBUTING.md) file.

# Trademark Information

Intel, the Intel logo, OpenVINO, the OpenVINO logo, Pentium, Xeon, and Gaudi are trademarks of Intel Corporation or its subsidiaries.

Other names and brands may be claimed as the property of others.

&copy; Intel Corporation
