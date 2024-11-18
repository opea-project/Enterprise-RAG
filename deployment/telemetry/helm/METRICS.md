## Available metrics and sources:

a) **GMConnector/router**:

- `http_server_duration_milliseconds_*` histogram,
- `http_server_request_size_bytes_total`, `http_server_response_size_bytes_total`,
- `http_client_duration_milliseconds_*` histogram,
- `http_client_request_size_bytes_total`, `http_client_response_size_bytes_total`,
- `llm_all_token_latency_milliseconds_bucket`, `llm_first_token_latency_milliseconds_bucket`, `llm_pipeline_latency_milliseconds_bucket`, `llm_next_token_latency_milliseconds_bucket`,

Example:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/router-service:8080/proxy/metrics
```

b) **opea-microservices** (instrumentation using https://github.com/trallnag/prometheus-fastapi-instrumentator):

- `http_requests_total` counter, labels: **status** and **method**
- `http_request_size_bytes` summary (count/sum), labels: **handler**,
- `http_response_size_bytes` summary (count/sum), labels: **handler**,
- `http_request_duration_seconds_` histogram with labels: **handler**, **method** (extra: service, pod, container, endpoint, service)
- `http_request_duration_highr_seconds_` histogram (no labels),
- `process_resident_memory_bytes`, `process_cpu_seconds_total`, ...

Example:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/llm-svc:llm-uservice/proxy/metrics
```

c) **HABANA metrics exporter**

  - `habanalabs_clock_soc_max_mhz`,
  - `habanalabs_clock_soc_mhz`,
  - `habanalabs_device_config`,
  - `habanalabs_ecc_feature_mode`,
  - `habanalabs_energy`,
  - `habanalabs_kube_info`,
  - `habanalabs_memory_free_bytes`,
  - `habanalabs_memory_total_bytes`,
  - `habanalabs_memory_used_bytes`,
  - `habanalabs_nic_port_status`,
  - `habanalabs_pci_link_speed`,
  - `habanalabs_pci_link_width`,
  - `habanalabs_pcie_receive_throughput`,
  - `habanalabs_pcie_replay_count`,
  - `habanalabs_pcie_rx`,
  - `habanalabs_pcie_transmit_throughput`,
  - `habanalabs_pcie_tx`,
  - `habanalabs_pending_rows_state`,
  - `habanalabs_pending_rows_with_double_bit_ecc_errors`,
  - `habanalabs_pending_rows_with_single_bit_ecc_errors`,
  - `habanalabs_power_default_limit_mW`,
  - `habanalabs_power_mW`,
  - `habanalabs_temperature_onboard`,
  - `habanalabs_temperature_onchip`,
  - `habanalabs_temperature_threshold_gpu`,
  - `habanalabs_temperature_threshold_memory`,
  - `habanalabs_temperature_threshold_shutdown`,
  - `habanalabs_temperature_threshold_slowdown`,
  - `habanalabs_utilization`

Example output:
```
podname=`kubectl get pods -n monitoring -l app.kubernetes.io/name=habana-metric-exporter-ds -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics"
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics" | grep HELP | grep habanalabs
```
   
d) **TGI** metrics (Broken):

Example output:
```
curl -v -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tgi-service-m:tgi/proxy/metrics
```

Check the issue: https://github.com/huggingface/text-generation-inference/issues/2184

e) **TEI**  metrics:

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tei-embedding-svc:tei/proxy/metrics
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/tei-reranking-svc:teirerank/proxy/metrics
```

f) **torchserver-embedding**  metrics

https://pytorch.org/serve/metrics_api.html 

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/chatqa/services/torchserve-embedding-svc:torchserve/proxy/metrics
```

g) **redis-exporter**

Example output:
```
curl -sL http://127.0.0.1:8001/api/v1/namespaces/monitoring/services/telemetry-prometheus-redis-exporter:redis-exporter/proxy/metrics
```
- `redis_latency_percentiles_usec` 
- `redis_up`

h) **node-exporter** metrics:

Example output:
```
podname=`kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus-node-exporter -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics"
curl -sL "http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics" | grep HELP | grep node_
```

- `node_cpu_seconds_total`  ...


i) **pcm** metrics (seperately installed) - check instructions below
```
podname=`kubectl -n monitoring get pod -l app.kubernetes.io/component=pcm-sensor-server -ojsonpath='{.items[0].metadata.name}'`
echo $podname
curl -Ls http://127.0.0.1:8001/api/v1/namespaces/monitoring/pods/$podname/proxy/metrics 
```
- `DRAM_Writes`, `Instructions_Retired_Any` ...


