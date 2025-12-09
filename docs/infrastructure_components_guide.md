# Infrastructure Components Guide

This document describes how to install infrastructure components on a K8s cluster.

All instructions need to be executed on your local machine from the `deployment` folder.

If you are using your own custom Kubernetes cluster, you may need to install additional infrastructure components before deploying Intel® AI for Enterprise RAG application. These include the NFS server for shared storage, the Gaudi operator (for Habana Gaudi AI accelerator support), Velero, local registry, or other supported services.

To install additional infrastructure components to your cluster:

1. **Edit the configuration file:**
   - Open `inventory/test-cluster/config.yaml`.
   - Fill in the required values:
     - `deploy_k8s`: `false`
     - `gaudi_operator`: `true` set to true only if you are working with Gaudi nodes and want to install the Gaudi software stack via operator.
     - `install_csi` - set one of the following options:
        - `local-path-provisioner` for single-node deployment
        - `nfs` for multi-node deployment; when choosing this option, fill in the nfs section in config.yaml
        - `netapp-trident`: Use for enterprise deployments with NetApp ONTAP storage backend; when choosing this option, fill in the netapp-trident section in config.yaml
     - `local_registry`: Default is `false`. Set to `true` only if you have a multi-node setup and you don't want to use images from public registry. When enabled, also configure:
       - `insecure_registry`: `"<node-name>:32000"` where `<node-name>` is the Kubernetes node name where the registry pod will be deployed
     - `httpProxy` and `httpsProxy` values if you are using a proxy.
     - `kubeconfig`: `path to your kubeconfig`
     - `velero`: `true` if you want to install the Velero backup tool.

> [!NOTE]
> The `pre-install` tag automatically configures system limits (file descriptors, process limits, inotify watches, and kernel parameters) on all cluster nodes. These configurations are essential for optimal Enterprise RAG performance and are applied before the main installation process.

> [!NOTE]
> The local registry option creates a Kubernetes pod with registry functionality and configures Docker and containerd settings to enable pushing and pulling images to the registry pod. This is particularly useful for multi-node clusters where a standard Docker registry would only be accessible from a single node.

2. **Validate hardware resources and `config.yaml`:**

   ```sh
   ansible-playbook playbooks/validate.yaml --tags hardware,config -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
   ```
> [!NOTE]
> If this is a Gaudi deployment, add the flag `-e is_gaudi_platform=true`.

3. **Configure system limits (recommended before installation):**

   ```sh
   ansible-playbook -K playbooks/infrastructure.yaml --tags pre-install -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
   ```
   This will configure system limits on all cluster nodes including file descriptors, process limits, inotify watches, and kernel parameters required for Enterprise RAG.

4. **Install infrastructure components (NFS, Gaudi operator, local registry, or others):**

   ```sh
   ansible-playbook -K playbooks/infrastructure.yaml --tags post-install -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
   ```
   This will install and configure the NFS server, Gaudi operator, local registry, or Velero as specified in your configuration.
   
> [!NOTE]
> You can enable several components in the same run if multiple components are needed. Additional components may be supported via post-install in the future.

