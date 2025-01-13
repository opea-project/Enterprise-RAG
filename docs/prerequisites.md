# Prerequisites for Enterprise RAG

This comprehensive guide outlines the essential prerequisites for deploying and using the Enterprise RAG solution. The goal of this guide is to ensure that users have a solid foundation in place before proceeding with the installation and configuration of their Enterprise RAG solution.

## Support matrix
|         |                                                                                                           |
|--------------------|--------------------------------------------------------------------------------------------------------------------|
| Operating System   | Ubuntu 22.04                                                               |
| Hardware Platforms | 4th Gen Intel® Xeon® Scalable processors<br>5th Gen Intel® Xeon® Scalable processors<br>3rd Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator<br>4th Gen Intel® Xeon® Scalable processors and Intel® Gaudi® 2 AI Accelerator |
| Kubernetes Version   | 1.29
| Gaudi Firmware Version   | 1.18.0

## Kubernetes Cluster
Deploy Kubernetes using Kubespray `(v2.25.0)` on a remote machine, followed by configuration and installation steps for the master node. The following steps show how this can be done using `Kubespray`.

-   The following instructions must be executed on a host machine that has network access to the Kubernetes cluster.
-   It is assumed that Kubespray will not be run directly on the machines where Kubernetes is intended to be installed.

To be executed on a remote machine that has network access to the Gaudi cluster, meaning you should be able to SSH into a machine within the GPU cluster:

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
git checkout v2.25.0
pip install -U -r requirements.txt
```

In Kubespray, the `inventory` directory holds configurations for each cluster in separate subdirectories. The `inventory/sample` folder offers a template configuration for initializing new Kubernetes clusters.

Copy the inventory/sample folder and create your custom inventory:
```bash
cp -r inventory/sample/ inventory/mycluster
```

#### Single Node Example Configuration
Next step is to create a `hosts.yaml` file in directory  `inventory/mycluster`. `hosts.yaml` defines the structure and roles of nodes within a Kubernetes cluster

```bash
# use any text editor to create and edit the  hosts.yaml file
vi inventory/mycluster/hosts.yaml
```
An example of `hosts.yaml` for a single-node cluster is shown below:
```yaml
all:
  hosts:
    node1:
      ansible_host: <K8s host ip>
      ip: <K8s host ip>
      access_ip: <K8s host ip>
      ansible_user: sdp
  children:
    kube_control_plane:
      hosts:
        node1:
    kube_node:
      hosts:
        node1:
    etcd:
      hosts:
        node1:
    k8s_cluster:
      children:
        kube_control_plane:
        kube_node:
    calico_rr:
      hosts: {}
```
  -   `ansible_host`: Specifies the IP address of the node. This is the address Ansible uses to communicate with the node.
    -   `ip`: Typically the same as `ansible_host`, used by Kubernetes components to communicate with the node.
    -   `access_ip`: Also the IP used for accessing the node, can be different in complex network configurations where internal and external IPs differ.
    -   `ansible_user`: The username is the Linux user account name that Ansible will use when it connects to the node, here set to `sdp`.

Suppose the IP address of your node is `100.51.110.245`, which you can verify by inspecting the output of `ifconfig` within the Ethernet interface section. Assuming there is a Linux user named `user` with a home directory set up, your `hosts.yaml` file for a Kubespray configuration would be structured as follows:

```yaml
all:
  hosts:
    node1:
      ansible_host: localhost
      ip: 100.51.110.245
      access_ip: 100.51.110.245
      ansible_user: user
  children:
    kube_control_plane:
      hosts:
        node1:
    kube_node:
      hosts:
        node1:
    etcd:
      hosts:
        node1:
    k8s_cluster:
      children:
        kube_control_plane:
        kube_node:
    calico_rr:
      hosts: {}
