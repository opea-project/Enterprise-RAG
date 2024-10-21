## How to deploy K8s using Kubespray

This instruction illustrates how to deploy K8s via Kubespray to have a valid configuration for running Enterprise RAG.

Bellow instructions should be executed on the host that has access to the K8s cluster. We assume we do not run Kubespray directly on the machine where we want to have K8s installed.

### To be executed on a remote machine 

- Clone Kubespray repository:
  ```bash
  git clone https://github.com/kubernetes-sigs/kubespray.git
  ```
- Execute the below commands to set a virtual environment from which we will run the Kubespray Ansible scripts:
  ```
  sudo apt update
  sudo apt install python3-venv

  VENVDIR=kubespray-venv
  KUBESPRAYDIR=kubespray

  python3 -m venv $VENVDIR
  source $VENVDIR/bin/activate
  
  # Check out the latest release version tag of kubespray.
  cd $KUBESPRAYDIR
  git checkout v2.25.0
  pip install -U -r requirements.txt
  ```

  **_WARNING:_** Make sure you have not made any changes to the repository as git checkout would not pass and would lead to unexpected behavior.

- Copy the inventory/sample folder and create your custom inventory:
  ```bash
  cp -r inventory/sample/ inventory/mycluster
  ```
- Create a `hosts.yaml` file in folder `inventory/mycluster`. An example for a single-node cluster is shown below:
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

- Install sshpass to be able to send machine credentials via Ansible scripts:
  ```bash
  sudo apt-get install sshpass
  ```

- Make changes to your inventory. Setup proxy in `inventory/mycluster/group_vars/all/all.yaml`
  **_WARNING:_** Don't change `no_proxy` variable.
- Enable *local_host_provisioner* in `inventory/mycluster/group_vars/k8s_cluster/addons.yml` and point it to `/mnt` folder:
  ```
  local_path_provisioner_enabled: true
  # local_path_provisioner_namespace: "local-path-storage"
  # local_path_provisioner_storage_class: "local-path"
  # local_path_provisioner_reclaim_policy: Delete
  local_path_provisioner_claim_root: /mnt
  ```

- Reset K8s cluster to make sure we are making install on a clean environment: 
  ```bash
  ansible-playbook -i inventory/mycluster/hosts.yaml  --become --become-user=root -e override_system_hostname=false -kK reset.yml
  ```
  If you want to skip being prompted for passwords, remove the -kK options.
- Install K8s cluster:
  ```bash
  ansible-playbook -i inventory/mycluster/hosts.yaml --become --become-user=root -e override_system_hostname=false -kK cluster.yml
  ```
- Wait for the successful execution of ansible-playbook

### Execute on K8s master node
- create .kube folder `mkdir ~/.kube`
- next `cp /etc/kubernetes/admin.conf ~/.kube/config`
- verify if the K8s cluster is working `kubectl get pods -A`.
- verify that all pods are in running state.