### Helm chart for install telemetry services for Enterprice RAG

#### Assumptions/current state/limitations:

- ChatQnA application is deployed to "chatqa" namespace (check instructions below).
- All telemetry components will be deployed to `monitoring` namespace.
- `kubectl proxy` is running in background (for testing).
- localhost:5000 docker registry is deployed  e.g. with `docker run -d -p 5000:5000 --name local-registry registry:2` or use kind creation script: `example/kind-with-registry-opea-models-mount.sh`

#### Getting started (install telemetry only)

a) Install "rag-telemetry" release from helm source directory:

```
helm dependency build
helm install -n monitoring --create-namespace rag-telemetry .

# or upgrade (takes more time, show --debug to see progress)
helm upgrade --debug --install -n monitoring --create-namespace rag-telemetry .

# reinstall
time helm uninstall -n monitoring rag-telemetry
time helm install -n monitoring --create-namespace rag-telemetry .
```

Please check "Extra additions" (not yet merged into helm chart) for **pcm** and **metrics-server**.


b) Check deployed components pods/monitors and configmaps:
```
kubectl --namespace monitoring get pods 
kubectl --namespace monitoring get servicemonitors -l "release=rag-telemetry"
kubectl --namespace monitoring get podmonitors -l "release=rag-telemetry"
kubectl --namespace monitoring get configmaps 
```

c) Access the grafana:
```
kubectl --namespace monitoring port-forward svc/rag-telemetry-grafana 3000:80
```
on `https://127.0.0.1:3000`
using admin/prom-operator.


d) (For debugging only) Access the Prometheus with kubectl proxy:
```
kubectl proxy
```

on `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/rag-telemetry-kube-prometh-prometheus:http-web/proxy/graph`

Note that all scrapping targets should be properly discovered and scrapped here `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/rag-telemetry-kube-prometh-prometheus:http-web/proxy/targets?search=&scrapePool=` .

e) Access alert manager:

on `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/rag-telemetry-kube-prometh-alertmanager:http-web/proxy/#/alerts`


#### Available metrics and sources:

a) **GMConnector/router** (requires router from branch available here: (https://github.com/opea-project/GenAIInfra/pull/296) or as submodule in /deployment/GenAIInfra:

- `http_server_duration_milliseconds_*` histogram,
- `http_server_request_size_bytes_total`, `http_server_response_size_bytes_total`,
- `http_client_duration_milliseconds_*` histogram,
- `http_client_request_size_bytes_total`, `http_client_response_size_bytes_total`,
- `llm_all_token_latency_milliseconds_bucket`, `llm_first_token_latency_milliseconds_bucket`, `llm_pipeline_latency_milliseconds_bucket`, `llm_next_token_latency_milliseconds_bucket`,

Example:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/router-service:8080/proxy/metrics
```

b) **opea-microservices** (instrumentation using https://github.com/trallnag/prometheus-fastapi-instrumentator):

- `http_requests_total` counter, labels: **status** and **method**
- `http_request_size_bytes` summary (count/sum), labels: **handler**,
- `http_response_size_bytes` summary (count/sum), labels:: **handler**,
- `http_request_duration_seconds_` histogram with labels: **handler**, **method** (extra: service, pod, container, endpoint, service)
- `http_request_duration_highr_seconds_` histogram (no labels),
- `process_resident_memory_bytes`, `process_cpu_seconds_total`, ...

Example:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/llm-svc:llm-uservice/proxy/metrics
```

c) **HABANA metrics exporter**

  - `habanalabs_clock_soc_max_mhz`,
  - `habanalabs_clock_soc_mhz`,
  - `habanalabs_device_config`,
  - `habanalabs_ecc_feature_mode`,
  - `habanalabs_energy`,
  - `habanalabs_kube_info`,
  - `habanalabs_memory_free_bytes`,
  - `habanalabs_memory_total_bytes`,
  - `habanalabs_memory_used_bytes`,
  - `habanalabs_nic_port_status`,
  - `habanalabs_pci_link_speed`,
  - `habanalabs_pci_link_width`,
  - `habanalabs_pcie_receive_throughput`,
  - `habanalabs_pcie_replay_count`,
  - `habanalabs_pcie_rx`,
  - `habanalabs_pcie_transmit_throughput`,
  - `habanalabs_pcie_tx`,
  - `habanalabs_pending_rows_state`,
  - `habanalabs_pending_rows_with_double_bit_ecc_errors`,
  - `habanalabs_pending_rows_with_single_bit_ecc_errors`,
  - `habanalabs_power_default_limit_mW`,
  - `habanalabs_power_mW`,
  - `habanalabs_temperature_onboard`,
  - `habanalabs_temperature_onchip`,
  - `habanalabs_temperature_threshold_gpu`,
  - `habanalabs_temperature_threshold_memory`,
  - `habanalabs_temperature_threshold_shutdown`,
  - `habanalabs_temperature_threshold_slowdown`,
  - `habanalabs_utilization`

Example output:
```
podname=`kubectl get pods -n monitoring -l app.kubernetes.io/name=metric-exporter-ds -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics"
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics" | grep HELP | grep habanalabs
```
   
d) **TGI** metrics (Broken):

Example output:
```
curl -v -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tgi-service-m:tgi/proxy/metrics
```

Check the issue: https://github.com/huggingface/text-generation-inference/issues/2184

e) **TEI**  metrics:

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tei-embedding-svc:tei/proxy/metrics
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tei-reranking-svc:teirerank/proxy/metrics
```

f) **redis-exporter**

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/rag-telemetry-prometheus-redis-exporter:redis-exporter/proxy/metrics
```
- `redis_latency_percentiles_usec` 
- `redis_up`

g) **node-exporter** metrics:

Example output:
```
podname=`kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus-node-exporter -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics"
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics" | grep HELP | grep node_
```

