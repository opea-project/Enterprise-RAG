# Intel(R) AI for Enterprise RAG

Intel AI for Enterprise RAG makes turning your enterprise data into actionable insights easy while delivering better total cost of ownership (TCO) than the alternative. Powered by Intel Gaudi AI accelerators and Intel Xeon processors, Intel AI for Enterprise RAG integrates components from [OPEA] and industry partners to offer a streamlined approach to deploying solutions for enterprises. It scales seamlessly with proven orchestration frameworks, giving you the flexibility and choice your enterprise needs.

[OPEA]:https://opea.dev/

# Table of Contents

- [Documentation](#documentation)
- [System Requirements](#system-requirements)
- [Installation](#Installation)
- [Support](#support)
- [License](#license)
- [Security](#security)
- [Trademark Information](#trademark-information)

# Documentation

* [Application Guide](docs/Application_Guide.md) explains how to install and configure Intel(R) AI for Enterprise RAG for your needs.
* [API Reference](docs/API_Reference.md) provides a comprehensive reference of APIs.

# System Requirements

Intel(R) AI for Enterprise RAG supports following platforms: 
- 4th Gen Intel Xeon processors and Intel(R) Gaudi(R) 2 AI accelerator
- 5th Gen Intel Xeon processors and Intel(R) Gaudi(R) 3 AI accelerator
  
## Requirements for Building from Source

Intel(R) AI for Enterprise RAG supports systems meeting the following requirements:
* Debian based Linux* Operating system with Intel 64 
* Kubernetes (K8s) cluster with version v1.11.3+ [Refer K8s setup with Gaudi nodes](https://docs.habana.ai/en/latest/Orchestration/Gaudi_Kubernetes/index.html#kubernetes-user-guide)
* AWS account with Elastic Container Registry (ECR) - Planned to be removed 

# Installation

```
git clone https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution.git
cd applications.ai.enterprise-rag.enterprise-ai-solution/deployment/microservices-connector
./one_click_chatqna.sh -a AWS_ACCESS_KEY_ID -s AWS_SECRET_ACCESS_KEY -r REGION [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -g HUG_TOKEN
```
Proxy variables are optional.
Refer [Deployment](deployment/microservices-connector/README.md#prerequisites) if you prefer to install with multiple options.

# Support

Submit questions, feature requests, and bug reports on the
GitHub Issues page.

# License

Intel(R) AI for Enterprise RAG is licensed under [Apache License Version 2.0](LICENSE). Refer to the
"[LICENSE](LICENSE)" file for the full license text and copyright notice.

This distribution includes third party software governed by separate license
terms. This third party software, even if included with the distribution of
the Intel software, may be governed by separate license terms, including
without limitation, third party license terms, other Intel software license
terms, and open source software license terms. These separate license terms
govern your use of the third party programs as set forth in the
"[THIRD-PARTY-PROGRAMS](THIRD-PARTY-PROGRAMS)" file.

# Security

[Security Policy](SECURITY.md) outlines our guidelines and procedures
for ensuring the highest level of Security and trust for our users
who consume oneDNN.

# Trademark Information

Intel, the Intel logo, Arc, Intel Atom, Intel Core, Iris,
OpenVINO, the OpenVINO logo, Pentium, VTune, and Xeon are trademarks
of Intel Corporation or its subsidiaries.

Arm and Neoverse are trademarks, or registered trademarks of Arm Ltd.

\* Other names and brands may be claimed as the property of others.

Microsoft, Windows, and the Windows logo are trademarks, or registered
trademarks of Microsoft Corporation in the United States and/or other
countries.

OpenCL and the OpenCL logo are trademarks of Apple Inc. used by permission
by Khronos.

(C) Intel Corporation
