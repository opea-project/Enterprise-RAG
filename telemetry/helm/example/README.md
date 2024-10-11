### Deploy local environment using Kind based cluster for development purposes.

#### Prerequisites

- **kind**: https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries
- Go language: https://go.dev/doc/install
- kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
- docker service running
- optionally "reg" tool to check pushed images (https://github.com/genuinetools/reg)
- assumes environment with proxy
- disk space ~150GB (for models, images x 3 copies each)
- local registry (only if on :5000 port) must be replaced with one script below (otherwise containerd inside kind will not connect)
- plenty of time and patience 3-4h for initial build/push and pulling (only once, because unmodified layers will be cached in /var/lib/docker (local registry) and /kind-containerd-images (containerd storage))

Run from *root folder* + deployment directory:
```
cd deployment
```

#### 1) Create kind cluster and local registry

```sh
# Create Local registry and kind-control-plane containers (~3GB, ~2 minutes):
time bash ../telemetry/helm/example/kind-with-registry-opea-models-mount.sh 
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

./set_values.sh -p $http_proxy -u $https_proxy -n $no_proxy -g $HF_TOKEN -t $TAG
# check yaml values
git --no-pager diff microservices-connector/helm/values.yaml

### a) Build images (~1h once, ~50GB)
time no_proxy=localhost ./update_images.sh --tag $TAG --build
# check build images
docker image ls | grep $TAG

### b) Push images (~2h once, ~20GB)
time no_proxy=localhost ./update_images.sh --tag $TAG --push
# check pushed images
reg ls -k -f localhost:5000 2>/dev/null | grep $TAG

### c) Deploy everything (~30 once, 70GB)
time ./install_chatqna.sh --tag $TAG --kind --deploy xeon_torch --ui --telemetry  --upgrade
# check ChatQnA response
kubectl proxy
pgrep -laf 'kubectl proxy'
curl -sL -N http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/router-service:8080/proxy/ -H "Content-Type: application/json" -d '{"text":"what is the day today?","parameters":{"max_tokens":8, "max_new_tokens":8, "do_sample": true}}'

### d) Access UI
pgrep -laf 'port-forward'
# or port forwards processes manually
kubectl --namespace monitoring port-forward svc/telemetry-grafana 3000:80
kubectl port-forward --namespace rag-ui svc/ui-chart 4173:4173
kubectl port-forward --namespace auth svc/keycloak 1234:80
# UI: http://127.0.0.1:4173 
# Grafana: http://127.0.0.1:3000
```

#### 3) Clean up
```
kind delete cluster

# Warning: first time initialize will take a lot time when following steps are executed:
docker rm -f kind-registry
rm -rf /kind-containerd-images      # removes all pulled images by containerd inside kind (~70GB)
rm -rf /mnt/opea-models             # removes all models used by model servers (~30GB)
docker system df
docker system prune -a -f           # removes all containers images inside docker cache (~20GB)
docker volume prune -f              # removes volumes used by local registry (~63GB)
docker image prune -a -f            # removed build images local registry (~90GB)
```
