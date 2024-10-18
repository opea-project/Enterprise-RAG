### Telemetry for Enterprise RAG

#### Intro

Telemetry stack for Enterprise RAG is split into three related parts (main chart and two subcharts):

- [**metrics**](helm/README.md) - (base) provides metrics signals based on Prometheus and set of exporters and basic infrastructure for visualization (Grafana) and alerting (AlertManager + Rules)
- [**logs**](helm/charts/logs/README.md) - provides mechanism to collect logs (custom OpenTelemetry collector running as DaemonSet) from all pods and HOST system OS systemd units and backends to store and query (Loki and optionally OpenSearch)
- [**traces**](helm/charts/traces/README.md) - exposes central service where traces can be pushed (OpenTelemetry collector running as Deployment deployed by OpenTelemetry operator) and backends to store and query (Tempo and optionally Jeager)

This three charts needs to be installed separately but **metrics** and **logs** will share the same namespace.

Please follow instructions in [helm/README.md](helm/README.md) to install **metrics** part and [subcharts READMEs ](helm/charts/) for **logs** and **traces**.

#### Namespaces

- **metrics** and **logs** charts are deployed to **monitoring** namespace
- **traces** chart is deployed to **monitoring-traces** namespace

#### Architecture (overview)

This is the "default" telemetry pipeline when all "default" components are deployed (when following instructions "deployment" directory):

```
       ------>  otelcol-traces-deployment  ----------->  Tempo  --\  ------------------
      /                                                            \                   \
Pods --------------------------->  exporters ------------------------>  Prometheus ----->  Grafana
          \                                                                            /
journald ---->  otelcol-logs-daemonset(journalctl) ------------  Loki -----------------
```

where:

- **`otelcol-*`** are OpenTelemetry collectors, deployed as Deployment or DaemonSet running in "push by pods" or "pull from pods/journald"  mode for **traces** and **logs**,
- **`exporters`** are set of exporters as sources to scrape metrics by Prometheus (every pod can be treated as exporter using `ServiceMonitor` or `PodPmonitor` custom resources),
- **`Promethues`**, **`Loki`** and **`Tempo`** are telemetry backends respectively for: metrics, logs and traces,
- **`Grafana`** is a frontend to query date from telemetry backends with configured data sources and provisioned dashboards.
