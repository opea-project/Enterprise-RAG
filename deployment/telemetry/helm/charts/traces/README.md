## Enterprise RAG Telemetry "Traces" Helm subchart

### Introduction

Traces chart allows to deploy "traces" pipeline in following configurations:

1) Default Traces pipeline:

```
Pods            -> otelcol-traces-deployment*     -> Tempo          -> Prometeheus
```

2) Optional Traces pipeline with Jaeger enabled:

```
Pods            -> otelcol-traces-deployment*     -> Tempo          -> Prometheus
                                                  -> Jaeger
```

Information:

- `otelcol-traces-deployment` is managed by "OpenTelemetry Operator for Kubernetes" with Custom Resource `OpenTelemetryCollector` "otelcol-traces" (deployed with another chart "traces-instr")
- `pods` are both manually (router-service/TGI/TEI) or automatically instrumented (python micro services) with Custom Resource `Instrumentation` "rag-python-instrumentation"
- Tempo `metrics-generator` generate metrics based on spans and push them to Prometheus (remote write) to generate Service Graphs.

*otelcol-traces-deployment is deployed by another subchart "traces-instr" because of the issue with webhook and CRD dependency

#### Optional components.

##### 1) Jaeger tracing backend

| **WARNING**   | 
| ------------- |
|  Jaeger is opt-in **exprimental** preview feature. Please consider testing in controlled environment, before enabling on production systems. |

To deploy Jaeger backend (from `telemetry/helm` directory):
```
helm upgrade telemetry-traces -n monitoring-traces --set jaeger.enabled=true charts/traces
```

To enable Jaeger as OpenTelemetry traces target:
```
helm upgrade telemetry-traces-instr -n monitoring-traces --set jaeger.enabled=true charts/traces-instr
```

Enable port-forward to access jeager UI at http://127.0.0.1:16686:
```
kubectl port-forward -n monitoring-traces svc/telemetry-traces-jaeger-query 16686:query
```