```

#### Network Settings

Install `sshpass` to be able to send machine credentials via Ansible scripts:
```bash
sudo apt-get install sshpass
```
if you are behing a corporate VPN, setup proxy by editing the `all.yaml` file:

```bash
# Edit proxy settings and save file
vi inventory/mycluster/group_vars/all/all.yaml
```

>**WARNING:** Don't change the `no_proxy` variable.

## CSI Driver

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

## Reset Cluster

`reset.yml` is the name of the playbook file used to clean up a Kubernetes cluster installation. It will remove Kubernetes components, dependencies, and configurations from the nodes listed in the `mycluster` inventory.

Reset K8s cluster to make sure we are making install on a clean environment:

```bash
ansible-playbook -i inventory/mycluster/hosts.yaml  --become --become-user=root -e override_system_hostname=false -kK reset.yml
```
>**Note:**  If you want to skip being prompted for passwords, remove the `-kK` options. The `-kK` flags prompt for the SSH password (`-k`) and the sudo password (`-K`). 

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

## Install Cluster

`cluster.yml` is the playbook file that will be executed. It contains the tasks that will configure the nodes as per the roles and settings defined within `mycluster`, for setting up or managing the cluster.

```bash
ansible-playbook -i inventory/mycluster/hosts.yaml --become --become-user=root -e override_system_hostname=false -kK cluster.yml
```
>**Note:**  If you want to skip being prompted for passwords, remove the `-kK` options. The `-kK` flags prompt for the SSH password (`-k`) and the sudo password (`-K`). 

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

## Setting Up and Verifying Kubernetes Cluster Access


```bash
# create the `.kube` folder
mkdir ~/.kube
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
# change owner to user 
sudo chown -R <username>:<username> ~/.kube
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
## Gaudi Software Stack
To fully utilize the Enterprise RAG solution, LLMs must be run on Gaudi accelerator hardware, which requires proper setup and preparation prior to use. The following steps must be performed after successful installation and testing of the K8s cluster.

Install Habana Container Runtime:
```bash
sudo apt install -y habanalabs-container-runtime
```

Setup `/etc/containerd/config.toml` to point to habana-container-runtime:
>**Important:** Execute the following command directly in the terminal. Do not manually edit the `/etc/containerd/config.toml` file. This ensures that the configuration is set correctly without formatting issues.

```
sudo tee /etc/containerd/config.toml <<EOF
disabled_plugins = []
version = 2

[plugins]
  [plugins."io.containerd.grpc.v1.cri"]
    [plugins."io.containerd.grpc.v1.cri".containerd]
      default_runtime_name = "habana"
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.habana]
          runtime_type = "io.containerd.runc.v2"
          [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.habana.options]
            BinaryName = "/usr/bin/habana-container-runtime"
  [plugins."io.containerd.runtime.v1.linux"]
    runtime = "habana-container-runtime"
EOF
```
Restart the containerd service and verify that the status is `active`:
```bash
sudo systemctl restart containerd
sudo systemctl status containerd
```

Uncomment the following lines in `/etc/habana-container-runtime/config.toml` and set to `false` if `true`:

```
#mount_accelerators = false
.
.
.
#visible_devices_all_as_default = false

```
For more details, refer to the [Gaudi Firmware installation](https://docs.habana.ai/en/latest/Installation_Guide/Bare_Metal_Fresh_OS.html#driver-fw-install-bare) guide.

## Install K8s Plugin

Follow the instructions in [Intel Gaudi Device Plugin for Kubernetes](https://docs.habana.ai/en/latest/Orchestration/Gaudi_Kubernetes/Device_Plugin_for_Kubernetes.html) under the `Deploying Intel Gaudi Device Plugin for Kubernetes` section to install the device plugin.

Verify that the plugin is installed successfully by running `kubectl get pods -A`:
```
NAMESPACE            NAME                                       READY   STATUS    RESTARTS   AGE
habana-system        habanalabs-device-plugin-daemonset-gjs67   1/1     Running   0          67s
kube-system          calico-kube-controllers-68485cbf9c-dr9vd   1/1     Running   0          46m
kube-system          calico-node-gnxk9                          1/1     Running   0          47m
kube-system          coredns-69db55dd76-4zq74                   1/1     Running   0          46m
kube-system          dns-autoscaler-6d5984c657-b7724            1/1     Running   0          46m
kube-system          kube-apiserver-node1                       1/1     Running   1          47m
kube-system          kube-controller-manager-node1              1/1     Running   2          47m
kube-system          kube-proxy-qt4c4                           1/1     Running   0          47m
kube-system          kube-scheduler-node1                       1/1     Running   1          47m
kube-system          nodelocaldns-nltqf                         1/1     Running   0          46m
local-path-storage   local-path-provisioner-f78b6cbbc-qfkmd     1/1     Running   0          46m
```
You should see a new namespace called `habana-system`.

To check is to verify if Gaudi resources are available on the node, run:
```bash
kubectl describe node node1 | grep habana.ai/gaudi
```
You should see the following output:
```
habana.ai/gaudi: 8
habana.ai/gaudi: 8
habana.ai/gaudi 8 8
```

 You have successfully installed and verified the prerequisites on your system. Proceed to the [Getting Started Guide](./getting_started.md) to learn how to deploy and configure the Enterprise RAG Solution.
