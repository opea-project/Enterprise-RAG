## Enterprise RAG Telemetry Logs Helm subchart

### Introduction

Logs chart allows to deploy "logs" pipeline in following configurations:

1) Default Logs pipeline (not custom image needed, but not logs from systemd units):


```
pods            -> otelcol-logs-daemonset/default      -> loki
```

2) (recommended) Logs pipeline with custom otelcol with journald support:

```
pods
journald        -> otelcol-logs-daemonset/journalctl   -> loki
```

3) Logs Pipeline with additional OpenSearch logs backend:

```
pods
journald        -> otelcol-logs-daemonset              -> loki
                                                          opensearch
```

4) Logs pipeline without otelcol but collects both pods logs and systemd units logs:

```
pods
journald        -> promtail                             -> loki
```

5) All above combined

```
pods
journald        -> promtail                             -> loki

pods
journald        -> otelcol-logs-daemonset/journalctl    -> loki
                                                           opensearch
```

### Getting started

#### Install metrics and logs telemetry

Please follow instruciton from "base telemetry" [README Installation instruciton section](../../README.md).

#### Optional components.

##### a) OpenSearch logs backend

Installed as upgrade to **"telemetry-logs"** release `[loki, otelcol/journalctl, opensearch]`:

| **WARNING**   | 
| ------------- |
|  OpenSearch backend is opt-in **exprimental** preview feature. Please consider testing in controlled environment, before enabling on production systems. |

```
helm upgrade --install telemetry-logs -n monitoring -f values-journalctl.yaml -f values-opensearch.yaml .
```

##### b) Promtail logs collector

| **WARNING**   | 
| ------------- |
|  Promtail is opt-in **exprimental** preview feature. Please consider testing in controlled environment, before enabling on production systems. |


If you don't want to use custom image and one wants to have to access to systemd/journalctl logs, then you need log collector that can collect journald systemd unit logs.
Promtail replaces otelcol and collects pods logs as well as systemd units logs.

Both Promtail and otelcol can be deployed together (both generate different set of indexes/labels) in Loki.
Logs from Promtail are directly transferred in Loki (otelcol is not used!).

Consider deploying as a separate Helm chart release named “telemetry-logs-promtail”:

```
helm install telemetry-logs-promtail -n monitoring -f values-promtail.yaml .
```

### Prerequisites (images/volumes)

#### 1) OpenTelemetry collector requirements

##### 1a) Build custom image for Journald host logs

Using `Dockerfile-otelcol-contrib-journalctl` build custom image:

```
docker build -f Dockerfile-otelcol-contrib-journalctl -t localhost:5000/otelcol-contrib-journalctl .
docker push localhost:5000/otelcol-contrib-journalctl:latest
```

Test docker journalctl compatibility with Host OS version:
```
ssh TARGET_NODE
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

Check numbers of inotify user instances (on target Host):
```
sudo sysctl -w fs.inotify.max_user_instances=8192
```

To make this change **permanent** modify `/etc/sysctl.conf` or `/syc/sysctl.d/` accordingly.

References:
- https://github.com/kubeflow/manifests/issues/2087

### Troubleshooting

#### OpenTelemetry collector

##### a) **telemetry-logs-otelcol-logs-agent** (with journalctl support) pod fails with error in logs:

```
Error: cannot start pipelines: start stanza: journalctl command exited                                                                                                                                                                                       │
│ 2024/09/16 11:15:20 collector server run finished with error: cannot start pipelines: start stanza: journalctl command exited  
```

Check configuration of Host OS:
```
cat /proc/sys/fs/inotify/max_user_instances
```

If number is low (<8000 e.g. on Ubuntu default number is 128), please check how to set correct OS settings in prerequisites [here](#1b-number-of-iwatch-open-descriptors)

Description:

It is caused by journalctl automatically turning off "follow mode" when run by opentelemetry agent with following error
"Insufficient watch descriptors available. Reverting to -n." (this error is not exposed by otelcol agent, to confirm disable journalctl receiver and attach pod and run `journalctl -f` command).

##### b) Inspect final configuration

```
# for installed as "telemetry-logs" release
kubectl get configmap -n monitoring telemetry-logs-otelcol-logs-agent -ojsonpath='{.data.relay}'

# for installed as "telemetry-logs-otelcol" release
kubectl get configmap -n monitoring telemetry-logs-otelcol-otelcol-logs-agent -ojsonpath='{.data.relay}'

```

##### c) Check otelcol metrics using dashboard

Open "OTEL / OpenTelemetry Collector" Dashboard in Grafana

##### d) Inspect pipelines and traces ending with errors with zpages extension (enabled by default):
```
podname=`kubectl get pod -l app.kubernetes.io/name=otelcol-logs -n monitoring -oname | cut -f '2' -d '/'` ; echo $podname
curl -vs "127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname:55679/proxy/debug/pipelinez" -o /dev/null
echo open "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname:55679/proxy/debug/tracez"
echo open "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname:55679/proxy/debug/pipelinez"
```
##### e) Enable and modify "debug exporter"

Check `values.yaml` file for `otelcol-logs.alternateConfig.exporters.debug` section . Change mode "basic" to "verbose" or "detailed".

##### f) Change level verbosity from "info" to "debug"

Check `values-journalctl-devel.yaml` file for `otelcol-logs.alternateConfig.service.telemetry.logs.level`.  Change from "info" to "debug".

More details [here](https://opentelemetry.io/docs/collector/internal-telemetry/#configure-internal-logs).

Or with '--set' argument trick: modify otelcol agent daemonset "telemetry-logs-otelcol-logs-agent" spec:
```

spec:
  template:
    spec:
      containers:
      - args:
        - --config=/conf/relay.yaml
        - --set=service::telemetry::logs::level=debug
```

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
