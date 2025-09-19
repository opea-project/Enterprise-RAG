# Telemetry Helm Chart

This Helm chart sets up telemetry infrastructure for the Intel® AI for Enterprise RAG.

## Table of Contents

- [Overview](#overview)
- [Available Metrics and Sources](#available-metrics-and-sources)
- [Getting Started](#getting-started)
  - [Install Metrics Pipeline](#install-metrics-pipeline)
  - [Install Logs Pipeline](#install-logs-pipeline)
  - [Install Traces Pipeline Telemetry](#install-traces-pipeline-telemetry)
- [Bill of Materials](#bill-of-materials)
- [Extra Additions](#extra-additions)
  - [metrics-server – Kubernetes Metrics Pipeline](#metrics-server--kubernetes-own-metrics-pipeline)
  - [pcm-sensor-server – XEON Telemetry](#pcm-sensor-server---xeon-telemetry)
- [Configuration: prometheus-kube-stack](#configuration-prometheus-kube-stack)
  - [kube-etcd Monitoring](#telemetry-kube-prometheus-kube-etcd)
  - [kube-proxy Monitoring](#telemetry-kube-prometheus-kube-proxy)
  - [kube-scheduler Monitoring](#telemetry-kube-prometheus-kube-scheduler-and-kube-scheduler-kind-control-plane)


## Overview

The chart provisions:
 - Prometheus – for metrics collection and storage.
 - Exporters – for exposing metrics from pods and services.
 - Grafana – for visualization of metrics with preconfigured dashboards.
 - AlertManager – for alerting with predefined rules.


Default Metrics pipeline:

```
pods    -> Prometheus   -> Grafana
```

Prometheus scrapes pods and services using Prometheus Operator CRDs: PodMonitor and ServiceMonitor.

This chart should be installed before other telemetry components (logs, traces) due to dependencies on Prometheus and Grafana.

## Available metrics and sources:

Check [METRICS.md](METRICS.md) how to check existing metrics.

## Getting started

Following instruction deploy only telemetry components.

### Install metrics pipeline

This is metrics pipeline and Grafana deployed from helm source **base** directory:

```
helm install telemetry -n monitoring --create-namespace .
```

Base chart deploys:

- Grafana with configured data sources and dashboards
- Prometheus operator, Prometheus and AlertManager instances and Prometheus monitors (for Enterprise RAG components)
- Extra exporters: Habana, Redis, node-exporter, kube-state-metrics

Please check the "Extra additions" section for information on **pcm** and **metrics-server** (not yet merged into the Helm chart).

### Install logs pipeline

This uses "logs" subchart from helm **charts/logs** chart directory:

The **metrics** telemetry requires the "metrics pipeline" to be deployed first.

> [!WARNING]
> Before deploying, make sure that prerequisites/requirements described [logs/README.md](charts/logs/README.md#prerequisites-imagesvolumes) are met (persistent volumes and images).

#### Install loki and OpenTelemetry collector for logs (with journalctl support) 

This is **recommended** method but requires custom image.

```
helm install telemetry-logs -n monitoring -f charts/logs/values-journalctl.yaml charts/logs
```


#### Install loki and OpenTelemetry collector for logs (default image, without journalctl support):
```
helm install telemetry-logs -n monitoring charts/logs
```

"logs" chart deploys:
- loki as logs backend and Grafana datasource,
- OpenTelemetry collector in DaemonSet mode as logs collector only,

Check [logs README.md](charts/logs/README.md#optional-components) for details.

### Install **traces pipeline** telemetry.

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


## Bill of Materials

Telemetry including following components:

- application services Prometheus serviceMonitors for ChatQnA application in [templates/app-monitors](templates/app-monitors).
- infra Prometheus monitors to scrape date from: habana and redis exporter in [templates/infra-monitors](templates/infra-monitors).
- Grafana dashboards for application and infrastructure in [files/dashboards](files/dashboards).
- Habana exporter based on [this](https://docs.habana.ai/en/latest/Orchestration/Prometheus_Metric_Exporter.html)
- subcharts (dependency):
  - logs (subchart):
    - loki
    - opentelemetry-collector
  - traces (subchart):
    - opentelemetry-operator
    - tempo 
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
- (optional) metric-server	
- (optional) pcm-sensor-server

## Extra Additions

### metrics-server – Kubernetes own metrics pipeline

Install:
```
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace monitoring-metrics-server --create-namespace
```
Uninstall:

```
helm uninstall metrics-server --namespace monitoring
```

### pcm-sensor-server - XEON telemetry

> [!WARNING]
> PCM-sensor-server is opt-in **experimental** preview feature. Please consider testing in controlled environment, before enabling on production systems.

It is work in progress by ppalucki, so it requires deployment from source:

https://github.com/intel/pcm/pull/727 (images are published but not helm charts).

#### Clone and deploy
```
cd helm
git clone https://github.com/ppalucki/pcm/ example/pcm
cd example/pcm
git checkout ppalucki/helm
cd deployment/pcm

# check README for further details
cat README.md

# WARNING: We are using privileged mode. (TODO: Consider a more secure version later, accessing through the perf subsystem.)
requires: msr module
ssh TARGET_NODE
sudo modprobe msr

helm install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=telemetry
helm upgrade --install -n monitoring pcm . -f values-direct-privileged.yaml --set cpuLimit=1000m --set cpuRequest=1000m --set memoryLimit=2048Mi --set memoryRequest=2048Mi --set podMonitor=true --set podMonitorLabels.release=telemetry
```

#### Check PCM metrics
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

#### Download PCM dashboard (should be already included in helm-chart)
```
cd helm
podname=`kubectl -n monitoring get pod -l app.kubernetes.io/component=pcm-sensor-server -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/dashboard/prometheus/default -o files/dashboards/pcm-dashboard.json
```

#### Uninstall PCM
```
helm uninstall -n monitoring pcm 
```

### Configuration prometheus-kube-stack

When deploying the Prometheus Operator using the `kube-prometheus-stack` Helm chart, additional configuration may be required to monitor certain Kubernetes services. The following sections provide guidance on how to configure monitoring for the `kube-controller-manager`, `kube-etcd`, `kube-proxy`, and `kube-scheduler` components. This issue was well described [here](https://github.com/prometheus-community/helm-charts/issues/204).

#### telemetry-kube-prometheus-kube-etcd

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

#### telemetry-kube-prometheus-kube-proxy

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

#### telemetry-kube-prometheus-kube-scheduler and kube-scheduler-kind-control-plane

Monitoring the `kube-scheduler` service, as well as the `kube-scheduler-kind-control-plane` if you are using kind, requires meeting certain pre-requisites when using `kubeadm`. These pre-requisites are outlined in the [kube-prometheus documentation](https://github.com/prometheus-operator/kube-prometheus/blob/main/docs/kube-prometheus-on-kubeadm.md#kubeadm-pre-requisites).

Ensure that your cluster configuration adheres to these requirements to enable successful monitoring of these components with Prometheus.
By following these steps, you can configure the `kube-prometheus-stack` Helm chart to monitor key Kubernetes services effectively.
