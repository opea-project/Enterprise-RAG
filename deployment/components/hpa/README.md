# Horizontal Pod Autoscaler

This document describes how to scale Enterprise RAG using the Horizontal Pod Autoscaler (HPA). To find out how HPA works: [Kubernetes autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

Scaling components allow increasing the bandwidth of critical components to eliminate bottlenecks that might occur while using the RAG pipeline. Autoscaling of the solution is based on metrics gathered by Prometheus in telemetry; therefore, installing telemetry is a prerequisite to implementing scaling the solution.

## How it works

Prometheus collects metrics from running containers via ServiceMonitors. Next, `prometheus-adapter` based on metrics from Prometheus is collecting custom metrics. Prometheus adapter creates an API service, and custom metrics should be accessible via the following command: 
```bash
`kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1 | jq .`.
```
Once the custom metrics are accessible via the API service, we can define HPA objects for specific deployments. HPA objects consist of several sections:

- `metrics` section defines the name of the custom metric and the target value (threshold above which we scale up/down the deployment):

  ```yaml
  metrics:
  - type: Object
    object:
      metric:
        name: vllm_token_latency
      describedObject:
        apiVersion: v1
        # get metric for named object of given type (in the same namespace)
        kind: Service
        name: vllm-service-m
      target:
        type: Value
        value: 100m      # this value is a threshold, if measured value is above the target and scale policies are meet scaling replicas will proceed.
  ```
- `behavior` section defines how to scale the deployments:
 
  ```yaml
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 180  # wait 180 secs before taking any action
      policies:
      - type: Percent
        value: 25
        periodSeconds: 90   # remove replica every 90 secs
    scaleUp:
      selectPolicy: Max
      stabilizationWindowSeconds: 0 
      policies:
      - type: Pods
        value: 1
        periodSeconds: 90
  ```

As there might be performance differences between different hardware setups, please fill in the [CPU resources](../../pipelines/chatqa/resources-reference-cpu.yaml) or [Gaudi resources](../../pipelines/chatqa/resources-reference-hpu.yaml) HPA section values prior to deploying the solution.
Every component that is able to scale up has HPA section that was set assuming hardware platform is Xeon Gen4 platform and default `LLM` `embedding` `reranking` models are set. Therefore, please consider modifying target values per component if needed. Sections in resources files would give information about which metrics expression represents the target value.
