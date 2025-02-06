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
2. Check, if Intel TDX is enabled:

   ```bash
   sudo dmesg | grep -i tdx
   ```
   
   The output should show the Intel TDX module version and initialization status: 
   ```text
   virt/tdx: TDX module: attributes 0x0, vendor_id 0x8086, major_version 1, minor_version 5, build_date 20240129, build_num 698
   (...)
   virt/tdx: module initialized
   ```
   
   In case the module version or `build_num` is lower than shown above, please refer to the [Intel TDX documentation](https://cc-enabling.trustedservices.intel.com/intel-tdx-enabling-guide/04/hardware_setup/#deploy-specific-intel-tdx-module-version) for update instructions.

3. [Setup Remote Attestation](https://github.com/canonical/tdx?tab=readme-ov-file#setup-remote-attestation)
4. [Install Confidential Containers Operator](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-confidential-containers-operator)
5. [Install Attestation Components](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-attestation-components)
6. Make sure that you have exported the KBS_ADDRESS:

   ```bash
   export KBS_ADDRESS=<YOUR_KBS_ADDRESS>
   ```

7. Increase the kubelet timeout and wait until the node is `Ready`:

   ```bash
   echo "runtimeRequestTimeout: 30m" | sudo tee -a /etc/kubernetes/kubelet-config.yaml > /dev/null 2>&1
   sudo systemctl daemon-reload && sudo systemctl restart kubelet
   kubectl wait --for=condition=Ready node --all --timeout=2m
   ```

8. Set the environment variables:

   ```bash
   export HUGGINGFACEHUB_API_TOKEN="your_hf_token"
   export REGISTRY="your_public_registry"
   export TAG="your_tag"
   export PIPELINE="xeon_torch_llm_guard"
   ```

9. Login to your registry:

   ```bash
   docker login your_public_registry
   ```

10. Push the images to public registry and deploy ChatQnA by adding `--features tdx` parameter and leaving all other parameters without changes (note, that only `*xeon*` pipelines are supported with Intel TDX):

   ```bash
   ./update_images.sh --build --push --registry "${REGISTRY}" --tag "${TAG}"
   ./set_values.sh -g "${HUGGINGFACEHUB_API_TOKEN}" -r "${REGISTRY}" -t "${TAG}"
   ./install_chatqna.sh --deploy "${PIPELINE}" --registry "${REGISTRY}" --tag "${TAG}" --features tdx
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

Edit the [tdx.yaml](../deployment/microservices-connector/helm/resources-tdx.yaml) file to customize the Intel TDX-specific configuration.
The file contains common annotations and runtime class and list of services that should be protected by Intel TDX.
The service-specific resources are minimum that is required to run the service within a protected VM.
It overrides resources requests and limits only if increasing the resources.


## Limitations

1. Enterprise RAG cannot be used with Intel TDX with local registry or a registry with custom SSL certificate, see [this issue](https://github.com/kata-containers/kata-containers/issues/10507).
2. Only `*xeon*` pipelines are supported with Intel TDX (e.g.: `chatQnA_xeon_torch_llm_guard`)
3. Some microservices defined in [tdx.yaml](../deployment/microservices-connector/helm/resources-tdx.yaml) may not yet work with Intel TDX due to various issues in opensource components.
