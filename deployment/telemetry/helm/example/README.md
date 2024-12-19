### Deploy local environment using Kind based cluster for development purposes.

#### Prerequisites

- **kind**: https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries
- **make** (required to build GMC operator images)
- **kubectl**: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
- **docker** service running
- optionally **reg** tool to check pushed images (https://github.com/genuinetools/reg)
- assumes environment with proxy (variants for no proxy included)
- disk space ~150GB (for models, images x 3 copies each)
- if you running own (on 5000 port) must be replaced with one script below (otherwise containerd inside kind will not connect because of port conflict)
- check `cat /proc/sys/fs/inotify/max_user_instances` and set `sysctl -w fs.inotify.max_user_instances=8192` to handle journald collector
- time and patience 1h only for initial build/push and pulling (only once, because unmodified layers will be cached in /var/lib/docker (local registry) and /kind-containerd-images (containerd storage))

Run from *root folder* + deployment directory:
```
cd deployment
```

#### 1) Create kind cluster and local registry

```sh
# Create Local registry and kind-control-plane containers:
bash ./telemetry/helm/example/kind-with-registry-opea-models-mount.sh 
kind export kubeconfig
docker ps
kubectl get pods -A
```

#### 2) Build images and deploy everything

First:

**export HF_TOKEN=your-hf-token-here**

Then run from *root folder* of project:

```sh
cd deployment/

TAG=ts`date +%s`
echo $TAG

# no proxy version (use only on system without proxy)
./set_values.sh -g $HF_TOKEN -t $TAG

# proxy version
./set_values.sh -p $http_proxy -u $https_proxy -n $no_proxy -g $HF_TOKEN -t $TAG

# check yaml values
git --no-pager diff microservices-connector/helm/values.yaml

### a) Build images (~1h once, ~50GB)
no_proxy=localhost ./update_images.sh --tag $TAG --build -j 100

# check build progress (output logs in another terminal)
tail -n 0 -f logs/build_*
pgrep -laf 'docker build'
# check build images
docker image ls | grep $TAG

### b) Push images (~2h once, ~20GB)
no_proxy=localhost ./update_images.sh --tag $TAG --push -j 100

# check pushing processes
pgrep -laf 'docker push'
# check pushed images
reg ls -k -f localhost:5000 2>/dev/null | grep $TAG

### c) Deploy everything (~30 once, 70GB)
# Please modify grafana_password for your own
./install_chatqna.sh --tag $TAG --auth --kind --deploy xeon_torch --ui --telemetry --ip 127.0.0.1

# Install or reinstall(upgrade) individual components
./install_chatqna.sh --tag $TAG --kind --auth --upgrade --keycloak_admin_password admin     # namespaces: auth, auth-apisix, ingress-nginx namespaces
./install_chatqna.sh --tag $TAG --kind --deploy xeon_torch --upgrade                        # namespaces: system, chatqa, dataprep
./install_chatqna.sh --tag $TAG --kind --deploy xeon_torch_llm_guard --upgrade              # namespaces: system, chatqa, dataprep
./install_chatqna.sh --tag $TAG --kind --telemetry --upgrade --grafana_password devonly     # namespaces: monitoring, monitoring-namespace
./install_chatqna.sh --tag $TAG --kind --ui --upgrade --ip 127.0.0.1                        # namespaces: erag-ui

# check ChatQnA response
kubectl proxy
pgrep -laf 'kubectl proxy'
curl -sL -N http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/router-service:8080/proxy/ -H "Content-Type: application/json" -d '{"text":"what is the day today?","parameters":{"max_new_tokens":5, "streaming": true}}'

# check DataPrep pipeline
SIZE=100 ; curl -v -N -s -H 'Content-Type: application/json' -o /dev/null http://127.0.0.1:8001/api/v1/namespaces/dataprep/services/router-service:8080/proxy/ -X POST -d '{"files":[{"filename":"file.txt", "data64":"'`head -c $SIZE </dev/random | base64 -w 0 | base64 -w 0`'"}],"links":[]}'

### d) Access Grafana/Prometheus
pgrep -laf 'port-forward'
# or port forwards processes manually
kubectl --namespace monitoring port-forward svc/telemetry-grafana 3000:80
# Grafana: http://127.0.0.1:3000
# Prometheus: http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-kube-prometheus-prometheus:http-web/proxy/graph

### e) Access UI/KeyCloak and Grafana
# Add "127.0.0.1 auth.erag.com grafana.erag.com erag.com" line to /etc/hosts (Linux) or c:\windows\System32\drivers\etc\hosts (Windows)
kubectl port-forward --namespace ingress-nginx svc/ingress-nginx-controller 443:https
# UI: https://erag.com/
# Grafana: https://grafana.erag.com/
# KeyCloak: https://auth.erag.com/

# Passwords for Grafana/Keycloak is given above in command line for installation.
# Passwords for users: 
cat default_credentials.txt

### Optionally install metrics-server (for resource usage metrics)
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace monitoring-metrics-server --create-namespace
```

#### 3) Clean up
```
kind delete cluster
docker rm -f kind-registry

# Warning: first time initialize will take a lot time when following steps are executed:
rm -rf /kind-containerd-images      # removes all pulled images by containerd inside kind (~70GB)
rm -rf /kind-registry               # removes all images stored in registry (~20GB)
rm -rf /kind-local-path-provisioner # removes all images stored in registry (~20GB)
# Warning: Below commands can remove not Enterprise RAG related data
docker system df
docker image prune -a -f            # removed build images local registry (~90GB)
docker system prune -a -f           # removes all containers images inside docker cache (~20GB)
docker volume prune -f              # removes volumes used by local registry (~1GB)
```
