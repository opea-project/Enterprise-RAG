${instance_name} ansible_connection=local ansible_user=${ssh_user} ansible_python_interpreter=/home/ubuntu/erag-venv/bin/python3

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
