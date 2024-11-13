## Enterprise RAG Telemetry "Traces" Helm subchart

### Introduction

Traces chart allows to deploy "traces" pipeline in following configurations:

1) Default Traces pipeline:

```
Pods            -> otelcol-traces-deployment*     -> Tempo          -> Prometeheus
```

Information:

- `otelcol-traces-deployment` is managed by "OpenTelemetry Operator for Kubernetes" with Custom Resource `OpenTelemetryCollector` "otelcol-traces" (deployed with another chart "traces-instr")
- `pods` are both manually (router-service/TGI/TEI) or automatically instrumented (python micro services) with Custom Resource `Instrumentation` "rag-python-instrumentation"
- Tempo `metrics-generator` generate metrics based on spans and push them to Prometheus (remote write) to generate Service Graphs.

*otelcol-traces-deployment is deployed by another subchart "traces-instr" because of the issue with webhook and CRD dependency
