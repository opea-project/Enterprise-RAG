## Enterprise RAG Telemetry Logs Helm subchart

### Introduction

Logs chart allows to deploy "logs" pipeline in following configurations:

1) Default Logs pipeline (not custom image needed, but not logs from systemd units):


```
pods            -> otelcol/default      -> loki
```

2) (recommended) Logs pipeline with custom otelcol with journald support:

```
pods
journald        -> otelcol/journalctl   -> loki
```

3) Logs Pipeline with additional OpenSearch logs backend:

```
pods
journald        -> otelcol              -> loki
                                          opensearch
```

4) Logs pipeline without otelcol but collects both pods logs and systemd units logs:

```
pods
journald        -> promtail             -> loki
```

5) All above combined

```
pods
journald        -> promtail             -> loki

pods
journald        -> otelcol/journalctl   -> loki
                                           opensearch
```



### Getting started

#### Install metrics and logs telemetry

##### 1) Install "base telemetry" from parent "deployment/helm" directory

As **"telemetry"** release:
```
helm install telemetry -n monitoring ../..
```

##### 2a) Install "logs" subchart 

(Recommended!) Deploy using custom `otelcol-contrib-journalctl` image for journald logs as **"telemetry-logs"** release `[loki, otelcol/journalctl]`:
```
helm install telemetry-logs -n monitoring -f values-journalctl.yaml .
```

or use local registry and debug for development:
```
helm install telemetry-logs -n monitoring -f values-journalctl.yaml -f values-journalctl-devel.yaml .
```

Alternatively deploy default version (no custom image, no systemd/journald logs available) as **"telemetry-logs"** release `[loki, otelcol/default]`:
```
helm install telemetry-logs -n monitoring .
```

**Notice**: below is mostly for development purposes

##### 2b) [Alternatively] Install "logs" and "logs-otelcol" as **separate** releases.

Install "loki" logs backend only as **"telemetry-logs"** release `[loki]`:
```
helm install telemetry-logs -n monitoring --set otelcol-logs.enabled=false . 
```

Install "otelcol" logs collector **only** (without journalctl) as **"telemetry-logs-otelcol"** release `[otelcol/default]`:
```
helm install telemetry-logs-otelcol -n monitoring --set loki.enabled=false .
```

Install "otelcol" logs collector (with journalctl) only as **"telemetry-logs-otelcol"** release  `[otelcol/journalctl]`:
```
helm upgrade --install telemetry-logs-otelcol -n monitoring -f values-journalctl.yaml -f values-journalctl-devel.yaml --set loki.enabled=false .
```

#### Optional components.

##### a) OpenSearch logs backend

Installed as upgrade to **"telemetry-logs"** release `[loki, otelcol/journalctl, opensearch]`:

```
helm upgrade --install telemetry-logs -n monitoring -f values-journalctl.yaml -f values-opensearch.yaml .
```

##### b) Promtail logs collector

If you don't want to use custom image and one wants to have to access to systemd/journalctl logs, then you need log collector that can collect journald systemd unit logs.
Promtail replaces otelcol and collects pods logs as well as systemd units logs.

Both Promtail and otelcol can be deployed together (both generate different set of indexes/labels) in Loki.
Logs from Promtail are directly transferred in Loki (otelcol is not used!).

Deployed as separate helm chart as **"telemetry-logs-promtail"** release `[promtail]`:

```
helm upgrade --install telemetry-logs-promtail -n monitoring -f values-promtail.yaml .
```

### Uninstall and data clean up

#### 1) Uninstall **logs** pipeline:

```
helm uninstall telemetry -n monitoring
helm uninstall telemetry-logs -n monitoring
```

**WARNING** data loss:

Clean up old LOKI data 
```
kubectl delete pvc -n monitoring -l app.kubernetes.io/instance=telemetry-logs
kubectl delete pvc -n monitoring -l app=minio,release=telemetry-logs
kubectl delete -f loki-volumes.yaml
ssh dcgaudicluster2
# DANGERUOES !
sudo find /mnt/k8stelemetryvolumes -mindepth 2 -delete -print
kubectl create -f loki-volumes.yaml
```

#### 2) Uninstall optional

```
helm uninstall telemetry-logs-otelcol -n monitoring
helm uninstall telemetry-logs-promtail -n monitoring
```

