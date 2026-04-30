---
# Source: torchserve/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: torchserve-reranking-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
{{- if and .Values.vllmNodes .Values.balloons.enabled }}
{{- range .Values.vllmNodes }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ $.Values.pvc.modelReranker.name }}-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
spec:
  accessModes:
    - {{ $.Values.pvc.modelReranker.accessMode }}
  resources:
    requests:
      storage: {{ $.Values.pvc.modelReranker.storage }}
{{- end }}
{{- else }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Values.pvc.modelReranker.name }}
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  accessModes:
    - {{ .Values.pvc.modelReranker.accessMode }}
  resources:
    requests:
      storage: {{ .Values.pvc.modelReranker.storage }}
{{- end }}
---
# Source: torchserve/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: torchserve-reranking
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 8090
      targetPort: 8090
      protocol: TCP
      name: torchserve
    - port: 8091
      targetPort: 8091
      protocol: TCP
      name: management
    - port: 8092
      targetPort: 8092
      protocol: TCP
      name: metrics
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
{{- if and .Values.vllmNodes .Values.balloons.enabled }}
{{- range .Values.vllmNodes }}
# Source: torchserve/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve-reranking-svc-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
    reranking-node: {{ .name }}
spec:
  replicas: {{ .VLLM_INSTANCES | default 1 }}
  selector:
    matchLabels:
      {{- include "manifest.selectorLabels" (list $.filename $) | nindent 6 }}
      reranking-node: {{ .name }}
  template:
    metadata:
      labels:
        {{- include "manifest.selectorLabels" (list $.filename $) | nindent 8 }}
        reranking-node: {{ .name }}
    spec:
      nodeSelector:
        {{- toYaml .nodeSelector | nindent 8 }}
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: kubernetes.io/hostname
                    operator: In
                    values:
                      - {{ .name }}
      tolerations:
        - key: "inference_eligible"
          operator: "Equal"
          value: "true"
          effect: "PreferNoSchedule"
      initContainers:
        {{- include "manifest.balloons.initContainer" $ | nindent 8 }}
        - name: cache-warmer
          {{- include "manifest.torchserve.reranking.containerFields" (list $ (list "TORCHSERVE_PRELOAD_MODE=1")) | nindent 10 }}
      securityContext:
        {{- toYaml $.Values.podSecurityContext | nindent 8 }}
      {{- include "gmc.imagePullSecrets" $ }}
      containers:
        - name: torchserve-reranking
          {{- include "manifest.torchserve.reranking.containerFields" (list $ (list)) | nindent 10 }}
          ports:
            - name: http
              containerPort: 8090
              protocol: TCP
            - name: management
              containerPort: 8091
              protocol: TCP
            - name: metrics
              containerPort: 8092
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: ping
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            exec:
              command: {{- include "manifest.torchserve.probeInferenceCmd" . | nindent 14 }}
            initialDelaySeconds: 5
            periodSeconds: 30
            timeoutSeconds: 60
            failureThreshold: 20
          startupProbe:
            exec:
              command: {{- include "manifest.torchserve.probeInferenceCmd" . | nindent 14 }}
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 60
            failureThreshold: 120
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ $.Values.pvc.modelReranker.name }}-{{ .name }}
        - name: model-store
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 1Gi
        - name: tmp
          emptyDir: {}
        - name: torchserve-tmp
          emptyDir: {}
        - name: torchserve-logs
          emptyDir: {}
---
{{- end }}
{{- else }}
# Source: torchserve/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve-reranking-svc-deployment
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  replicas: {{ include "getReplicas" (list .filename .Values) | default 4 }}
  selector:
    matchLabels:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 6 }}
  template:
    metadata:
      {{- include "manifest.podLabels" (list .filename .) | nindent 6 }}
    spec:
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
      initContainers:
        - name: cache-warmer
          {{- include "manifest.torchserve.reranking.containerFields" (list . (list "TORCHSERVE_PRELOAD_MODE=1")) | nindent 10 }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: torchserve-reranking
          {{- include "manifest.torchserve.reranking.containerFields" (list . (list)) | nindent 10 }}
          ports:
            - name: http
              containerPort: 8090
              protocol: TCP
            - name: management
              containerPort: 8091
              protocol: TCP
            - name: metrics
              containerPort: 8092
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: ping
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            exec:
              command: {{- include "manifest.torchserve.probeInferenceCmd" . | nindent 14 }}
            initialDelaySeconds: 5
            periodSeconds: 30
            timeoutSeconds: 60
            failureThreshold: 20
          startupProbe:
            exec:
              command: {{- include "manifest.torchserve.probeInferenceCmd" . | nindent 14 }}
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 60
            failureThreshold: 120
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ .Values.pvc.modelReranker.name }}
        - name: model-store
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 1Gi
        - name: tmp
          emptyDir: {}
        - name: torchserve-tmp
          emptyDir: {}
        - name: torchserve-logs
          emptyDir: {}
---

{{- if and .Values.hpaEnabled (not .Values.balloons.enabled) }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: torchserve-reranking
  labels:
  {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: torchserve-reranking-svc-deployment
  minReplicas: {{ ( ((index .Values "services" .filename).hpa).minReplicas | default 1) }}
  maxReplicas: {{ ( ((index .Values "services" .filename).hpa).maxReplicas | default 3) }}
  metrics:
  - type: Object
    object:
      metric:
        name: torchserve_reranking_query_latency
      describedObject:
        apiVersion: v1
        kind: Service
        name: torchserve-reranking-svc
      target:
        type: Value
        value: {{ ( ((index .Values "services" .filename).hpa).targetValue | default "1000m") }}
  {{- $hpaBehavior := ( ((index .Values "services" .filename).hpa).behavior) }}
  {{- if $hpaBehavior }}
  behavior:
    {{- toYaml $hpaBehavior | nindent 4 }}
  {{- else }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 180
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
        value: 25
        periodSeconds: 60
      - type: Pods
        value: 1
        periodSeconds: 60
  {{- end }}
{{- end }}
{{- end }}
