# Enterprise-RAG Telemetry Helm Chart

### Assumptions/current state/limitations:

- ChatQnA application is deployed to "chatqa" namespace (check instructions below).
- All telemetry components will be deployed to `monitoring` namespace.
- `kubectl proxy` is running in background (for testing).
- localhost:5000 docker registry is deployed  e.g. with `docker run -d -p 5000:5000 --name local-registry registry:2` or use kind creation script: `example/kind-with-registry-opea-models-mount.sh`

### Getting started

Following instruction deploy only telemetry components.

#### I) Install **metrics pipeline** telemetry.

This is metrics pipeline and Grafana deployed from helm source **base** directory:

```
helm install telemetry -n monitoring --create-namespace .
```

Base chart deploys:

- Grafana with configured data sources and dashboards
- Prometheus operator, Prometehus and AlertManager instances and Prometheus monitors (for Enterprise RAG components)
- Extra exporters: Habana, Redis, node-exporter, kube-state-metrics

Please check "Extra additions" (not yet merged into helm chart) for **pcm** and **metrics-server**.

#### II) Install **logs pipeline** telemetry.

This uses "logs" subchart from helm **charts/logs** chart directory:

The **metrics** telemetry requires "a) metric pipeline" to be deployed first.

**WARNING**: Before deploying, make sure that prerequisites/requirements described [logs/README.md](charts/logs/README.md#prerequisites-imagesvolumes) are met (persistent volumes and images).

##### II a) Install loki and otelcol (with journalctl support) 

This is **recommended** method but requires custom image.

```
helm install telemetry-logs -n monitoring -f charts/logs/values-journalctl.yaml charts/logs
```

**Note** This step is explicit, because of helm [bug](https://github.com/helm/helm/pull/12879), causing that "logs" subchart cannot be deployed together with "telemetry" chart on single node setup (as subchart it cannot nullify required log-writer pod anti affinity and two replicas at least).

##### II b) [Alternatively to IIa] Install loki and otelcol (default image without journalctl support):
```
helm install telemetry-logs -n monitoring charts/logs
```

"logs" chart deploys:
- loki as logs backend and Grafana datasource,
- opentelemetry collector in daemonset mode as logs collector only,
- Optionally: OpenSearch, Promtail

Check [logs README.md](charts/logs/README.md#optional-components) for details.

#### III) Verification and access

##### III a) Access the Grafana:
```
kubectl --namespace monitoring port-forward svc/telemetry-grafana 3000:80
```
on `https://127.0.0.1:3000`
using admin/prom-operator.


##### III b) Access the Prometheus with kubectl proxy:

For debugging only purposes:
```
kubectl proxy
```

on `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-kube-prometh-prometheus:http-web/proxy/graph`

Note that all scrapping targets should be properly discovered and scrapped here `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-kube-prometh-prometheus:http-web/proxy/targets?search=&scrapePool=` .

##### III c) Access alert manager:

on `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-kube-prometh-alertmanager:http-web/proxy/#/alerts`

### Available metrics and sources:

Check [metrics files](METRICS.md) how to check existing metrics.

### Bill of materials

Telemetry including following components:

- application services Prometheus serviceMonitors for ChatQnA application in [templates/app-monitors](templates/app-monitors).
- infra Prometheus monitors to scrape date from: habana and redis exporter in [templates/infra-monitors](templates/infra-monitors).
- Grafana dashboards for application and infrastructure in [files/dashboards](files/dashboards).
- Habana exporter based on [this](https://docs.habana.ai/en/latest/Orchestration/Prometheus_Metric_Exporter.html)
- subcharts (depedency):
  - logs (subchart):
    - loki
    - opentelemetry-collector
    - (optional) OpenSearch
    - (optional) promtail
  - prometheus-redis-exporter
  - kube-prometheus-stack:
    - Prometheus operator
    - Prometheus (single prometheus instance based using Prometheus operator CRD) with alerts and rules (for Kubernetes derived metrics)
    - AlertManager
    - Extra Kubernetes exporters: core-dns, kube-api-server, kube-controller-manager, kube-dns, kube-etcd, kube-proxy, kube-scheduler, kubelet
    - Grafana dashboards: alertmanager-overview, apiserver, cluster-total, etcd, grafana-overview, k8s-resources-, kubelet, ...
    - Thanos-ruler
    - Subcharts:
      - grafana
      - kube-state-metrics
      - prometheus-node-exporter
	

Note: Redis dashboard is based on:
```
cd helm
curl -sL https://raw.githubusercontent.com/oliver006/redis_exporter/master/contrib/grafana_prometheus_redis_dashboard.json -o files/dashboards/redis-dashboard.json
head files/dashboards/redis-dashboard.json
```

#### Update HABANA prometheus exporter
```
cd templates/habana-exporter
wget https://vault.habana.ai/artifactory/gaudi-metric-exporter/yaml/1.17.0/metric-exporter-daemonset.yaml -O metric-exporter-daemonset.yaml
```

### Extra additions

#### a) metrics-server - Kubernetes own "metrics" pipeline

```
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace monitoring
```
or uninstall

```
helm uninstall metrics-server --namespace monitoring
```

#### b) pcm-sensor-server - XEON telemetry

It is work in progress by ppalucki, so it requires deployemt from source:

https://github.com/intel/pcm/pull/727 (images are published but not helm charts).

a) Clone and deploy
```
cd helm
git clone https://github.com/ppalucki/pcm/ example/pcm
cd example/pcm
git checkout ppalucki/helm
cd deployment/pcm

# check README for further details
cat example/pcm/deployment/pcm/README.md

# WARN: we are using privilged mode (TODO: consider less unsecure version later access through perf-subsystem)
requires: msr module
ssh dcgaudicluster2 
sudo modprobe msr

helm install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=telemetry
helm upgrade --install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=telemetry
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

