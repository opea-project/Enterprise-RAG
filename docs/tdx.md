# Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

This document outlines the deployment process of ChatQnA components on Intel® Xeon® Processors where the microservices are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).

> [!NOTE]
> Intel TDX feature in Enterprise RAG is experimental.


## What is Intel TDX?

[Intel Trust Domain Extensions (Intel TDX)](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html) is hardware-based trusted execution environment (TEE) that allows the deployment of hardware-isolated virtual machines (VM) designed to protect sensitive data and applications from unauthorized access.

[Confidential Containers](https://confidentialcontainers.org/docs/overview/) encapsulates pods inside confidential virtual machines, allowing Cloud Native workloads to leverage confidential computing hardware with minimal modification.


## Prerequisites

### System Requirements

| Category            | Details                                                                               |
|---------------------|---------------------------------------------------------------------------------------|
| Operating System    | Ubuntu 24.04                                                                          |
| Hardware Platforms  | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors  |
| Kubernetes Version  | 1.29.5 <br> 1.29.12 <br> 1.30.8 <br> 1.31.4                                           |

This guide assumes that:

1. you are familiar with the regular deployment of [Enterprise RAG](../README.md),
2. you have prepared a server with 4th Gen Intel® Xeon® Scalable Processor or later,
3. you have a single-node Kubernetes cluster already set up on the server for the regular deployment of Enterprise RAG, 
4. you are using public container registry to push Enterprise RAG images.


## Getting Started

### Prepare Intel Xeon node

Follow the below steps on the server node with Intel Xeon Processor:

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

4. Increase the kubelet timeout and wait until the node is `Ready`:

   ```bash
   echo "runtimeRequestTimeout: 30m" | sudo tee -a /etc/kubernetes/kubelet-config.yaml > /dev/null 2>&1
   sudo systemctl daemon-reload && sudo systemctl restart kubelet
   kubectl wait --for=condition=Ready node --all --timeout=2m
   ```


### Prepare the cluster

Follow the steps below on the Kubernetes cluster:

1. [Install Confidential Containers Operator](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-confidential-containers-operator)
2. [Install Attestation Components](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-attestation-components)


### Deploy the ChatQnA

Follow the steps below to deploy ChatQnA:

1. Make sure that you have exported the KBS_ADDRESS:

   ```bash
   export KBS_ADDRESS=http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}'):$(kubectl get svc kbs -n coco-tenant -o jsonpath='{.spec.ports[0].nodePort}')
   ```

2. Set the environment variables:

   ```bash
   export REGISTRY="your_container_registry"
   export TAG="your_tag"
   ```

3. Login to your registry:

   ```bash
   docker login your_container_registry
   ```

4. Push the images to your container registry:

   ```bash
   ./update_images.sh --build --push --registry "${REGISTRY}" --tag "${TAG}"
   ```

5. Update inventory/sample/config.yaml

   ```bash
   huggingToken: "" # Provide your Hugging Face token here
   kubeconfig: ""   # Provide absolute path to kubeconfig (e.g. /home/ubuntu/.kube/config)
   registry: ""     # Provide your_container_registry
   tag: ""          # Provide your_tag
   tdxEnabled: true # Set to true to enable Intel TDX
   ```

6.  Deploy eRAG

   ```bash
    ansible-playbook playbooks/application.yaml -e @inventory/sample/config.yaml --tags install
   ```

## Protected services

By default all microservices under following namespaces are protected with Intel TDX:

* `chatqa` 
* `edp`
* `fingerprint` 
* `rag-ui` 


## Advanced configuration


### Authenticated registry or encrypted images

If your images are stored in a private registry and are available only after authentication, follow the steps described in [authenticated registries guide](https://confidentialcontainers.org/docs/features/authenticated-registries/).

If you want to store your images encrypted in your container registry, follow the steps described in [encrypted images guide](https://confidentialcontainers.org/docs/features/encrypted-images/).


### Deployment customization

Edit the [resources-tdx.yaml](../deployment/components/*/resources-tdx.yaml) files to customize the Intel TDX-specific configurations per namespace.
The file contains common annotations and runtime class and list of services that should be protected by Intel TDX.
The service-specific resources are minimum that is required to run the service within a protected VM.
It overrides resources requests and limits only if increasing the resources.


## Limitations

1. Enterprise RAG cannot be used with Intel TDX with local registry or a registry with custom SSL certificate, see [this issue](https://github.com/kata-containers/kata-containers/issues/10507).
2. Only `*cpu*` pipelines are supported with Intel TDX (e.g.: `examples/cpu-torch.yaml`)
