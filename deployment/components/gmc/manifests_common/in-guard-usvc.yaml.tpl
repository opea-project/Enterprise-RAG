---
# Source: in-guard-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: in-guard-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
  HF_HOME: /tmp/in-guard/huggingface
  KMP_AFFINITY: granularity=fine,compact,1,0
---
# Source: in-guard-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: in-guard-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 8050
      targetPort: 8050
      protocol: TCP
      name: in-guard-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: in-guard-usvc
    app.kubernetes.io/instance: in-guard-usvc
  name: in-guard-usvc
---
# Source: in-guard-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: in-guard-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  replicas: {{ include "getReplicas" (list .filename .Values) | default 1 }}
  selector:
    matchLabels:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 6 }}
  template:
    metadata:
      {{- include "manifest.podLabels" (list .filename .) | nindent 6 }}
      {{- include "manifest.tdx.annotations" (list .filename .) | nindent 6 }}
    spec:
      {{- include "manifest.tdx.runtimeClassName" (list .filename .) | nindent 6 }}
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: inference-eligible
                    operator: In
                    values:
                      - "true"
      tolerations:
        - key: "inference_eligible"
          operator: "Equal"
          value: "true"
          effect: "PreferNoSchedule"
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      {{- include "gmc.imagePullSecrets" . }}
      serviceAccountName: in-guard-usvc
      containers:
        - name: in-guard-usvc
          envFrom:
            - configMapRef:
                name: in-guard-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
            - name: MKL_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: in-guard-usvc
              containerPort: 8050
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
            - mountPath: /home/user/nltk_data
              name: nltk-data
            - mountPath: /home/user/.cache # required for Anonimize scanner
              name: user-cache
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: in-guard-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: in-guard-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: in-guard-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '4', memory: '8Gi'}, limits: {cpu: '8', memory: '16Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
        - name: nltk-data
          emptyDir: {}
        - name: user-cache
          emptyDir: {}
---
{{- if .Values.hpaEnabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: in-guard
  labels:
  {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: input-scan-svc-deployment
  minReplicas: {{ ( ((index .Values "services" .filename).hpa).minReplicas | default 1) }}
  maxReplicas: {{ ( ((index .Values "services" .filename).hpa).maxReplicas | default 3) }}
  metrics:
  - type: Object
    object:
      metric:
        name: http_request_duration_seconds_avg_input_scan
      describedObject:
        apiVersion: v1
        kind: Service
        name: input-scan-svc
      target:
        type: AverageValue
        averageValue: {{ ( ((index .Values "services" .filename).hpa).averageValue | default 1) }}
  {{- $hpaBehavior := ( ((index .Values "services" .filename).hpa).behavior) }}
  {{- if $hpaBehavior }}
  behavior:
    {{- toYaml $hpaBehavior | nindent 4 }}
  {{- else }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
      - type: Pods
        value: 1
        periodSeconds: 60
    scaleUp:
      selectPolicy: Max
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 1
        periodSeconds: 60
  {{- end }}
{{- end }}
