# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

---
apiVersion: apps/v1
kind: Deployment
metadata:
{{- `
  name: {{.DplymntName}}
  namespace: {{.Namespace}}
` }}
  labels:
    {{- include "manifest.labels" (list "gmc-router" .) | nindent 4 }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: router-service
      app.kubernetes.io/name: router-service
      app.kubernetes.io/version: "v0.8"
  template:
    metadata:
      labels:
        app: router-service
        app.kubernetes.io/name: router-service
        app.kubernetes.io/version: "v0.8"
        {{- include "manifest.tdx.labels" (list "gmc-router" .) | nindent 8 }}
      {{- include "manifest.tdx.annotations" (list "gmc-router" .) | nindent 6 }}
    spec:
      {{- include "manifest.tdx.runtimeClassName" (list "gmc-router" .) | nindent 6 }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      serviceAccountName: default
      {{- include "gmc.imagePullSecrets" . }}
      containers:
      - name: router-server
        {{- $image := "gmcRouter" }}
        image: {{ include "manifest.image" (list $image .Values) }}
        imagePullPolicy: {{ toYaml (index .Values "images" $image "pullPolicy" | default "Always") }}
        securityContext:
            {{- toYaml .Values.securityContext | nindent 10 }}
        ports:
        - containerPort: 8080
        env:
        {{- `
        - name: no_proxy
          value: {{.NoProxy}}
        - name: http_proxy
          value: {{.HttpProxy}}
        - name: https_proxy
          value: {{.HttpsProxy}}
        ### OTEL/Tracing
        # target
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otelcol-traces-collector.monitoring-traces:4318"
        # exclusion
        - name: OTEL_GO_EXCLUDED_URLS
          value: "/metrics"
        # identification
        - name: OTEL_SERVICE_NAME
          value: "{{.Namespace}}/{{.DplymntName}}"
        # identification (namespace is used to distinguish different span names for different router-instances) used by router not OTEL
        - name: OTEL_NAMESPACE
          value: "{{.Namespace}}"
        ### TODO: Enabling this breaks traces->logs correlation when query in Grafana
        # - name: OTEL_RESOURCE_ATTRIBUTES
        #   value: "namespace={{.Namespace}}"
        # ratio: 0 never and 1 always with 0.5 half of queries will be traced
        - name: OTEL_TRACES_SAMPLER_FRACTION
          value: "1.0"
        ### OTEL/Logs: Warning: Enabling logs through collector disables logs to stdout
        # - name: OTEL_LOGS_GRPC_ENDPOINT
        #   value: "otelcol-traces-collector.monitoring-traces:4317"
        ` -}}
        args:
        {{- `
        - "--graph-json"
        - {{.GRAPH_JSON}}
        ` -}}
        resources:
          {{- $defaultValues := "{requests: {cpu: '1', memory: '1Gi'}, limits: {cpu: '1', memory: '1Gi'}}" -}}
          {{- include "manifest.getResource" (list "gmc-router" $defaultValues .Values) | nindent 12 }}
---
apiVersion: v1
kind: Service
metadata:
{{- `
  name: {{.SvcName}}
  namespace: {{.Namespace}}
` -}}
spec:
  type: ClusterIP
  selector:
    app: router-service
    app.kubernetes.io/name: router-service
    app.kubernetes.io/version: "v0.8"
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
