# Enterprise RAG Telemetry - Metrics

An overview of available metrics and their sources, organized by application components. 

## Available Metrics and Sources:

a) **GMConnector/router**:

> Note:
> These metrics are visualized in Grafana on the dashboard:
`EnterpriseRAG → Services → GMConnector (router)`.


- `http_client_duration_milliseconds_*` - histogram of outbound HTTP request duration.
- `http_client_request_size_bytes_total` - total size of HTTP request messages.
- `router_e2e_latency_milliseconds_*` - histogram of the total end-to-end latency, measuring the time taken to process the entire request through all steps.
- `router_e2e_ttft_latency_milliseconds_*` - histogram of time-to-first-token (TTFT) for the entire request. Measures the time from request start until the first token is generated.
- `router_pipeline_step_milliseconds_*` - histogram of latency for a specific pipeline step, identified by `stepName`.
- `router_pipeline_latency_milliseconds_*` - histogram of the time spent executing all pipeline steps before the LLM stage, including the time to retrieve and rerank documents that are then fed into the LLM.
- `router_llm_first_token_latency_milliseconds_*` - histogram of the time required by the LLM server to generate the first token, showing how quickly the model starts responding.
- `router_llm_next_token_latency_milliseconds_*` - histogram of the latency for generating by the LLM Server each subsequent token after the first token.
- `router_llm_all_tokens_latency_milliseconds_*` - histogram of the total time the LLM server takes to generate the full set of tokens, representing the duration of the LLM stage for producing the complete response.

Example:

```
# To forward the router service to your local machine
kubectl port-forward --namespace chatqa svc/router-service 8080:8080

# To fetch the raw Prometheus-formatted metrics for inspection or debugging
curl -sL http://localhost:8080/metrics
```

b) **opea-microservices** (instrumentation using https://github.com/trallnag/prometheus-fastapi-instrumentator):

> Note:
> These metrics are visualized in Grafana on the dashboard:
`EnterpriseRAG / Services / Details`.

- `http_requests_total` counter, labels: **status** and **method**
- `http_request_size_bytes` summary (count/sum), labels: **handler**,
- `http_response_size_bytes` summary (count/sum), labels: **handler**,
- `http_request_duration_seconds_` histogram with labels: **handler**, **method** (extra: service, pod, container, endpoint, service)
- `http_request_duration_highr_seconds_` histogram (no labels),
- `process_resident_memory_bytes`, `process_cpu_seconds_total`, ...

Example:
```
# Forward the selected microservice to your local machine.
# In this example, we are forwarding the `llm-svc` service.

kubectl port-forward --namespace chatqa svc/llm-svc 9000:9000

# Fetch the raw Prometheus-formatted metrics for inspection or debugging
curl -sL http://localhost:9000/metrics
```

c) **HABANA metrics exporter**

  - `habanalabs_clock_soc_max_mhz`
  - `habanalabs_clock_soc_mhz`
  - `habanalabs_device_config`
  - `habanalabs_ecc_feature_mode`
  - `habanalabs_energy`
  - `habanalabs_kube_info`
  - `habanalabs_memory_free_bytes`
  - `habanalabs_memory_total_bytes`
  - `habanalabs_memory_used_bytes`
  - `habanalabs_nic_port_status`
  - `habanalabs_pci_link_speed`
  - `habanalabs_pci_link_width`
  - `habanalabs_pcie_receive_throughput`
  - `habanalabs_pcie_replay_count`
  - `habanalabs_pcie_rx`
  - `habanalabs_pcie_transmit_throughput`
  - `habanalabs_pcie_tx`
  - `habanalabs_pending_rows_state`
  - `habanalabs_pending_rows_with_double_bit_ecc_errors`
  - `habanalabs_pending_rows_with_single_bit_ecc_errors`
  - `habanalabs_power_default_limit_mW`
  - `habanalabs_power_mW`
  - `habanalabs_temperature_onboard`
  - `habanalabs_temperature_onchip`
  - `habanalabs_temperature_threshold_gpu`
  - `habanalabs_temperature_threshold_memory`
  - `habanalabs_temperature_threshold_shutdown`
  - `habanalabs_temperature_threshold_slowdown`
  - `habanalabs_utilization`

Example output:
```
podname=`kubectl get pods -n monitoring -l app.kubernetes.io/name=habana-metric-exporter-ds -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics"
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics" | grep HELP | grep habanalabs
```
   

d) **TEI**  metrics:

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tei-embedding-svc:tei/proxy/metrics
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tei-reranking-svc:teirerank/proxy/metrics
```

e) **torchserver-embedding**  metrics

For reference, see the official TorchServe metrics API at https://pytorch.org/serve/metrics_api.html.  


Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/torchserve-embedding-svc:torchserve/proxy/metrics
```

f) **redis-exporter** metrics

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-prometheus-redis-exporter:redis-exporter/proxy/metrics
```
- `redis_latency_percentiles_usec` 
- `redis_up`

g) **node-exporter** metrics:

Example output:
```
podname=`kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus-node-exporter -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics"
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics" | grep HELP | grep node_
```

- `node_cpu_seconds_total`  ...


h) **pcm** metrics
> [!WARNING]
> It is **not enabled by default** and requires a separate installation of PCM.
```
podname=`kubectl -n monitoring get pod -l app.kubernetes.io/component=pcm-sensor-server -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics 
```
- `DRAM_Writes`, `Instructions_Retired_Any` ...


