## Enterprise RAG Telemetry "Traces instrumentation" Helm subchart for "Traces"

### Introduction

Traces instrumentation chart allows to deploy "OpenTelemetry collector" and instrumentation objects for `chatqa` and `edp` for enabling auto zero-code instrumentation.

### Enabling instrumentation

| **WARNING**   | 
| ------------- |
|  Enabling tracing from all services is experimental **preview feature**, please check overhead of tracing under high load in testing controlled environment before enabling full tracing in production. |
|  Tracing instrumentation is not working with Istio enabled. Please, disable this feature before using patches.|


Collecting traces and spans (and optionally pushing logs/metrics, through OpenTelemetry collector) has high overheard so it is disabled by default for all services (excluding router-service).

Please follow this procedure to enable logs/traces from all Enterprise RAG services and downstream services (e.g. model servers).

#### 1) Enabling traces from "router-service"

Enable "correlated" logs (structured logs with trace_id/sample_id, so they can be easily found for specific trace_id/span_id) for log entries generated by `otlpr` logger in router-service:
```
kubectl patch -n chatqa deploy router-service-deployment --patch-file patches/patch-deploy-inject-chatqa-router.yaml
```

> [!WARNING]
> With above "structured logs" pushed by traces OpenTelemetry collector, there will not be logs in stdout/Loki collected by "logs" pipeline.

"Structured logs" from router-service are controlled by `OTEL_LOGS_GRPC_ENDPOINT` (empty or unset disables logs)

Check [above patch](patches/patch-deploy-inject-router.yaml) for description for logging flag.

#### 2) Auto instrumentation for Enterprise RAG micro services

To enable auto instrumentation of python based RAG micro services, they need to be annotated as described [here](https://opentelemetry.io/docs/kubernetes/operator/automatic/#python).
and [here](https://github.com/open-telemetry/opentelemetry-operator#opentelemetry-auto-instrumentation-injection).

Please apply following patches to (examples):
```

# chatqa
kubectl patch -n chatqa deploy embedding-svc-deployment --patch-file patches/patch-deploy-inject-us-chatqa-embedding.yaml
kubectl patch -n chatqa deploy reranking-svc-deployment --patch-file patches/patch-deploy-inject-us-chatqa-reranking.yaml
kubectl patch -n chatqa deploy retriever-svc-deployment --patch-file patches/patch-deploy-inject-us-chatqa-retriever.yaml

# edp
kubectl patch -n edp deploy edp-dataprep --patch-file patches/patch-deploy-inject-us-edp-dataprep.yaml
kubectl patch -n edp deploy edp-embedding --patch-file patches/patch-deploy-inject-us-edp-embedding.yaml
kubectl patch -n edp deploy edp-ingestion --patch-file patches/patch-deploy-inject-us-edp-ingestion.yaml
```

Please check options inside because "token per span" overhead issue to be configured properly (inside [patch file](patches/patch-deploy-inject-us-chatqa-llm.yaml)):
```
kubectl patch -n chatqa deploy llm-svc-deployment --patch-file patches/patch-deploy-inject-us-chatqa-llm.yaml
```

Instrumentation in Python services enables:
- tracing (auto zero-code instrumentation)
- logs - requires that all loggers propagate log entries to root logger (set `LOGGING_PROPAGATE` to true) e.g. logs have trace_id/span_id identifiers to be easily found by tracing explorer.

#### 3) Enabling traces from downstream services (e.g. model servers)

Here are examples of how to modify TGI/TEI/torchserver services to enable traces:

```
# auto zero-code instrumentation
kubectl patch -n chatqa deploy torchserve-embedding-svc-deployment --patch-file patches/patch-deploy-inject-chatqa-torchserve.yaml
# enabling options specific for TGI/TEI
kubectl patch -n chatqa deploy tei-reranking-svc-deployment --patch-file patches/patch-deploy-inject-chatqa-teirerank.yaml
kubectl patch -n chatqa deploy tgi-service-m-deployment --patch-file patches/patch-deploy-inject-chatqa-tgi.yaml
```

Please follow upstream instructions for more description, for those components:

- https://huggingface.co/docs/text-generation-inference/main/en/reference/launcher#otlpendpoint
- https://github.com/huggingface/text-embeddings-inference?tab=readme-ov-file#docker (search for OTLP_ENDPOINT) 
