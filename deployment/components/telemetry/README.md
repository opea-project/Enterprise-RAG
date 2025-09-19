# Telemetry for Intel® AI for Enterprise RAG

# Overview

The telemetry stack for Intel® AI for Enterprise RAG is built from those related Helm charts, including the main metrics chart and three subcharts:

- [**metrics**](helm/README.md) - (base) Helm chart that sets up metrics collection with Prometheus and exporters, and provisions the core infrastructure for visualization (Grafana) and alerting (AlertManager with rules)

- [**logs**](helm/charts/logs/README.md) - Helm chart that sets up log collection using a custom OpenTelemetry collector (running as a DaemonSet) to gather data from all pods and host-level systemd units, and stores it in [Loki](https://github.com/grafana/loki) for querying.

- [**traces**](helm/charts/traces/README.md) - Helm chart that deploys the trace backend [Tempo](https://github.com/grafana/tempo) for storing and querying traces, and installs the OpenTelemetry operator to automate collectors deployment

- [**traces-instr**](helm/charts/traces-instr/README.md) - Helm chart that provisions a central service where traces can be pushed (OpenTelemetry collector running as a deployment deployed by OpenTelemetry operator) and enables zero-code auto-instrumentation


> [!NOTE]
> These four charts need to be installed in order due to implicit dependencies: Loki and Tempo rely on Grafana and Prometheus, while the Traces collector depends on the OpenTelemetry Operator for deployment. Please follow instructions in [helm/README.md](helm/README.md) to install all four charts.


## Architecture

The default telemetry pipeline integrates metrics, logs, and traces across the platform, leveraging industry-standard open-source components for collection, storage, and visualization.


```
       ------>  otelcol-traces-deployment  ----------->  Tempo  --\  ------------------
      /                                                            \                   \
Pods --------------------------->  exporters ------------------------>  Prometheus ----->  Grafana
          \                                                                            /
journald ---->  otelcol-logs-daemonset(journalctl) ------------  Loki -----------------
```

### Component Roles

- **Grafana:** Unified dashboard for querying and visualizing metrics, logs, and traces from all telemetry backends.
- **Prometheus:** Metrics backend, scraping data from exporters and providing alerting and monitoring capabilities.
- **Loki:** Log backend, storing and indexing logs collected from pods and host systemd units.
- **Tempo:** Trace backend, storing distributed traces for performance and debugging analysis.
- **Exporters:** Expose metrics from application pods, discovered via `ServiceMonitor` or `PodMonitor` resources.
- **OpenTelemetry Collectors (`otelcol-*`):** Collect and forward telemetry data. Deployed as DaemonSets for logs (journald) and as Deployments for traces, supporting both push and pull modes.

This architecture ensures scalable, reliable telemetry collection and observability across all deployed workloads.

### Namespaces

The telemetry stack is organized into separate namespaces to isolate different types of signals and simplify management:

- **metrics** and **logs** charts are deployed to the **monitoring** namespace
- **traces** and **traces-instr** are deployed to the **monitoring-traces** namespace