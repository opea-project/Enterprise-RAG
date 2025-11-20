# Cluster Deployment Guide

This document explains how to deploy a K8s cluster using Intel® AI for Enterprise RAG ansible automations.

All instructions need to be executed on your local machine from the `deployment` folder. 

To deploy a K8s cluster, you need to fill the inventory.ini file that describes K8s node roles and gives ansible information on how to connect to the hosts. Make sure you are able to ssh from your local machine to the nodes on which you want to deploy K8s before provisioning the cluster. 

**Prerequisites**: Ansible nodes need to have passwordless SSH connection from localhost to MACHINE_HOSTNAME. To check this, the command `ssh REMOTE_USER@MACHINE_IP` should work without asking for a password.

**Setting up passwordless SSH connection:**
1. Generate SSH key pair:
   ```bash
   ssh-keygen -t ed25519
   ```
2. Copy the public key to the remote host:
   ```bash
   ssh-copy-id REMOTE_USER@MACHINE_IP
   ```
3. Verify that SSH connection works without password:
   ```bash
   ssh REMOTE_USER@MACHINE_IP
   ```

Below are example inventory.ini files for different deployment scenarios:

### Localhost Deployment (Single-node, running from the node itself)

For deployments where you're running Ansible directly on the target node:

```ini
# Sample inventory for localhost deployment
# Replace <hostname> with your actual hostname

localhost ansible_connection=local

[kube_control_plane]
localhost

[kube_node]
localhost

[etcd:children]
kube_control_plane

[k8s_cluster:children]
kube_control_plane
kube_node

[k8s_cluster:vars]
ansible_become=true
```

### Remote Deployment (Single-node or Multi-node)

For deployments where you're managing remote nodes via SSH:

**Single-node remote cluster:**
```ini
# Control plane node
MACHINE_HOSTNAME ansible_host=MACHINE_IP

[kube_control_plane]
MACHINE_HOSTNAME

[kube_node]
MACHINE_HOSTNAME

[etcd:children]
kube_control_plane

[k8s_cluster:children]
kube_control_plane
kube_node

[k8s_cluster:vars]
ansible_become=true
ansible_user=REMOTE_USER
ansible_connection=ssh
ansible_ssh_private_key_file=PATH_TO_PRIVATE_SSH_KEY
```

**Multi-node remote cluster:**
```ini
# Control plane nodes
kube-master-1 ansible_host=<node1_ip_address>
kube-master-2 ansible_host=<node2_ip_address>
kube-master-3 ansible_host=<node3_ip_address>

# Worker nodes
kube-worker-1 ansible_host=<node4_ip_address>
kube-worker-2 ansible_host=<node5_ip_address>
kube-worker-3 ansible_host=<node6_ip_address>

[kube_control_plane]
kube-master-1
kube-master-2
kube-master-3

[kube_node]
kube-worker-1
kube-worker-2
kube-worker-3

[etcd:children]
kube_control_plane

[k8s_cluster:children]
kube_control_plane
kube_node

[k8s_cluster:vars]
ansible_become=true
ansible_user=REMOTE_USER
ansible_connection=ssh
ansible_ssh_private_key_file=PATH_TO_PRIVATE_SSH_KEY
```

1. **Edit the inventory file:**
   - Open `inventory/test-cluster/inventory.ini`.
   - Replace placeholders (`<hostname>`, `REMOTE_USER`, `MACHINE_HOSTNAME`, `MACHINE_IP`, etc.) with your actual values.

For more information on preparing an Ansible inventory, see the [Ansible Inventory Documentation](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html).

**Verify Ansible connectivity:**
After creating the inventory file, verify that Ansible can connect to all defined hosts:
```bash
ansible all -i inventory/test-cluster/inventory.ini -m ping --ask-become-pass
```

The output should look like this:
```
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
igk-0701 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```

2. **Edit the configuration file:**
   - Open `inventory/test-cluster/config.yaml`.
   - Fill in the required values:
     - `deploy_k8s`: `true` to install K8s cluster.
     - `gaudi_operator`: `true` set value to true only if you are working with Gaudi nodes and want to install the Gaudi software stack via operator.
     - `install_csi` - set one of the following options:
        - `local-path-provisioner` for single-node deployment.
        - `nfs` for multi-node deployment; when choosing this option, fill in the nfs section in config.yaml.
        - `netapp-trident`: Use for enterprise deployments with NetApp ONTAP storage backend; when choosing this option, fill in the netapp-trident section in config.yaml.
     - `local_registry`: Default is `false`. Set to `true` only if you have a multi-node setup and you don't want to use images from public registry. When enabled, also configure:
       - `insecure_registry`: `"<node-name>:32000"` where `<node-name>` is the Kubernetes node name where the registry pod will be deployed.
     - `httpProxy` and `httpsProxy` values if you are using a proxy.
     - `kubeconfig`: `<repository path>/deployment/inventory/test-cluster/artifacts/admin.conf` as the installation will create a K8s config file there.
     - `velero`: `true` if you want to install the Velero backup tool together with the K8s installation.

> [!NOTE]
> The local registry option creates a Kubernetes pod with registry functionality and configures Docker and containerd settings to enable pushing and pulling images to the registry pod. This is particularly useful for multi-node clusters where a standard Docker registry would only be accessible from a single node.

3. **(Optional) Validate hardware resources:**

   Before running the validation, ensure that SSH connection works without asking for a password by testing:
   ```bash
   ssh REMOTE_USER@MACHINE_IP
   ```

   Then run the hardware validation:
   ```sh
   ansible-playbook playbooks/validate.yaml --tags hardware -i inventory/test-cluster/inventory.ini
   ```

> [!NOTE]
> If this is a Gaudi deployment, add the additional flag `-e is_gaudi_platform=true`.

4. **Deploy K8s cluster:**

   ```sh
   ansible-playbook -K playbooks/infrastructure.yaml --tags configure,install -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
   ```

## K8s Cluster Deletion

To remove the K8s cluster, run:

```sh
ansible-playbook -K playbooks/infrastructure.yaml --tags delete -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
```
