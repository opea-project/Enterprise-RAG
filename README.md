# Intel® AI for Enterprise RAG

<div align="center">
  <a href="https://www.youtube.com/watch?v=wWcUNle1kkg">
    <img width=560 width=315 alt="Enterprise RAG Demo ChatQ&A" src="./images/yt_thumbnail.png">
  </a>
</div>
&nbsp;

Intel® AI for Enterprise RAG simplifies transforming your enterprise data into actionable insights. Powered by Intel® Gaudi® AI accelerators and Intel® Xeon® processors, it integrates components from industry partners to offer a streamlined approach to deploying enterprise solutions. It scales seamlessly with proven orchestration frameworks, providing the flexibility and choice your enterprise needs.

Building on the strong foundation of OPEA, Intel® AI for Enterprise RAG extends this base with key features that enhance scalability, security, and user experience. These include integrated Service Mesh capabilities for seamless integration with modern service-based architectures, production-ready validation for pipeline reliability, and a feature-rich UI for RAG as a service to manage and monitor workflows easily. Additionally, Intel® and partner support provide access to a broad ecosystem of solutions, combined with integrated IAM with UI and application, ensuring secure and compliant operations. Programmable guardrails enable fine-grained control over pipeline behavior, allowing for customized security and compliance settings.

> [!NOTE]
The video provided above showcases the beta release of our project. As we transition to the 1.0 version, users can anticipate an improved UI design along with other minor enhancements. While many features remain consistent with the beta, the 1.0 release will offer a more refined user experience.

**ChatQnA**

The ChatQnA solution uses retrieval augmented generation (RAG) architecture, quickly becoming the industry standard for chatbot development. It combines the benefits of a knowledge base (via a vector store) and generative models to reduce hallucinations, maintain up-to-date information, and leverage domain-specific knowledge.

![arch](./images/architecture.png)

For the complete microservices architecture, refer [here](./docs/microservices_architecture.png)
<div align="left">
    <a href="https://opea.dev/" target="_blank">
    <img  src="./images/logo.png" alt="Powered by Open Platform for Enterprise AI" height=100 width=280>
  </a>
</div>

# Table of Contents

