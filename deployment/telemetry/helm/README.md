# Enterprise-RAG Telemetry Helm Chart

### Assumptions/current state/limitations:

- ChatQnA application is deployed to "chatqa" namespace (check instructions below).
- All telemetry base components (metrics) will be deployed to `monitoring` namespace.

Default Metrics pipeline:

```
pods    -> Prometheus   -> Grafana
```

Information:
- pods and services are directly scrapped by Prometheus, defined by Prometheus-operator CRDs: "PodMonitor" and "ServiceMonitor"

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

##### II a) Install loki and OpenTelemetry collector for logs (with journalctl support) 

This is **recommended** method but requires custom image.

```
helm install telemetry-logs -n monitoring -f charts/logs/values-journalctl.yaml charts/logs
```

**Note** This step is explicit, because of helm [bug](https://github.com/helm/helm/pull/12879), causing that "logs" subchart cannot be deployed together with "telemetry" chart on single node setup (as subchart it cannot nullify required log-writer pod anti affinity and two replicas at least).

##### II b) [Alternatively to IIa] Install loki and OpenTelemetry collector for logs (default image, without journalctl support):
```
helm install telemetry-logs -n monitoring charts/logs
```

"logs" chart deploys:
- loki as logs backend and Grafana datasource,
- OpenTelemetry collector in DaemonSet mode as logs collector only,
- Optionally: OpenSearch, Promtail

Check [logs README.md](charts/logs/README.md#optional-components) for details.

#### III) Install **traces pipeline** telemetry.

Note two step (two charts) installation is required because CRD/CR dependency and WebHooks race condition of "OpenTelemetry operator" and created custom resources (collector/instrumentation):

Install traces **backends**:
```
helm install telemetry-traces --create-namespace charts/traces -n monitoring-traces 
```

Install traces **collector** and **instrumentation**:
```
helm install telemetry-traces-instr charts/trace-instr -n monitoring-traces 
```

Check [tracing README.md](charts/traces/README.md) for details.

#### IV) Verification and access

##### IV a) Access the Grafana:
```
kubectl --namespace monitoring port-forward svc/telemetry-grafana 3000:80
```
on `https://127.0.0.1:3000`
using admin/prom-operator.


##### IV b) Access the Prometheus with kubectl proxy:

For debugging only purposes:
```
kubectl proxy
```

on `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-kube-prometh-prometheus:http-web/proxy/graph`

Note that all scrapping targets should be properly discovered and scrapped here `http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-kube-prometh-prometheus:http-web/proxy/targets?search=&scrapePool=` .

##### IV c) Access alert manager:

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

#### Update HABANA Prometheus exporter
```
cd templates/habana-exporter
wget https://vault.habana.ai/artifactory/gaudi-metric-exporter/yaml/1.17.0/metric-exporter-daemonset.yaml -O metric-exporter-daemonset.yaml
```

### Extra additions

#### a) metrics-server - Kubernetes own "metrics" pipeline

```
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace monitoring-metrics-server --create-namespace
```
or uninstall

```
helm uninstall metrics-server --namespace monitoring
```

#### b) pcm-sensor-server - XEON telemetry

| **WARNING**   | 
| ------------- |
|  PCM-sensor-server is opt-in **experimental** preview feature. Please consider testing in controlled environment, before enabling on production systems. |

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
cat README.md

# WARN: we are using privilged mode (TODO: consider less unsecure version later access through perf-subsystem)
requires: msr module
ssh TARGET_NODE
sudo modprobe msr

helm install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=telemetry
helm upgrade --install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=telemetry
```

b) Check PCM metrics
```
kubectl get -n monitoring daemonset pcm
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

#### Configuration prometheus-kube-stack

When deploying the Prometheus Operator using the `kube-prometheus-stack` Helm chart, additional configuration may be required to monitor certain Kubernetes services. The following sections provide guidance on how to configure monitoring for the `kube-controller-manager`, `kube-etcd`, `kube-proxy`, and `kube-scheduler` components. This issue was well described [here](https://github.com/prometheus-community/helm-charts/issues/204).

##### telemetry-kube-prometheus-kube-etcd

To monitor the `kube-etcd` service, you need to update the `ClusterConfiguration` for `kubeadm` to expose the metrics endpoint. This solution is detailed in a [GitHub issue comment](https://github.com/prometheus-community/helm-charts/issues/204#issuecomment-1003558431)


``` yml
kind: ClusterConfiguration
etcd:
  local:
    extraArgs:
      listen-metrics-urls: http://0.0.0.0:2381
```

Then, adjust the `kube-prometheus-stack` Helm chart values to match the `kube-etcd` metrics service port:

``` yml
kubeEtcd:
  service:
    port: 2381
    targetPort: 2381
```

##### telemetry-kube-prometheus-kube-proxy

The `kube-proxy` service may have issues with Prometheus instances accessing its metrics. The problem and its solution are documented in the `kube-prometheus-stack` chart [README](https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/README.md#kubeproxy).

To resolve this, modify the `kube-proxy` ConfigMap to set the `metricsBindAddress` to `0.0.0.0:10249`:

```console
kubectl -n kube-system edit cm kube-proxy
```

Update the ConfigMap with the following configuration:

```yaml
apiVersion: v1
data:
  config.conf: |-
    apiVersion: kubeproxy.config.k8s.io/v1alpha1
    kind: KubeProxyConfiguration

    metricsBindAddress: 0.0.0.0:10249 # Updated line

kind: ConfigMap
metadata:
  labels:
    app: kube-proxy
  name: kube-proxy
  namespace: kube-system
```

##### telemetry-kube-prometheus-kube-scheduler and kube-scheduler-kind-control-plane

Monitoring the `kube-scheduler` service, as well as the `kube-scheduler-kind-control-plane` if you are using kind, requires meeting certain pre-requisites when using `kubeadm`. These pre-requisites are outlined in the [kube-prometheus documentation](https://github.com/prometheus-operator/kube-prometheus/blob/main/docs/kube-prometheus-on-kubeadm.md#kubeadm-pre-requisites)
.
Ensure that your cluster configuration adheres to these requirements to enable successful monitoring of these components with Prometheus.
By following these steps, you can configure the `kube-prometheus-stack` Helm chart to monitor key Kubernetes services effectively.
