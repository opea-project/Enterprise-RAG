#!/bin/bash
set -o errexit

# Prompt the user
echo "Due to recent docker hub rate-limit changes for unauthenticated users you may experience issues with pulling images from docker hub."
echo "To avoid this issue, you can use docker credentials in kind cluster."
echo ""
prompt="Do you want to use docker credentials in kind cluster? (y/n): "

registry_auth_config=""

# Check the user input
while true; do
    read -p "$prompt" -n 1 -s -t 5 reply || (( $? > 128 ))
    case $reply in
        Y|y)
          echo ""
          read -p "Enter Docker username: " docker_login
          read -s -p "Enter Docker password: " docker_password
          echo ""

          docker logout
          echo "$docker_password" | docker login --username $docker_login --password-stdin

          success=$?

          if [ $success -ne 0 ]; then
            echo "Failed to login to docker hub. Possibly wrong credentials. Exiting..."
            exit 1
          fi

          registry_auth_config=$(cat <<EOF
  [plugins."io.containerd.grpc.v1.cri".registry.configs."docker.io".auth]
    username = "$docker_login"
    password = "$docker_password"
EOF
)
        break;;
        ""|N|n)
          echo ""
          echo "Skipping docker credentials in kind cluster."
          break;;
        *) ;;
    esac
done

# Add kind-registry to env no_proxy. It will be used in kind container.
if ! echo "$no_proxy" | grep -q "kind-registry"; then
  export no_proxy="${no_proxy},kind-registry"
fi

# 1. Create registry container unless it already exists
reg_name='kind-registry'
reg_port='5000'
if [ "$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)" != 'true' ]; then
  docker run \
    -d -v /kind-registry:/var/lib/registry --restart=always -p "127.0.0.1:${reg_port}:5000" --network bridge --name "${reg_name}" \
    registry:2
fi

# 2. Create kind cluster with containerd registry config dir enabled
# TODO: kind will eventually enable this by default and this patch will
# be unnecessary.
#
# See:
# https://github.com/kubernetes-sigs/kind/issues/2875
# https://github.com/containerd/containerd/blob/main/docs/cri/config.md#registry-configuration
# See: https://github.com/containerd/containerd/blob/main/docs/hosts.md
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraMounts:
  - hostPath: /var/log/journal
    containerPath: /var/log/journal
  - hostPath: /kind-containerd-images
    containerPath: /var/lib/containerd/
  - hostPath: /kind-local-path-provisioner
    containerPath: /opt/local-path-provisioner
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    controllerManager:
      extraArgs:
        bind-address: 0.0.0.0
    scheduler:
      extraArgs:
        bind-address: 0.0.0.0
    etcd:
      local:
        extraArgs:
          listen-metrics-urls: http://0.0.0.0:2381

containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry]
    config_path = "/etc/containerd/certs.d"
$registry_auth_config
EOF

# 3. Add the registry config to the nodes
#
# This is necessary because localhost resolves to loopback addresses that are
# network-namespace local.
# In other words: localhost in the container is not localhost on the host.
#
# We want a consistent name that works from both ends, so we tell containerd to
# alias localhost:${reg_port} to the registry container when pulling images
REGISTRY_DIR="/etc/containerd/certs.d/localhost:${reg_port}"
for node in $(kind get nodes); do
  docker exec "${node}" mkdir -p "${REGISTRY_DIR}"
  cat <<EOF | docker exec -i "${node}" cp /dev/stdin "${REGISTRY_DIR}/hosts.toml"
[host."http://${reg_name}:5000"]
EOF
done

# 4. Connect the registry to the cluster network if not already connected
# This allows kind to bootstrap the network but ensures they're on the same network
if [ "$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' "${reg_name}")" = 'null' ]; then
  docker network connect "kind" "${reg_name}"
fi

# 5. Document the local registry
# https://github.com/kubernetes/enhancements/tree/master/keps/sig-cluster-lifecycle/generic/1755-communicating-a-local-registry
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${reg_port}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

# Wait for ready
kubectl wait --for=condition=Ready pod -n kube-system --all

# Update kube-proxy cm with proper value of metricsBindAddress
kubectl get cm kube-proxy -n kube-system -o yaml | sed 's/metricsBindAddress: ""/metricsBindAddress: 0.0.0.0:10249/' | kubectl apply -f -

### Own CSI driver to be able to cache PVC for model-servers (required new version of local-path-provisioner)
# 1) Install new version of local-path-provisioner that support "parameters"
# not needed after kind issue with old version of local-path-provisioner (overwrite with never version) until https://github.com/kubernetes-sigs/kind/issues/3810 is resolved
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.30/deploy/local-path-storage.yaml
kubectl wait --for=condition=Ready pod -n kube-system --all
# 2) keycloak: we cannot reuse data from previous PVC for keycloak so lets clear its contents
rm -rf /kind-local-path-provisioner/auth/data-keycloak-postgresql-0/
# 3) reconfigure 
kubectl delete sc standard      # delete original
kubectl delete sc local-path    # delete one provided by local-path-install

script_dir=$(dirname "$(realpath "$0")")
kubectl apply -f $script_dir/sc.yaml      # create our own dataclass that will reuse directories on hosts based on PVC name
