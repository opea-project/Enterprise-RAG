# Prerequisites for Enterprise RAG

This document outlines the essential prerequisites for deploying and using the Enterprise RAG solution on Xeon-only or Xeon + Gaudi hardware. This guide ensures you're ready to install and configure Enterprise RAG.

- **For Xeon-only deployments**: Follow the instructions in the Common Prerequisites section and stop at the end of the [Install Cluster](#install-cluster) section. You do **not** need to proceed to the `Gaudi Software Stack` and later sections.
- **For Xeon + Gaudi deployments**: Go through the whole document.

## Table of Contents

 1. [Common Prerequisites (For Xeon & Xeon + Gaudi Deployments)](#common-prerequisites-for-xeon--xeon--gaudi-deployments)
    1. [System Requirements](#system-requirements)
    2. [Deploy Kubernetes using Kubespray](#deploy-kubernetes-using-kubespray)
 2. [Gaudi-Specific Prerequisites (Required for Xeon + Gaudi Deployments)](#gaudi-specific-prerequisites-required-for-xeon--gaudi-deployments)
 3. [Helpful Tools](#helpful-tools)

# Common Prerequisites (For Xeon & Xeon + Gaudi Deployments)

## System Requirements

| Category            | Details                                                                                                           |
|---------------------|-------------------------------------------------------------------------------------------------------------------|
| Operating System    | Ubuntu 20.04/22.04                                                                                                |
| Hardware Platforms  | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors<br>6th Gen Intel® Xeon® Scalable processors<br>3rd Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator<br>4th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator <br>6th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 3 AI Accelerator|
| Kubernetes Version  | 1.29.5 <br> 1.29.12 <br> 1.30.8 <br> 1.31.4                                                                        |
| Gaudi Firmware Version | 1.21.0

## Deploy Kubernetes using Kubespray
Deploy Kubernetes using Kubespray `(v2.27.0)` on a remote machine, followed by configuration and installation steps for the master node. The following steps show how this can be done using `Kubespray`.

>[!WARNING]
> The following instructions must be executed on a host machine that has network access to the Kubernetes cluster.
> It is adviced that Kubespray will not be run directly on the machines where Kubernetes is intended to be installed. Deploying the Kubernetes locally may generate some unexpected errors.

To be executed on a remote machine that has network access to the Gaudi cluster, meaning you should be able to SSH into a machine within the GPU cluster.

### Kubespray Setup

To run the Kubespray Ansible scripts, a virtual environment must be set up on your system. This involves creating a new Python virtual environment and installing the required dependencies.

Ansible is an automation tool that allows you to manage and configure infrastructure resources such as servers, networks, and databases. In this context, Ansible scripts will be used to deploy and manage a Kubernetes cluster using Kubespray.

Execute the below commands to set a virtual environment from which we will run the Kubespray Ansible scripts:

```bash
sudo apt update
sudo apt install python3-venv

VENVDIR=kubespray-venv

python3 -m venv $VENVDIR
source $VENVDIR/bin/activate
```
Clone the Kubespray repository and install the requirements:

```bash
git clone https://github.com/kubernetes-sigs/kubespray.git
cd kubespray
git checkout v2.27.0
pip install -U -r requirements.txt
```

In Kubespray, the `inventory` directory holds configurations for each cluster in separate subdirectories. The `inventory/sample` folder offers a template configuration for initializing new Kubernetes clusters.

Copy the inventory/sample folder and create your custom inventory:
```bash
cp -r inventory/sample/ inventory/mycluster
```

#### Single Node Example Configuration
Next step is to create a `hosts.ini` file in directory `inventory/mycluster`. `hosts.ini` defines the structure and roles of nodes within a Kubernetes cluster

```bash
# use any text editor to create and edit the hosts.ini file
vi inventory/mycluster/hosts.ini
```
An example of `hosts.ini` for a single-node cluster is shown below:
```ini
# This inventory describe a HA typology with stacked etcd (== same nodes as control plane)
# and 3 worker nodes
# See https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html
# for tips on building your inventory
node1 ansible_host=<K8s host ip> # ip=10.3.0.1 etcd_member_name=etcd1

# Configure 'ip' variable to bind kubernetes services on a different ip than the default iface
# We should set etcd_member_name for etcd cluster. The node that are not etcd members do not need to set the value,
# or can set the empty string value.
[kube_control_plane]
node1

[etcd]
node1

[kube_node]
node1
```

Suppose the IP address of your node is `100.51.110.245`, which you can verify by inspecting the output of `ifconfig` within the Ethernet interface section. Then, your `hosts.ini` file for a Kubespray configuration would be structured as follows:

```ini
node1 ansible_host=100.51.110.245

[kube_control_plane]
node1

[etcd]
node1

[kube_node]
node1
```

For more detailed info on cluster setup you can check [kubespray/getting-started](https://github.com/kubernetes-sigs/kubespray/blob/master/docs/getting_started/getting-started.md) and [inventory](https://github.com/kubernetes-sigs/kubespray/blob/release-2.27/docs/ansible/inventory.md) guides.

>[!WARNING]
>Ensure passwordless SSH for Ansible host nodes (from `hosts.ini`):
> - Generate keys (ssh-keygen) and copy the public key (ssh-copy-id user@node-ip).
> - Verify permissions (chmod): Ensure ~/.ssh directory permissions are set to `700` and authorized_keys file permissions are set to `600` on the remote host to maintain secure access.
> - Create a ~/.ssh/config file (if doesn't exist) and add a field for the remote machine. Example field might look as follows:
>
> ```bash
>   Host 111.22.333.444
>     ProxyCommand nc -X 5 -x <proxy_address> %h %p
>     IdentityFile "/home/user/.ssh/id_rsa"
>     User guest
>
>   Host 100.51.110.245
>     IdentityFile "/home/user/.ssh/id_rsa"
>     User user
>     ProxyJump 111.22.333.444
> ```
> - Test with **ssh user@node-ip** (should not prompt for a password).

#### Network Settings

Install `sshpass` to be able to send machine credentials via Ansible scripts:
```bash
sudo apt-get install sshpass
```
if you are behing a corporate VPN, setup proxy by editing the `all.yml` file:

```bash
# Edit proxy settings and save file
vi inventory/mycluster/group_vars/all/all.yml
```

>[!WARNING]
>Don't change the `no_proxy` variable.

### CSI Driver

A Container Storage Interface (CSI) driver is a standardized plugin that allows Kubernetes to manage storage solutions. These drivers abstract storage operations, ensuring consistent handling across different container environments.

The following instructions will set up a provisioner that will allow Kubernetes to automatically manage local disk storage for applications running in the cluster, using the specified directory (`/mnt`) as the base for all dynamically created volumes.

```bash
# edit and save the addons.yml file as shown below
vi inventory/mycluster/group_vars/k8s_cluster/addons.yml
```
Enable `local_host_provisioner` and point it to `/mnt`:

```yaml
local_path_provisioner_enabled: true
# local_path_provisioner_namespace: "local-path-storage"
# local_path_provisioner_storage_class: "local-path"
# local_path_provisioner_reclaim_policy: Delete
local_path_provisioner_claim_root: /mnt
```
Note that `local_path_provisioner_namespace`, `local_path_provisioner_storage_class` and `local_path_provisioner_reclaim_policy` must remain commented out in the file.

### Reset Cluster

>[!NOTE]
> Make sure that you can do a passwordless SSH into the ansible host node added in the `hosts.ini` file above.

`reset.yml` is the name of the playbook file used to clean up a Kubernetes cluster installation. It will remove Kubernetes components, dependencies, and configurations from the nodes listed in the `mycluster` inventory.

Reset K8s cluster to make sure we are making install on a clean environment:

```bash
ansible-playbook -i inventory/mycluster/hosts.ini --become --become-user=root -e override_system_hostname=false -kK reset.yml
```
>[!NOTE]
> If you want to skip being prompted for passwords, remove the `-kK` options. The `-kK` flags prompt for the SSH password (`-k`) and the sudo password (`-K`). If you choose to skip passwords, ensure that passwordless access to both the root and user accounts is configured on the localhost.

Answer `yes` to the prompt:
```bash
[Reset Confirmation]
Are you sure you want to reset cluster state? Type 'yes' to reset your cluster.:
```

A similar output can be seen after a successful reset:
```bash
PLAY RECAP *****************************************************************************************************
node1                      : ok=135  changed=30   unreachable=0    failed=0    skipped=118  rescued=0    ignored=0

Monday 28 October 2024  21:50:29 +0000 (0:00:00.375)       0:00:47.908 ********
===============================================================================
reset : Reset | delete some files and directories --------------------------------------------------------------------------- 10.03s
kubernetes/preinstall : Ensure kubelet expected parameters are set ----------------------------------------------------------- 3.82s
Reset Confirmation ----------------------------------------------------------------------------------------------------------- 3.55s
Gather information about installed services ---------------------------------------------------------------------------------- 2.03s
reset : Reset | remove containerd binary files ------------------------------------------------------------------------------- 1.32s
reset : Reset | remove services ---------------------------------------------------------------------------------------------- 1.29s
reset : Reset | stop services ------------------------------------------------------------------------------------------------ 1.11s
Gather necessary facts (hardware) -------------------------------------------------------------------------------------------- 0.85s
kubernetes/preinstall : Ensure ping package ---------------------------------------------------------------------------------- 0.68s
reset : Flush iptables ------------------------------------------------------------------------------------------------------- 0.64s
bootstrap-os : Assign inventory name to unconfigured hostnames (non-CoreOS, non-Flatcar, Suse and ClearLinux, non-Fedora) ---- 0.60s
kubernetes/preinstall : Install packages requirements ------------------------------------------------------------------------ 0.59s
kubernetes/preinstall : Create kubernetes directories ------------------------------------------------------------------------ 0.56s
bootstrap-os : Gather facts -------------------------------------------------------------------------------------------------- 0.53s
Gather necessary facts (network) --------------------------------------------------------------------------------------------- 0.49s
kubernetes/preinstall : Mask swap.target (persist swapoff) ------------------------------------------------------------------- 0.43s
kubernetes/preinstall : Update package management cache (APT) ---------------------------------------------------------------- 0.42s
kubernetes/preinstall : Write Kubespray DNS settings to systemd-resolved ----------------------------------------------------- 0.41s
kubernetes/preinstall : Disable fapolicyd service ---------------------------------------------------------------------------- 0.41s
kubernetes/preinstall : Remove swapfile from /etc/fstab ---------------------------------------------------------------------- 0.39s
```

### Install Cluster

`cluster.yml` is the playbook file that will be executed. It contains the tasks that will configure the nodes as per the roles and settings defined within `mycluster`, for setting up or managing the cluster.

```bash
ansible-playbook -i inventory/mycluster/hosts.ini --become --become-user=root -e override_system_hostname=false -kK cluster.yml
```
>[!NOTE]
> If you want to skip being prompted for passwords, remove the `-kK` options. The `-kK` flags prompt for the SSH password (`-k`) and the sudo password (`-K`). If you choose to skip passwords, ensure that passwordless access to both the root and user accounts is configured on the localhost.

After a successful execution of the Ansible playbook, a similar output is observed:
```bash
PLAY RECAP *****************************************************************************************************
node1                      : ok=672  changed=137  unreachable=0    failed=0    skipped=1133 rescued=0    ignored=6
Monday 28 October 2024  22:00:03 +0000 (0:00:00.334)       0:07:21.153 ********
===============================================================================
container-engine/docker : Docker | Remove docker configuration files -------------------------------------------------------- 29.49s
container-engine/docker : Docker | Stop all running container --------------------------------------------------------------- 27.39s
container-engine/docker : Reset | remove all containers --------------------------------------------------------------------- 23.74s
kubernetes/control-plane : Kubeadm | Initialize first master ---------------------------------------------------------------- 21.56s
container-engine/docker : Docker | Remove docker package -------------------------------------------------------------------- 18.22s
etcd : Reload etcd ----------------------------------------------------------------------------------------------------------- 6.07s
etcd : Configure | Check if etcd cluster is healthy -------------------------------------------------------------------------- 5.29s
download : Download_container | Download image if required ------------------------------------------------------------------- 4.59s
etcd : Configure | Ensure etcd is running ------------------------------------------------------------------------------------ 3.89s
kubernetes/preinstall : Ensure kubelet expected parameters are set ----------------------------------------------------------- 3.82s
download : Download_container | Download image if required ------------------------------------------------------------------- 3.53s
kubernetes-apps/ansible : Kubernetes Apps | Lay Down CoreDNS templates ------------------------------------------------------- 3.35s
kubernetes/preinstall : Preinstall | wait for the apiserver to be running ---------------------------------------------------- 3.32s
container-engine/containerd : Containerd | Unpack containerd archive --------------------------------------------------------- 3.23s
kubernetes-apps/ansible : Kubernetes Apps | Start Resources ------------------------------------------------------------------ 3.04s
container-engine/crictl : Download_file | Download item ---------------------------------------------------------------------- 2.89s
container-engine/runc : Download_file | Download item ------------------------------------------------------------------------ 2.89s
download : Download_file | Download item ------------------------------------------------------------------------------------- 2.85s
etcdctl_etcdutl : Download_file | Download item ------------------------------------------------------------------------------ 2.84s
container-engine/containerd : Download_file | Download item ------------------------------------------------------------------ 2.78s
```

### Setting Up and Verifying Kubernetes Cluster Access

Once ansible scripts ended, connect via SSH to the remote machine to check if Kubernetes has deployed correctly. Inside the remote machine you can execute following commands to be able to manage k8s as non-root user.

```bash
# create the `.kube` folder
mkdir ~/.kube
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
# change owner to user
sudo chown -R <username>:<groupname> ~/.kube
```
To verify that the K8s cluster is working and all pods are in running state, run `kubectl get pods -A` .

The output should show the following pods in a running state:
```bash
NAMESPACE            NAME                                       READY   STATUS    RESTARTS   AGE
kube-system          calico-kube-controllers-68485cbf9c-dr9vd   1/1     Running   0          5m
kube-system          calico-node-gnxk9                          1/1     Running   0          5m19s
kube-system          coredns-69db55dd76-4zq74                   1/1     Running   0          4m45s
kube-system          dns-autoscaler-6d5984c657-b7724            1/1     Running   0          4m43s
kube-system          kube-apiserver-node1                       1/1     Running   1          5m59s
kube-system          kube-controller-manager-node1              1/1     Running   2          5m59s
kube-system          kube-proxy-qt4c4                           1/1     Running   0          5m28s
kube-system          kube-scheduler-node1                       1/1     Running   1          5m59s
kube-system          nodelocaldns-nltqf                         1/1     Running   0          4m43s
local-path-storage   local-path-provisioner-f78b6cbbc-qfkmd     1/1     Running   0          4m52s
```

## Helpful tools

**K9s**

 If you want to easier navigate through K8s cluster, you can install [K9s](https://github.com/derailed/k9s) that offers a terminal UI for Kubernetes related tasks.
