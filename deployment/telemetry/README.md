### Telemetry for Enterprise RAG

#### Intro

Telemetry stack for Enterprise RAG is split into three related parts (main chart and three subcharts):

- [**metrics**](helm/README.md) - (base) provides metrics signals based on Prometheus and set of exporters and basic infrastructure for visualization (Grafana) and alerting (AlertManager + Rules)
- [**logs**](helm/charts/logs/README.md) - provides mechanism to collect logs (custom OpenTelemetry collector running as DaemonSet) from all pods and HOST system OS systemd units and backends to store and query (Loki and optionally OpenSearch)
- [**traces**](helm/charts/traces/README.md) - deploys backends to store and query traces (Tempo and optionally Jaeger) and OpenTelemetry operator to automate collectors deployment,
- [**traces-instr**](helm/charts/traces-instr/README.md) - exposes central service where traces can be pushed (OpenTelemetry collector running as Deployment deployed by OpenTelemetry operator) and prepare auto zero-code instrumentations

This four charts needs to be installed in order because implicit dependencies (Loki and Tempo uses Grafana as visualization and Prometheus for self monitoring, Traces collector uses OpenTelemetry operator for deployment)

Please follow instructions in [helm/README.md](helm/README.md) to install all four charts.

#### Namespaces

- **metrics** and **logs** charts are deployed to **monitoring** namespace
- **traces** and **traces-instr** are deployed to **monitoring-traces** namespace

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
