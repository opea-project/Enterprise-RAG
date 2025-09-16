# Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

This document outlines the deployment process of ChatQnA components on Intel® Xeon® Processors where the microservices are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).

> [!NOTE]
> Intel TDX feature in Enterprise RAG is experimental.

## Table of Contents

1. [What is Intel TDX](#what-is-intel-tdx)
2. [Prerequisites](#prerequisites)
   1. [System Requirements](#system-requirements)
3. [Getting Started](#getting-started)
   1. [Prepare Intel Xeon node](#prepare-intel-xeon-node)
   2. [Prepare the cluster](#prepare-the-cluster)
   3. [Build Enterprise RAG images](#build-enterprise-rag-images)
   4. [Deploy the ChatQnA](#deploy-the-chatqna)
4. [Protected services](#protected-services)
5. [Advanced configuration](#advanced-configuration)
   1. [Authenticated registry or encrypted images](#authenticated-registry-or-encrypted-images)
   2. [Deployment customization](#deployment-customization)
6. [Limitations](#limitations) 

## What is Intel TDX?

[Intel Trust Domain Extensions (Intel TDX)](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html) is hardware-based trusted execution environment (TEE) that allows the deployment of hardware-isolated virtual machines (VM) designed to protect sensitive data and applications from unauthorized access.

[Confidential Containers](https://confidentialcontainers.org/docs/overview/) encapsulates pods inside confidential virtual machines, allowing Cloud Native workloads to leverage confidential computing hardware with minimal modification.


## Prerequisites

### System Requirements

| Category            | Details                                                                                                                          |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------|
| Operating System    | Ubuntu 24.04                                                                                                                     |
| Hardware Platforms  | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors<br>6th Gen Intel® Xeon® Scalable processors |
| Kubernetes Version  | 1.29.5 <br> 1.29.12 <br> 1.30.8 <br> 1.31.4                                                                                      |

This guide assumes that:

1. you are familiar with the regular deployment of [Enterprise RAG](../README.md),
2. you have prepared a server with 4th Gen Intel® Xeon® Scalable Processor or later,
3. you are using public container registry to push Enterprise RAG images.

Deployment can be done using a single-node Kubernetes cluster created:
1. inside single hardware-isolated Virtual Machine (VM) protected with TDX called Trust Domain (TD) for all pods `[one TD]`
2. on host, where multiple TDs (each per pod) are created using [Confidential Containers](https://confidentialcontainers.org/docs/overview/) `[CoCo]`

Steps below are common for both cases unless are tagged with `[one TD]` or `[CoCo]`.

## Getting Started

### Prepare Intel Xeon node

Follow the below steps on the server node with Intel Xeon Processor:

1. [Install Ubuntu 24.04 and enable Intel TDX](https://github.com/canonical/tdx/?tab=readme-ov-file#setup-host-os).
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

3. [Setup Remote Attestation](https://github.com/canonical/tdx/?tab=readme-ov-file#setup-remote-attestation).

4. `[CoCo]` Increase the kubelet timeout and wait until the node is `Ready`:

   ```bash
   echo "runtimeRequestTimeout: 30m" | sudo tee -a /etc/kubernetes/kubelet-config.yaml > /dev/null 2>&1
   sudo systemctl daemon-reload && sudo systemctl restart kubelet
   kubectl wait --for=condition=Ready node --all --timeout=2m
   ```

5. `[one TD]` [Create TD Image](https://github.com/canonical/tdx/?tab=readme-ov-file#51-create-a-new-td-image) and [Boot TD](https://github.com/canonical/tdx/?tab=readme-ov-file#61-boot-td-with-qemu-using-run_td-script).


### Prepare the cluster

1. Follow the steps to [deploy kubernetes cluster](../README.md#pre-installation). 

2. `[one TD]` Make sure to deploy the cluster inside the TD and check if NRI kubernetes plugin is enabled. Run device injector at index 10:
   
   ```bash
   git clone https://github.com/containerd/nri.git
   cd nri/plugins/device-injector
   go build
   ./device-injector -idx 10
   ```

3. `[CoCo]` [Install Confidential Containers Operator](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-confidential-containers-operator).

4. [Install Attestation Components](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-attestation-components).


### Build Enterprise RAG images

Follow the steps below to build Enterprise RAG images:

1. Set the environment variables:

   ```bash
   export REGISTRY="your_container_registry"
   export TAG="your_tag"
   ```

2. Login to your registry:

   ```bash
   docker login your_container_registry
   ```

3. Push the images to your container registry:

   ```bash
   ./update_images.sh --build --push --registry "${REGISTRY}" --tag "${TAG}"
   ```


### Deploy the ChatQnA

Follow the steps below to deploy Enterprise RAG:

1. Update `inventory/sample/config.yaml`:

   ```yaml
   huggingToken: "" # Provide your Hugging Face token here
   kubeconfig: ""   # Provide absolute path to kubeconfig (e.g. /home/ubuntu/.kube/config)
   registry: ""     # Provide your_container_registry
   tag: ""          # Provide your_tag
   tdx:
      enabled: true|false  # Set to true to enable Intel TDX.
      td_type: one-td|coco # Set accordingly to your deployment case: [one TD]/[CoCo] 
      attestation:
         enabled: true|false # [one TD] Set to true to enable TDX based attestation.
   ```

2. `[OPTIONAL]` `[one TD]` Provide attestation infrastracture:
   
   Build KBS client on VM and add place it under `/opt/trustee/target/release`.
   
   ```bash
   git clone -b {{ kbs_ver }} https://github.com/confidential-containers/trustee
   cd trustee/kbs
   make cli ATTESTER=tdx-attester
   mkdir -p /opt/trustee/target/release
   cp trustee/target/release/kbs-client /opt/trustee/target/release
   ```

3.  Deploy eRAG:
   
   Make sure that you have exported the KBS_ADDRESS, which points to the Key Broker Service (KBS): 
   
   ```bash
   export KBS_ADDRESS=http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}'):$(kubectl get svc kbs -n coco-tenant -o jsonpath='{.spec.ports[0].nodePort}')
   ```
   Now you can deploy erag:
   
   ```bash
    ansible-playbook playbooks/application.yaml -e @inventory/sample/config.yaml --tags install
   ```

## Protected services

`[one TD]` All microservices are protected by Intel TDX, as all pods run inside a single Trust Domain (TD).

`[CoCo]` All microservices under following namespaces are protected with Intel TDX:

* `chatqa`
* `chat-history`
* `edp`
* `fingerprint` 
* `rag-ui`
* `vdb`


## Advanced configuration


### Authenticated registry or encrypted images

If your images are stored in a private registry and are available only after authentication, follow the steps described in [authenticated registries guide](https://confidentialcontainers.org/docs/features/authenticated-registries/).

If you want to store your images encrypted in your container registry, follow the steps described in [encrypted images guide](https://confidentialcontainers.org/docs/features/encrypted-images/).


### Deployment customization

There are two mechanisms used to customize the deployment with Intel TDX:
- post rendering: enable new pods with Intel TDX using helm's post rendering, i.e. [main.yaml](../deployment/roles/application/vector_databases/tasks/main.yaml#L161).

- charts/tempEdit the `resources-tdx.yaml` files to customize the Intel TDX-specific configurations per namespace.
The file contains common annotations and runtime class and list of services that should be protected by Intel TDX.
The service-specific resources are minimum that is required to run the service within a protected VM.
It overrides resources requests and limits only if increasing the resources.

> [!NOTE]
> Resource files can be found under: `Enterprise-RAG/deployment/components/<component>/resources-tdx.yaml`.


## Limitations

1. Enterprise RAG (eRAG) cannot be used with Intel TDX with local registry or a registry with custom SSL certificate, see [this issue](https://github.com/kata-containers/kata-containers/issues/10507).
2. Only `*cpu*` pipelines are supported with Intel TDX.
3. `[CoCo]` A few of eRAG's microservices can't be enabled with Intel TDX due to lack of support for port forwarding support in kata VM, [see this issue](https://github.com/kata-containers/kata-containers/issues/1693).
