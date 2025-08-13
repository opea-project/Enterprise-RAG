[local]
localhost ansible_connection=local ansible_user=${ssh_user} ansible_python_interpreter=/tmp/Enterprise-RAG/deployment/erag-venv/bin/python3

[all]
${instance_name} ansible_host=${host_ip} ansible_ssh_private_key_file=/home/ubuntu/.ssh/ansible

# Define node groups
[kube_control_plane]
${instance_name}

[kube_node]
${instance_name}

[etcd:children]
kube_control_plane

[k8s_cluster:children]
kube_control_plane
kube_node

# Vars
[k8s_cluster:vars]
ansible_become=true
ansible_user=${ssh_user}
