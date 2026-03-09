# Running Intel® AI for Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

This document outlines the deployment process of ChatQnA components on Intel® Xeon® Processors where the microservices
are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).

> [!NOTE]
> `[CoCo]` deployment is not supported since release-2.1.0.

## Table of Contents

1. [What is Intel TDX](#what-is-intel-tdx)
2. [Prerequisites](#prerequisites)
    1. [System Requirements](#system-requirements)
3. [Getting Started](#getting-started)
    1. [Prepare Intel Xeon node](#prepare-intel-xeon-node)
    2. [Prepare the cluster](#prepare-the-cluster)
    3. [Deploy the ChatQnA/Audio ChatQnA/Docsum](#deploy-the-chatqna-audio-chatqna-docsum)
4. [Protected services](#protected-services)
5. [Advanced configuration](#advanced-configuration)
    1. [Authenticated registry or encrypted images](#authenticated-registry-or-encrypted-images)
    2. [Deployment customization](#deployment-customization)
6. [Limitations](#limitations)

## What is Intel TDX?

[Intel Trust Domain Extensions (Intel TDX)](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html)
is hardware-based trusted execution environment (TEE) that allows the deployment of hardware-isolated virtual machines
(VM) designed to protect sensitive data and applications from unauthorized access.

[Confidential Containers](https://confidentialcontainers.org/docs/overview/) encapsulates pods inside confidential
virtual machines, allowing Cloud Native workloads to leverage confidential computing hardware with minimal modification.

## Prerequisites

### System Requirements

| Category           | Details                                                                                                                          |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------|
| Operating System   | Ubuntu 24.04                                                                                                                     |
| Hardware Platforms | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors<br>6th Gen Intel® Xeon® Scalable processors |
| Kubernetes Version | 1.31+                                                                                                                            |

This guide assumes that:

1. you are familiar with the regular deployment of [Intel® AI for Enterprise RAG](../README.md),
2. you have prepared a server with 4th Gen Intel® Xeon® Scalable Processor or later,
3. you are using public container registry to push Intel® AI for Enterprise RAG.

Deployment can be done using a single-node Kubernetes cluster created:

1. inside single hardware-isolated Virtual Machine (VM) protected with TDX called Trust Domain (TD) for all pods
   `[one TD]`
2. on host, where multiple TDs (each per pod) are created
   using [Confidential Containers](https://confidentialcontainers.org/docs/overview/) `[CoCo]`

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

   In case the module version or `build_num` is lower than shown above, please refer to
   the [Intel TDX documentation](https://cc-enabling.trustedservices.intel.com/intel-tdx-enabling-guide/04/hardware_setup/#deploy-specific-intel-tdx-module-version)
   for update instructions.

3. [Setup Remote Attestation](https://github.com/canonical/tdx/?tab=readme-ov-file#setup-remote-attestation).

4. `[CoCo]` Increase the kubelet timeout and wait until the node is `Ready`:

   ```bash
   echo "runtimeRequestTimeout: 30m" | sudo tee -a /etc/kubernetes/kubelet-config.yaml > /dev/null 2>&1
   sudo systemctl daemon-reload && sudo systemctl restart kubelet
   kubectl wait --for=condition=Ready node --all --timeout=2m
   ```

5. `[one TD]` [Create TD Image](https://github.com/canonical/tdx/?tab=readme-ov-file#51-create-a-new-td-image)
   and [Boot TD](https://github.com/canonical/tdx/?tab=readme-ov-file#61-boot-td-with-qemu-using-run_td-script).

### Prepare the cluster

1. Follow the steps to [deploy kubernetes cluster](cluster_deployment_guide.md).

2. `[CoCo]` [Install Confidential Containers Operator](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-confidential-containers-operator).

3. [Install Attestation Components](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-attestation-components).

### Deploy the ChatQnA, Audio ChatQnA, Docsum

Follow the steps below to deploy Intel® AI for Enterprise RAG:

1. Update config
   
   - For ChatQnA and Audio ChatQnA: `inventory/sample/config.yaml`
   - For Docsum: `inventory/sample/config_docsum.yaml`

   ```yaml
   huggingToken: "<HUGGING_FACE_TOKEN>" # [OPTIONAL] Provide your Hugging Face token here - required for gated/private models
   kubeconfig: "<PATH_TO_KUBECONFIG>"   # [OPTIONAL] Provide absolute path to kubeconfig (e.g. /home/ubuntu/.kube/config) - can be left intact if `deploy_k8s: true` 
   registry: "<IMAGE_REGISTRY>"     # [OPTIONAL] Provide your_container_registry - can be left intact for default image
   tag: "<IMAGE_TAG>"          # [OPTIONAL] Provide your_tag - can be left intact for default image
   tdx:
      enabled: true|false  # Set to true to enable Intel TDX.
      td_type: one-td|coco # Set accordingly to your deployment case: [one TD]/[CoCo] 
      attestation:
         enabled: true|false # [one TD] Set to true to enable TDX based attestation.
   ```

   Setting `attestation.enabled` enforces TDX attestation as a prerequisite for a successful Intel® AI for Enterprise RAG
   deployment.    
   To learn more about TDX attestation head to [Confidential Containers Attestation](https://confidentialcontainers.org/docs/attestation/).

2. `[OPTIONAL]` `[one TD]` Provide attestation infrastructure:

   Build KBS client on VM and add place it under `/opt/trustee/target/release`.

   ```bash
   git clone -b {{ kbs_ver }} https://github.com/confidential-containers/trustee
   pushd trustee/kbs
   make cli ATTESTER=tdx-attester
   mkdir -p /opt/trustee/target/release
   popd
   cp trustee/target/release/kbs-client /opt/trustee/target/release
   ```

3. Deploy Intel® AI for Enterprise RAG:

   Make sure that you have exported the `KBS_ADDRESS`, which points to the Key Broker Service ([KBS](https://confidentialcontainers.org/docs/attestation/architecture/#key-broker-service)).
   KBS can be deployed on any trusted machine. The most common cases are described below.

   - `CoCo` - if KBS was deployed on the same kubernetes node as whole cluster, that is simply: 

       ```bash
        export KBS_ADDRESS=http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}'):$(kubectl get svc kbs -n coco-tenant -o jsonpath='{.spec.ports[0].nodePort}')
       ```
   - `one-TD` - the most common case is when KBS runs on host of the TD:
        ```bash
        export KBS_ADDRESS=http://<HOST IP ADDRESS>:8080
        ```

   Now you can deploy Intel® AI for Enterprise RAG:

    ```bash
     ansible-playbook playbooks/application.yaml -e @inventory/sample/config.yaml --tags install
    ```

## Protected services

`[one TD]` All microservices are protected by Intel TDX, as all pods run inside a single Trust Domain (TD).

`[CoCo]` All microservices under following namespaces are protected with Intel TDX (each pod has its own Trust Domain):

* `chatqa`
* `chat-history`
* `edp`
* `fingerprint`
* `rag-ui`
* `vdb`

## Advanced configuration

### Authenticated registry or encrypted images

If your images are stored in a private registry and are available only after authentication, follow the steps described
in [authenticated registries guide](https://confidentialcontainers.org/docs/features/authenticated-registries/).

If you want to store your images encrypted in your container registry, follow the steps described
in [encrypted images guide](https://confidentialcontainers.org/docs/features/encrypted-images/).

### Deployment customization

There are two mechanisms used to customize the deployment with Intel TDX:

- post rendering: enable new pods with Intel TDX using helm's post rendering,
  i.e. [main.yaml](../deployment/roles/application/vector_databases/tasks/main.yaml#L161).

- charts/tempEdit the `resources-tdx.yaml` files to customize the Intel TDX-specific configurations per namespace.
  The file contains common annotations and runtime class and list of services that should be protected by Intel TDX.
  The service-specific resources are minimum that is required to run the service within a protected VM.
  It overrides resources requests and limits only if increasing the resources.

> [!NOTE]
> Resource files can be found under: `Enterprise-RAG/deployment/components/<component>/resources-tdx.yaml`.

## Limitations

1. `[CoCo]` Intel® AI for Enterprise RAG cannot be used with Intel® TDX with local registry or a registry with custom SSL certificate,
   see [this issue](https://github.com/kata-containers/kata-containers/issues/10507).
2. Only `*cpu*` pipelines are supported with Intel TDX.

> [!NOTE]
> `[CoCo]` deployment path is experimental and not fully supported for all the microservices yet due to lack of support 
> for port forwarding support in kata VM, 
> [see this issue](https://github.com/kata-containers/kata-containers/issues/1693).