- [Documentation](#documentation)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Support](#support)
- [License](#license)
- [Security](#security)
- [Trademark Information](#trademark-information)

# Documentation

* [Deployment Guide](deployment/README.md) explains how to install and configure Intel® AI for Enterprise RAG for your needs.

# System Requirements

| Category            | Details                                                                                                           |
|---------------------|-------------------------------------------------------------------------------------------------------------------|
| Operating System    | Ubuntu 20.04/22.04                                                                                                |
| Hardware Platforms  | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors<br>6th Gen Intel® Xeon® Scalable processors<br>3rd Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator<br>4th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator <br>6th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 3 AI Accelerator|
| Kubernetes Version  | 1.29.5 <br> 1.29.12 <br> 1.30.8 <br> 1.31.4                                                                        |
| Gaudi Firmware Version | 1.21.0                                                                                                          |
| Python              | 3.10                                                                                                               |

## Hardware Prerequisites for Deployment using Gaudi® AI Accelerator

To deploy the solution on a platform with Gaudi® AI Accelerator we need to have access to instance with minimal requirements:

-  **logical cores**: A minimum of `48` logical cores
-  **RAM memory**: A minimum of `250GB` of RAM though this is highly dependent on database size
-  **Disk Space**: `1TB` of disk space is generally recommended, though this is highly dependent on the model size and database size
-  **Gaudi cards**: `8`
-  **Latest Gaudi driver**: To check your Gaudi version, `run hl-smi`. If Gaudi version doesn't match the required version, upgrade it by following [this tutorial](https://docs.habana.ai/en/latest/Installation_Guide/Driver_Installation.html).


If you don't have a Gaudi® AI Accelerator, you can request these instances in [Intel® Tiber™ AI Cloud](https://console.cloud.intel.com/home) to run Intel® AI for Enterprise RAG.

- Visit [ai.cloud.intel.com](https://ai.cloud.intel.com/) and register.
- on [Intel® Tiber™ AI Cloud](https://console.cloud.intel.com/home) the left pane select `Preview > Preview catalog`.
- Select `Gaudi® 2 Deep Learning Server`, we recommend choosing a Bare Metal machine with 8 Gaudi devices to be able to meet hardware requirements.
- request instance
- As there is a limited number of machines with Gaudi accelerators, you need to be whitelisted to be able to access them. Therefore:
  - Send your email, Account ID, and information that you have requested an instance to [EnterpriseRAGRequest@intel.com](mailto:EnterpriseRAGRequest@intel.com) so we could add you to the whitelist.
- on Intel® Tiber™ AI Cloud the left pane select `Catalog > Hardware`. Once you are added to the whitelist you should see Gaudi instances available.
- Select the Machine image - for example: `ubuntu-2204-gaudi2-1.20.1-*` with `Architecture: X86_64 (Baremetal only)`. Please note that minor version tags may change over time.
- Upload your public key and launch the instance
- Navigate to the `Instances` page and verify that the machine has reached its ready state, then click on "How to Connect via SSH" to configure your machine correctly for further installation.


## Hardware Prerequisites for Deployment using Xeon only
To deploy the solution on a platform using 4th or 5th generation Intel® Xeon® processors, you will need:
- access to any platform with Intel® Xeon® Scalable processors that meet bellow requirements:
-  **logical cores**: A minimum of `80` logical cores
-  **RAM memory**: A minimum of `250GB` of RAM
-  **Disk Space**: `500GB` of disk space is generally recommended, though this is highly dependent on the model size

### Software Prerequisites

Refer to the [prerequisites](./docs/prerequisites.md) guide for detailed instructions to install the components mentioned below:

-   **Kubernetes Cluster**: Access to a Kubernetes v1.29-v1.31 cluster
-   **CSI Driver**: The K8s cluster must have the CSI driver installed. Users can define their own CSI driver that will be used during EnterpriseRAG install; however StorageClass provided by CSI driver should support ReadWriteMany(RWX) in case of using a multi-node cluster.
- Current solution was tested on a single node using the CSI driver [local-path-provisioner](https://github.com/rancher/local-path-provisioner), with  `local_path_provisioner_claim_root`  set to  `/mnt`. For an example of how to set up Kubernetes via Kubespray, refer to the prerequisites guide:  [CSI Driver](./docs/prerequisites.md#csi-driver).
-   **Operating System**: Ubuntu 20.04/22.04
-   **Hugging Face Model Access**: Ensure you have the necessary access to download and use the chosen Hugging Face model. This default model used is `Mixtral-8x7B` for which access needs to be requested. Visit  [Mixtral-8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) to apply for access.

#### Additional Software Prerequisites when using Gaudi® AI Accelerator
-   **Gaudi Software Stack**: Verify that your setup uses a valid software stack for Gaudi accelerators, see  [Gaudi support matrix](https://docs.habana.ai/en/latest/Support_Matrix/Support_Matrix.html). Note that running LLM on a CPU is possible but will significantly reduce performance.

# Pre-Installation

It is recommended to use python3-venv to manage python packages.

```sh
cd deployment
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yaml --upgrade
```

# Configuration file

To prepare configuration file create a copy of examplary one:

```sh
cd deployment
cp -r inventory/sample inventory/test-cluster
```

Fill proper variables at `inventory/test-cluster/config.yaml`

```yaml
huggingToken: FILL_HERE # Provide your Hugging Face token here
kubeconfig: FILL_HERE  # Provide absolute path to kubeconfig (e.g. /home/ubuntu/.kube/config)

# proxy settings are optional
httpProxy:
httpsProxy:
# If HTTP/HTTPS proxy is set, update the noProxy field with the following:
noProxy: #"localhost,.svc,.monitoring,.monitoring-traces"
[...]
pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-cpu.yaml # for hpu deployment we set chatqa/reference-hpu.yaml
    resourcesPath: chatqa/resources-reference-cpu.yaml # for hpu deployment we set chatqa/resources-reference-hpu.yaml
    type: chatqa
```

# Install Gaudi software stack (For Gaudi nodes only)

If your K8s cluster contains nodes with Gaudi® AI Accelerator, add bellow values to your inventory:

```
gaudi_operator: true # set to true when Gaudi operator is to be installed
habana_driver_version: "1.21.1-16" # habana operator from https://vault.habana.ai/ui/native/habana-ai-operator/driver/
```

# Installation

```sh
ansible-playbook -u $USER -K playbooks/application.yaml --tags configure,install -e @inventory/test-cluster/config.yaml
```

Refer [Deployment](deployment/README.md) if you prefer to install with multiple options.

# Remove installation

```sh
cd deployment
ansible-playbook playbooks/application.yaml --tags uninstall -e @inventory/test-cluster/config.yaml
```

# Support

Submit questions, feature requests, and bug reports on the GitHub Issues page.

# License

Intel® AI for Enterprise RAG is licensed under the [Apache License Version 2.0](LICENSE). Refer to the "[LICENSE](LICENSE)" file for the full license text and copyright notice.

This distribution includes third-party software governed by separate license terms. This third-party software, even if included with the distribution of the Intel software, may be governed by separate license terms, including without limitation, third-party license terms, other Intel software license terms, and open-source software license terms. These separate license terms govern your use of the third-party programs as set forth in the "[THIRD-PARTY-PROGRAMS](THIRD-PARTY-PROGRAMS)" file.

# Security

The [Security Policy](SECURITY.md) outlines our guidelines and procedures for ensuring the highest level of security and trust for our users who consume Intel® AI for Enterprise RAG.

# Intel’s Human Rights Principles

Intel is committed to respecting human rights and avoiding causing or contributing to adverse impacts on human rights. See [Intel’s Global Human Rights Principles](https://www.intel.com/content/dam/www/central-libraries/us/en/documents/policy-human-rights.pdf). Intel’s products and software are intended only to be used in applications that do not cause or contribute to adverse impacts on human rights.

# Model Card Guidance

You, not Intel, are responsible for determining model suitability for your use case. For information regarding model limitations, safety considerations, biases, or other information consult the model cards (if any) for models you use, typically found in the repository where the model is available for download. Contact the model provider with questions. Intel does not provide model cards for third party models.

# Trademark Information

Intel, the Intel logo, OpenVINO, the OpenVINO logo, Pentium, Xeon, and Gaudi are trademarks of Intel Corporation or its subsidiaries.

* Other names and brands may be claimed as the property of others.

&copy; Intel Corporation
