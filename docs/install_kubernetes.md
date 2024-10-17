## How to deploy K8s using Kubespray

This instruction illustrates how to deploy K8s via Kubespray to have a valid configuration for running Enterprise RAG. 

Bellow instructions should be executed on the host that has access to the K8s cluster.
We assume we do not run Kubespray directly on the machine where we want to have K8s installed.

### To be executed on a remote machine 

- Clone Kubespray repository `git clone https://github.com/kubernetes-sigs/kubespray.git`
- Execute the below commands to set a virtual environment from which e will run Kubespray ansible scripts:
```
sudo apt update
sudo apt install python3-venv
VENVDIR=kubespray-venv
KUBESPRAYDIR=kubespray
python3 -m venv $VENVDIR
source $VENVDIR/bin/activate
cd $KUBESPRAYDIR
# Check out the latest release version of the tag for Kubespray.
git checkout v2.25.0
pip install -U -r requirements.txt
```

**_WARNING:_**   Make sure you have not made any changes to the repository as git checkout would not pass and would lead to unexpected behavior.

- copy inventory/samples folder and create your own inventory :`cp -r inventory/sample/ inventory/mycluster`
- create hosts.yaml file in `inventory/mycluster`, example for single node cluster bellow:
```
all:
  hosts:
    node1:
      ansible_host: <K8s host ip>
      ip: <K8s host ip>
      access_ip: <K8s host ip>
      ansible_user: ubuntu
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

- install sshpass to be able to send machine credentials via Ansible scripts:
`sudo apt-get install sshpass`

- make changes to your inventory
  - setup proxy in `inventory/mycluster/group_vars/all/all.yaml`
  - **_WARNING:_**  don't change `no_proxy` variable
  - enable local_host provisioner in `inventory/mycluster/group_vars/k8s_cluster/addons.yml` and point it to `/mnt` folder
```
local_path_provisioner_enabled: true
# local_path_provisioner_namespace: "local-path-storage"
# local_path_provisioner_storage_class: "local-path"
# local_path_provisioner_reclaim_policy: Delete
local_path_provisioner_claim_root: /mnt
```

- reset K8s cluster to make sure we are making install on a clean environment: `ansible-playbook -i inventory/mycluster/hosts.yaml  --become --become-user=root -e override_system_hostname=false -kK reset.yml`
- install K8s cluster `ansible-playbook -i inventory/mycluster/hosts.yaml  --become --become-user=root -e override_system_hostname=false -kK cluster.yml`
- wait for the successful execution of the Ansible playbook

### Execute on K8s master node
- create .kube folder `mkdir ~/./kube`
- next `cp /etc/kubernetes/admin.conf ~/.kube/config`
- verify if the K8s cluster is working `kubectl get pods -A`.
- verify that all pods are in running state.


