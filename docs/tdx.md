# Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

This document outlines the deployment process of ChatQnA components on Intel® Xeon® Processors where the microservices are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).

> [!NOTE]
> Intel TDX feature in Enterprise RAG is experimental.


## What is Intel TDX?

[Intel Trust Domain Extensions (Intel TDX)](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html) is hardware-based trusted execution environment (TEE) that allows the deployment of hardware-isolated virtual machines (VM) designed to protect sensitive data and applications from unauthorized access.

[Confidential Containers](https://confidentialcontainers.org/docs/overview/) encapsulates pods inside confidential virtual machines, allowing Cloud Native workloads to leverage confidential computing hardware with minimal modification.


## Prerequisites

### Support matrix

|                    |                                                                                      |
|--------------------|--------------------------------------------------------------------------------------|
| Operating System   | Ubuntu 24.04                                                                         |
| Hardware Platforms | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors |
| Kubernetes Version | 1.29                                                                                 |

This guide assumes that:

1. you are familiar with the regular deployment of [Enterprise RAG](../README.md),
2. you have prepared a server with 4th Gen Intel® Xeon® Scalable Processor or later,
3. you have a single-node Kubernetes cluster already set up on the server for the regular deployment of Enterprise RAG, 
4. you are using public container registry to push Enterprise RAG images.


## Getting Started

Follow the below steps on the server node with Intel Xeon Processor to deploy the example application:

1. [Install Ubuntu 24.04 and enable Intel TDX](https://github.com/canonical/tdx/blob/noble-24.04/README.md#setup-host-os)
2. [Setup Remote Attestation](https://github.com/canonical/tdx?tab=readme-ov-file#setup-remote-attestation)
3. [Install Confidential Containers Operator](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-confidential-containers-operator)
4. [Install Attestation Components](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-attestation-components)
5. Make sure that you have exported the KBS_ADDRESS:

   ```bash
   export KBS_ADDRESS=<YOUR_KBS_ADDRESS>
   ```

6. Increase the kubelet timeout and wait until the node is `Ready`:

   ```bash
   echo "runtimeRequestTimeout: 30m" | sudo tee -a /etc/kubernetes/kubelet-config.yaml > /dev/null 2>&1
   sudo systemctl daemon-reload && sudo systemctl restart kubelet
   kubectl wait --for=condition=Ready node --all --timeout=2m
   ```

7. Deploy ChatQnA by adding `--features tdx` parameter and leaving all other parameters without changes:

   ```bash
   git clone https://github.com/intel/Enterprise-RAG.git
   cd Enterprise-RAG/deployment
   ./one_click_chatqna.sh --features tdx -g HUG_TOKEN [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d [PIPELINE] -t [TAG] -y [REGISTRY]
   ```


## Protected services

By default, the microservices protected with Intel TDX are:

* `in-guard-usvc` 
* `llm-usvc` 
* `out-guard-usvc` 
* `redis-vector-db` 
* `reranking-usvc` 
* `retriever-usvc` 
* `tei` 
* `teirerank`


## Advanced configuration


### Authenticated registry or encrypted images

If your images are stored in a private registry and are available only after authentication, follow the steps described in [authenticated registries guide](https://confidentialcontainers.org/docs/features/authenticated-registries/).

If you want to store your images encrypted on a public registry, follow the steps described in [encrypted images guide](https://confidentialcontainers.org/docs/features/encrypted-images/).


### Deployment customization

Edit the [tdx.yaml](../deployment/microservices-connector/helm/tdx.yaml) file to customize the Intel TDX-specific configuration.
The file contains common annotations and runtime class and list of services that should be protected by Intel TDX.
The service-specific resources are minimum that is required to run the service within a protected VM.
It overrides resources requests and limits only if increasing the resources.


## Limitations

1. Enterprise RAG cannot be used with Intel TDX with local registry or a registry with custom SSL certificate, see [this issue](https://github.com/kata-containers/kata-containers/issues/10507).
2. Only `*xeon*` pipelines are supported with Intel TDX (e.g.: `chatQnA_xeon_torch_llm_guard`)
3. Some microservices defined in [tdx.yaml](../deployment/microservices-connector/helm/tdx.yaml) may not yet work with Intel TDX due to various issues in opensource components.
