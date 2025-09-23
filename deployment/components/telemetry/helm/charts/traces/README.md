# Enterprise RAG Telemetry - "Traces" Helm subchart

## Introduction

Traces chart allows to deploy "traces" pipeline in following configurations:


```
Pods            -> otelcol-traces-deployment*     -> Tempo          -> Prometheus
```

Where:

- `otelcol-traces-deployment` is managed by "OpenTelemetry Operator for Kubernetes" with Custom Resource `OpenTelemetryCollector` "otelcol-traces" (deployed with another chart "traces-instr")
- `pods` (python microservices) are instrumented automatically using the Instrumentation Custom Resource "rag-python-instrumentation"
- Tempo `metrics-generator` generate metrics based on spans and push them to Prometheus (remote write) to generate Service Graphs.

\*otelcol-traces-deployment is deployed by another subchart "traces-instr" because of the issue with webhook and CRD dependency
