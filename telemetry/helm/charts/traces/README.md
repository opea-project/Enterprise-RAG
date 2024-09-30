## Enterprise RAG Telemetry "Traces" Helm subchart

### Introduction

Traces chart allows to deploy "traces" pipeline in following configurations:

1) Default Traces pipeline:

```
Pods            -> otelcol-traces-deployment      -> Tempo          -> Prometeheus
```

2) Optional Traces pipeline with Jaeger enabled:

```
Pods            -> otelcol-traces-deployment      -> Tempo          -> Prometheus
                                                  -> Jaeger
```

Information:

- `otelcol-traces-deployment` is managed by "OpenTelemetry Operator for Kubernetes" with Custom Resource `OpenTelemetryCollector` "otelcol-traces"
- `pods` are both manually (router-service/TGI/TEI) or automatically instrumented (python micro services) with Custom Resource `Instrumentation` "rag-python-instrumentation"
- Tempo `metrics-generator` generate metrics based on spans and push them to Prometheus (remote write) to generate Service Graphs.

#### Optional components.

##### 1) Jaeger tracing backend

```
helm upgrade --install telemetry-tracing -n monitoring-tracing --set jaeger.enabled=true .
```

### Enabling instrumentation

Collecting traces and spans (and optionally pushing logs/metrics, through OpenTelemetry collector) has high overheard so it is disabled by default with exception to router-service.
Please follow this procedure to enable traces from Enterprise RAG services and downstream services (e.g. model server)

#### 1) Enabling traces from "router-service"

Enable traces and logs:
```
kubectl patch -n chatqa deploy router-server --patch-file patches/patch-deploy-inject-router.yaml
```

"router-service" can be configured to send:

1) traces - controlled by `OTEL_TRACES_DISABLED`,  `OTEL_EXPORTER_OTLP_ENDPOINT`
2) logs (structured with context of span) - controlled by `OTEL_LOGS_GRPC_ENDPOINT` (empty or unset disables logs)

Check [above patch](patches/patch-deploy-inject-router.yaml) for description of flags.


#### 2) Auto instrumentation for Enterprise RAG micro services

To enable auto instrumentation of python based RAG micro services, they need to be annotated as described [here](https://opentelemetry.io/docs/kubernetes/operator/automatic/#python).
and [here](https://github.com/open-telemetry/opentelemetry-operator#opentelemetry-auto-instrumentation-injection).

Please apply following patches to:
```
kubectl patch -n chatqa deploy embedding-svc-deployment --patch-file patches/patch-deploy-inject-us-embedding.yaml
kubectl patch -n chatqa deploy llm-svc-deployment --patch-file patches/patch-deploy-inject-us-llm.yaml
kubectl patch -n chatqa deploy reranking-svc-deployment --patch-file patches/patch-deploy-inject-us-reranking.yaml
kubectl patch -n chatqa deploy retriever-svc-deployment --patch-file patches/patch-deploy-inject-us-retriever.yaml
```

Instrumentation in Python services enables:
- tracing 
- logs - requires that all loggers propagate log entries to root logger (set `LOGGING_PROPAGTE` to be set to true)

#### 3) Enabling traces from downstream services (e.g. model servers)

Here are examples how to modify TGI/TEI services to enable traces:

```
kubectl patch -n chatqa deploy tgi-service-m-deployment --patch-file patches/patch-deploy-inject-tgi.yaml
kubectl patch -n chatqa deploy tei-embedding-svc-deployment --patch-file patches/patch-deploy-inject-tei.yaml
```

Please follow upstream instructions for more description, for those components:

- https://huggingface.co/docs/text-generation-inference/main/en/reference/launcher#otlpendpoint
- https://github.com/huggingface/text-embeddings-inference?tab=readme-ov-file#docker (search for OTLP_ENDPOINT) 


