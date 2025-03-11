# Deploy Intel&reg; AI for Enterprise RAG using Kind based cluster for development purposes
To deploy Intel&reg; AI for Enterprise RAG locally on Intel&reg; Xeon without kubespray, use kind. Note that this setup is less optimal than kubespray and incompatible with Intel&reg; Gaudi.

## Prerequisites

- **kind**: https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries
- **kubectl**: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
- **docker** service running
- *optionally:* **reg** tool to check pushed images (https://github.com/genuinetools/reg)
- disk space ~150GB (for models, images x 3 copies each)
- if you are running your own (on 5000 port) must be replaced with one script below (otherwise containerd inside kind will not connect because of port conflict)
- check `cat /proc/sys/fs/inotify/max_user_instances` and set `sysctl -w fs.inotify.max_user_instances=8192` to handle journald collector

Run from root folder + deployment directory:
```
cd deployment/
```

## 1. Create kind cluster and local registry

Initialize kind cluster and create a local registry.

```bash
# Create Local registry and kind-control-plane containers:
bash ./telemetry/helm/example/kind-with-registry-opea-models-mount.sh
kind export kubeconfig
docker ps
kubectl get pods -A
```

## 2. Build images and deploy everything

Set the configuration parameters. Skip `TAG` by removing `-t $TAG` for every command if you want to build and run the deployment on the `latest`. For proxy related environments, follow `proxy version`.

Retrieve your HuggingFace Token [here](https://huggingface.co/settings/tokens).

```bash
export HF_TOKEN=your-hf-token-here
cd deployment/

TAG=ts`date +%s`
echo $TAG

# no proxy version (use only on system without proxy)
./set_values.sh -g $HF_TOKEN -t $TAG

# proxy version
./set_values.sh -p $http_proxy -u $https_proxy -n $no_proxy -g $HF_TOKEN -t $TAG
```

Check your changes with following command:

```bash
# check yaml values
git --no-pager diff microservices-connector/helm/values.yaml
```

Build the images and push them to the registry. Reminder: skip `TAG` by removing `-t $TAG` for every command if you want to build and run the deployment on the `latest`.

### a) Build images (~1h once, ~50GB)
```bash
no_proxy=localhost ./update_images.sh --build -j 100 --tag $TAG

# check build progress (output logs in another terminal)
tail -n 0 -f logs/build_*
pgrep -laf 'docker build'
# check built images
docker image ls | grep $TAG
```

### b) Push images (~2h once, ~20GB)
```bash
no_proxy=localhost ./update_images.sh --push -j 100 --tag $TAG

# check pushing processes (output logs in another terminal)
pgrep -laf 'docker push'
# check pushed images
reg ls -k -f localhost:5000 2>/dev/null | grep $TAG
```

Deploy the pipeline. Choose a command that suits your needs. More information on install_chatqna.sh parameters can be found [here](../deployment/README.md).

### c) Deploy everything
```bash
./install_chatqna.sh --auth --kind --deploy xeon_torch_llm_guard --ui --telemetry --tag $TAG

# Install or reinstall(upgrade) individual components
./install_chatqna.sh --tag $TAG --kind --auth --upgrade --keycloak_admin_password admin     # namespaces: auth, auth-apisix, ingress-nginx namespaces
./install_chatqna.sh --tag $TAG --kind --deploy xeon_torch --upgrade                        # namespaces: system, chatqa, dataprep
./install_chatqna.sh --tag $TAG --kind --deploy xeon_torch_llm_guard --upgrade              # namespaces: system, chatqa, dataprep
./install_chatqna.sh --tag $TAG --kind --telemetry --upgrade --grafana_password devonly     # namespaces: monitoring, monitoring-namespace
./install_chatqna.sh --tag $TAG --kind --ui --upgrade                                       # namespaces: erag-ui
```

To verify that the deployment was successful, run the following command:
```bash
./test_connection.sh
```

Check out following commands for any additional needs.

### e) Access UI/KeyCloak and Grafana

In order to access UI or Grafana, follow instructions available in [deployment/README.md](../deployment/README.md#access-the-uigrafana).

Default passwords are available in `default_credentials.txt`. Change the passwords after first succesful login.
```bash
cat default_credentials.txt
```

### (Optionally) install metrics-server (for resource usage metrics)
```bash
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace monitoring-metrics-server --create-namespace
```

## 3. Clean up
For clean up, check out following commands.

```bash
kind delete cluster
docker rm -f kind-registry

# Warning: first time initialization will take a lot time when following steps are executed:
rm -rf /kind-containerd-images      # removes all pulled images by containerd inside kind
rm -rf /kind-registry               # removes all images stored in registry
rm -rf /kind-local-path-provisioner # removes all images stored in registry

# Warning: Below commands can also remove not only Enterprise RAG related data
docker system df
docker image prune -a -f            # removed built images local registry
docker system prune -a -f           # removes all containers images inside docker cache
docker volume prune -f              # removes volumes used by local registry
```