- `node_cpu_seconds_total`  ...


h) **pcm** metrics (installed seperately, BROKEN) - check instructions below
```
podname=`kubectl -n monitoring get pod -l app.kubernetes.io/component=pcm-sensor-server -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics 
```
- `DRAM_Writes`, `Instructions_Retired_Any` ...

#### Enabling Redis dashboard (manually) TODO

1) login to Grafana
2) Go to Administration/Plugins and data/Plugins
3) Search for "redis"
4) Click "Redis by Redis" and install
5) Click "Add new data source"
6) Set Address: to `redis://redis-vector-db.chatqa.svc.cluster.local:6379`
7) Click "Dashboards" tab
8) Import Redis dashboard

#### BOM

Enabled Kubernetes resources and dependent charts:

- opea-components serviceMonitors for ChatQnA application: templates/opea-monitors/
- opea-components Grafana dashboards: files/dasboards/
- subcharts:
  -  https://docs.habana.ai/en/latest/Orchestration/Prometheus_Metric_Exporter.html

  - kube-prometheus-stack:
    - alertmanager
    - exporters (service/endpoints and serviceMonitors): core-dns, kube-api-server, kube-controller-manager, kube-dns, kube-etcd, kube-proxy, kube-scheduler, kubelet
    - grafana dashboards: alertmanager-overview, apiserver, cluster-total, etcd, grafana-overview, k8s-resources-, kubelet, ...
    - prometheus-operator
    - prometheus (single prometheus instance based using Prometheus operator CRD)
      - rules (for Kubernetes derived metrics)
    - thanos-ruler
    - subcharts:
        - grafana
        - kube-state-metrics
        - prometheus-node-exporter
  - prometheus-redis-exporter


Note: redis dashboard is based on:
```
cd helm
curl -sL https://raw.githubusercontent.com/oliver006/redis_exporter/master/contrib/grafana_prometheus_redis_dashboard.json -o files/dashboards/redis-dashboard.json
head files/dashboards/redis-dashboard.json
```

#### Regenerating opea-components serviceMonitors:

Requirements:
- access to Kubernetes with deployed ChatQnA application (with Kubernetes services):
- jq command line tool

##### Check ChatQnA services:
```
kubectl get service -n chatqa -ojson | jq -r '.items[] | .metadata.labels["app.kubernetes.io/instance"] + " " + .metadata.name + " " + .spec.ports[].name + " " + (.spec.ports[].port|tostring)' | while read -r app_instance service_name port_name port; do 
echo app_instance=$app_instance service_name=$service_name port_name=$port_name port=$port
done
```

Generate using below bash template:

based on: https://prometheus-operator.dev/docs/api-reference/api/#monitoring.coreos.com/v1.ServiceMonitorSpec
```
kubectl get service -n chatqa -ojson | jq -r '.items[] | .metadata.labels["app.kubernetes.io/instance"] + " " + .metadata.name + " " + .spec.ports[].name + " " + (.spec.ports[].port|tostring)' | while read -r app_instance service_name port_name port; do 
cat >templates/opea-monitors/${service_name}-serviceMonitor.yaml  <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ${service_name}
  labels:
    release: rag-telemetry
spec:
  namespaceSelector:
    matchNames:
    - chatqa
  selector:
    matchLabels:
      app.kubernetes.io/instance: ${app_instance}
  endpoints:
  - port: "${port_name}"
EOF
done
```

Remove invalid router-service serviceMonitor (missing standard kubernetes labels):

```
rm templates/opea-monitors/8080-serviceMonitor.yaml
```

Check router-service `templates/opea-monitors/router-service-podMonitor.yaml`.

Spec help: https://prometheus-operator.dev/docs/api-reference/api/#monitoring.coreos.com/v1.PodMonitorSpec

Test it with:
```
kubectl apply -n chatqa -f templates/opea-monitors/router-service-podMonitor.yaml
```

#### Update HABANA prometheus exporter
```
cd templates/habana-exporter
wget https://vault.habana.ai/artifactory/gaudi-metric-exporter/yaml/1.17.0/metric-exporter-daemonset.yaml -O metric-exporter-daemonset.yaml
```

#### Deploy OPEA ChatQnA application with patched GMConnector router

##### (Optionally) Create local kind-based cluster with registry and models mounted

**requires kind installed**