### Prerequisites (images/volumes)

#### 1) OpenTelemetry collector requirements

##### 1a) Build custom image for Journald host logs

Using `Dockerfile-otelcol-contrib-journalctl` build custom image:

```
docker build -f Dockerfile-otelcol-contrib-journalctl -t localhost:5000/otelcol-contrib-journalctl .
docker push localhost:5000/otelcol-contrib-journalctl
```

Test docker journalctl compatibility with Host OS version:
```
ssh dcgaudicluster2
# Check Host OS version
sudo journalctl --version 
# Check Container version
docker run -ti --rm --entrypoint journalctl localhost:5000/otelcol-contrib-journalctl --version
# Try to get some logs from Host OS
docker run -ti --rm --entrypoint journalctl -v /var/log/journal:/var/log/journal -v /run/log/journal:/run/log/journal localhost:5000/otelcol-contrib-journalctl -D /var/log/journal -f

# Check the same file are available
sudo journalctl --header 
sudo journalctl --header | grep 'File path:'
docker run -ti --rm --entrypoint bash -v /var/log/journal:/var/log/journal -v /run/log/journal:/run/log/journal localhost:5000/otelcol-contrib-journalctl
docker run -ti --rm --entrypoint journalctl -v /var/log/journal:/var/log/journal -v /run/log/journal:/run/log/journal localhost:5000/otelcol-contrib-journalctl -D /var/log/journal --header | grep 'File path:'
```

##### 1b) Number of iwatch open descriptors

```
ssh dcgaudicluster2
sudo sysctl -w fs.inotify.max_user_instances=8192
```

References:
- https://github.com/kubeflow/manifests/issues/2087


#### 2) Loki volumes

TODO: This is temporary solution until "production" ready provisioner/CSI-driver is added to Kubernetes cluster.

```
### ssh target dcgaudicluster2 node
sudo mkdir -p /mnt/k8stelemetryvolumes
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-1
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-2
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-3
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-4
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-5
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-6
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-7
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-8
sudo mkdir -p /mnt/k8stelemetryvolumes/vol-9
sudo chmod -R a+rwx /mnt/k8stelemetryvolumes
kubectl apply -f loki-volumes.yaml -n monitoring
```



### Troubleshooting

#### Debugging otelcol

##### a) Inspect final configuration

```
# for installed as "telemetry-logs" release
kubectl get configmap -n monitoring telemetry-logs-otelcol-logs-agent -ojsonpath='{.data.relay}'

# for installed as "telemetry-logs-otelcol" release
kubectl get configmap -n monitoring telemetry-logs-otelcol-otelcol-logs-agent -ojsonpath='{.data.relay}'

```

##### b) Check otelcol metrics using dashboard

Open "OTEL / OpenTelemetry Collector" Dashboard in Grafana

##### c) Inspect pipelines and traces ending with errors with zpages extension (enabled by default):
```
podname=`kubectl get pod -l app.kubernetes.io/name=otelcol-logs -n monitoring -oname | cut -f '2' -d '/'` ; echo $podname
curl -vs "127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname:55679/proxy/debug/pipelinez" -o /dev/null
echo open "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname:55679/proxy/debug/tracez"
echo open "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname:55679/proxy/debug/pipelinez"
```
##### d) Enable and modify "debug exporter"

Check `values.yaml` file for `otelcol-logs.alternateConfig.exporters.debug` section . Change mode "basic" to "verbose" or "detailed".

#### Debugging OpenSearch

```
# Check statefulset 
kubectl get statefulset -n=monitoring -l app.kubernetes.io/component=opensearch-cluster-master

# Check opensearch responds.
curl -ik 127.0.0.1:8001/api/v1/namespaces/monitoring/services/opensearch-cluster-master:http/proxy/
# Query opensearch indices.
curl -ik '127.0.0.1:8001/api/v1/namespaces/monitoring/services/opensearch-cluster-master:http/proxy/_cat/indices?v'
# Query "ss4o_logs" logs.
curl -vik '127.0.0.1:8001/api/v1/namespaces/monitoring/services/opensearch-cluster-master:http/proxy/ss4o_logs-default-namespace/_search?pretty' -XGET -H 'Content-type: application/json' -d '{ "query": { "match_all": { } } }'
```