```
mkdir -p /opea-models
du -sm /opea-models
bash example/kind-with-registry-opea-models-mount.sh
kind export kubeconfig
docker ps # expected kind-control-plane and kind-registry
docker exec -ti kind-control-plane ls -l /opea-models/                                                                      # required by chatqna "no GMC"
docker exec -ti kind-control-plane bash -c "mkdir -p /mnt/ ; ln -sv /opea-models /mnt/opea-models; ls -l /mnt/opea-models/" # required by chatqn  "with GMC"
kubectl get pods -A
```

##### Build and install GMConnector itself 

- includes manifests for opea micorservices and router

Following instructions are based on `GenAIInfra/microservices-connector/usage_guide.md` to deploy patched gmconnector/router from tihs [PR](https://github.com/opea-project/GenAIInfra/pull/296).

a) Clone patch gmconnector/router source code with instrumented http server/client and custom metrics:
```
cd helm
git clone https://github.com/ppalucki/GenAIInfra example/GenAIInfra
cd example/GenAIInfra
git checkout ppalucki-telemetry-poc
```

b) Build and push gmcconnector and router images to local registry:
```
cd example/GenAIInfra/microservices-connector
make docker.build docker.push DOCKER_REGISTRY=localhost:5000
reg ls -k -f localhost:5000/
```

c) Prepare manifests (microservices and gmc-router) to be used in gmc-config configmap:
```
cd example/GenAIInfra/microservices-connector
export YOUR_HF_TOKEN="PUT YOUR TOKEN HERE"
`find helm/manifests_common/ -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$YOUR_HF_TOKEN#g" {} \;`
git diff

sed -i 's|image: opea/|image: localhost:5000/|' config/gmcrouter/gmc-router.yaml
sed -i 's/IfNotPresent/Always/g' config/gmcrouter/gmc-router.yaml
git diff -- config/gmcrouter/gmc-router.yaml
```

d) Install gmconnector with helm and custom image:
```
cd example/GenAIInfra/microservices-connector/helm
helm install -n default gmc . --set image.repository=localhost:5000/gmcmanager --set image.tag=latest --set image.pullPolicy=Always

# (hack if you don't reinstall gmc connector) use patched gmc-config from ppalucki kind test cluster (router from localhost) 
kubectl delete -n system configmap gmc-config
kubectl create -n system -f example/gmc-configs/gmc-config-ppalucki-image-localhost5000-ns-system.yaml
# (restore from hack) to original jpiasecki gmc-config (gmc-router is missing!?!?)
kubectl delete -n system configmap gmc-config
kubectl create -n system -f example/gmc-configs/gmc-config-jpiasecki-original.yaml
```

e) Install ChatQnA application:

```
cd example/GenAIInfra/microservices-connector
kubectl create ns chatqa
kubectl apply -n chatqa -f config/samples/chatQnA_xeon.yaml
```

f) Check application is working as expected (all pods are ready):

```
kubectl get pods -n chatqa 
```

and send chat query:

```
kubectl proxy # in background
curl -sL -N http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/router-service:8080/proxy/v1/ -H "Content-Type: application/json" -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}'
```

or stress test in loop for metrics:
```
while sleep 1 ; do curl -sL -N http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/router-service:8080/proxy/v1/ -H "Content-Type: application/json" -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}'; done
```

Now go and install telemetry (above).

#### Uninstall ChatQnA app, GMConnector operator and telemetry

```
kubectl delete namespace chatqa
helm uninstall -n default gmc
helm uninstall -n monitoring rag-telemetry
```

#### Extra additions (kubernetes metrics-server)

##### a) metrics-server

```
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace kube-system
```

##### b) pcm-sensor-server

It is work in progress by ppalucki, so it requires deployemt from source:

https://github.com/intel/pcm/pull/727 (images are published but not helm charts).

a) Clone and deploy
```
cd helm
git clone https://github.com/ppalucki/pcm/ example/pcm
cd example/pcm
git checkout ppalucki/helm
cd deployment/pcm

cd example/pcm/deployment/pcm/README.md

# WARN: we're using privilged mode (TODO: consider less unsecure version later access through perf-subsystem)
requires: msr module
ssh dcgaudicluster2 
sudo modprobe msr

helm install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=rag-telemetry
helm upgrade --install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=rag-telemetry
```

b) Check PCM metrics
```
kubectl get -n monitoring daemonset pcm
kubectl get -n monitoring pods 
podname=`kubectl -n monitoring get pod -l app.kubernetes.io/component=pcm-sensor-server -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics | grep L3_Cache_Misses                                                         # source: core
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics | grep DRAM_Writes                                                             # source: uncore
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics | grep Local_Memory_Bandwidth{socket="1",aggregate="socket",source="core"}     # source: RDT
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics | grep DRAM_Joules_Consumed 
```

c) Download PCM dashboard (should be already included in helm-chart)
```
cd helm
podname=`kubectl -n monitoring get pod -l app.kubernetes.io/component=pcm-sensor-server -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/dashboard/prometheus/default -o files/dashboards/pcm-dashboard.json
```

d) Uninstall PCM
```
helm uninstall -n monitoring pcm 
```

