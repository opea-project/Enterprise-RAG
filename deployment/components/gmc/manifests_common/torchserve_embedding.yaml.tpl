---
# Source: torchserve/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: torchserve-embedding-config
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
  name: {{ $.Values.pvc.modelEmbedding.name }}-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
spec:
  accessModes:
    - {{ $.Values.pvc.modelEmbedding.accessMode }}
  resources:
    requests:
      storage: {{ $.Values.pvc.modelEmbedding.storage }}
{{- end }}
{{- else }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Values.pvc.modelEmbedding.name }}
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  accessModes:
    - {{ .Values.pvc.modelEmbedding.accessMode }}
  resources:
    requests:
      storage: {{ .Values.pvc.modelEmbedding.storage }}
{{- end }}
---
# Source: torchserve/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: torchserve-embedding
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 8090
      targetPort: 8090
      protocol: TCP
      name: torchserve
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
  name: torchserve-embedding-svc-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
    embedding-node: {{ .name }}
spec:
  replicas: {{ .VLLM_INSTANCES | default 1 }}
  selector:
    matchLabels:
      {{- include "manifest.selectorLabels" (list $.filename $) | nindent 6 }}
      embedding-node: {{ .name }}
  template:
    metadata:
      labels:
        {{- include "manifest.selectorLabels" (list $.filename $) | nindent 8 }}
        embedding-node: {{ .name }}
      {{- include "manifest.tdx.annotations" (list $.filename $) | nindent 6 }}
    spec:
      {{- include "manifest.tdx.runtimeClassName" (list $.filename $) | nindent 6 }}
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
      securityContext:
        {{- toYaml $.Values.podSecurityContext | nindent 8 }}
      {{- include "gmc.imagePullSecrets" $ }}
      containers:
        - name: torchserve-embedding
          envFrom:
            - configMapRef:
                name: torchserve-embedding-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
          {{- if $.Values.tokens.hugToken }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token-secret
                  key: HF_TOKEN
          {{- end }}
            - name: TS_ENABLE_METRICS_API
              value: "true"
            - name: TS_METRICS_MODE
              value: prometheus
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
          securityContext:
            {{- toYaml $.Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list $.filename $.Values) }}
          imagePullPolicy: {{ toYaml (index $.Values "images" $.filename "pullPolicy" | default "Always") }}
          resources:
            {{- $defaultValues := "{requests: {cpu: '4', memory: '4Gi'}, limits: {cpu: '4', memory: '16Gi'}}" -}}
            {{- include "manifest.getResource" (list $.filename $defaultValues $.Values) | nindent 12 }}
          volumeMounts:
            - mountPath: /opt/ml/model
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /home/user/tmp
              name: torchserve-tmp
            - mountPath: /home/user/logs
              name: torchserve-logs
          ports:
            - name: http
              containerPort: 8090
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
            httpGet:
              path: ping
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: ping
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ $.Values.pvc.modelEmbedding.name }}-{{ .name }}
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
  name: torchserve-embedding-svc-deployment
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
      containers:
        - name: torchserve-embedding
          envFrom:
            - configMapRef:
                name: torchserve-embedding-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
          {{- if .Values.tokens.hugToken }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token-secret
                  key: HF_TOKEN
          {{- end }}
            - name: KMP_SETTINGS
              value: "1"
            - name: KMP_AFFINITY
              value: "granularity=fine,compact,1,0"
            - name: KMP_BLOCKTIME
              value: "1"
            - name: TS_ENABLE_METRICS_API
              value: "true"
            - name: TS_METRICS_MODE
              value: prometheus
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          resources:
            {{- $defaultValues := "{requests: {cpu: '4', memory: '4Gi'}, limits: {cpu: '4', memory: '16Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
          volumeMounts:
            - mountPath: /opt/ml/model
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /home/user/tmp
              name: torchserve-tmp
            - mountPath: /home/user/logs
              name: torchserve-logs
          ports:
            - name: http
              containerPort: 8090
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
              command:
              - /bin/sh
              - -c
              - |
                MODEL_NAME=$(basename "${TORCHSERVE_MODEL_NAME}")
                curl -sf http://localhost:8090/predictions/${MODEL_NAME} \
                  -H "Content-Type: application/json" \
                  -d '{"inputs": ["readiness check"]}' \
                  | grep -q '\['
            initialDelaySeconds: 5 # adjust this value if the model is large or internet is slow
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: ping
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ .Values.pvc.modelEmbedding.name }}
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
  name: torchserve-embedding
  labels:
  {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: torchserve-embedding-svc-deployment
  minReplicas: {{ ( ((index .Values "services" .filename).hpa).minReplicas | default 4) }}
  maxReplicas: {{ ( ((index .Values "services" .filename).hpa).maxReplicas | default 10) }}
  metrics:
  - type: Object
    object:
      metric:
        name: torchserve_requests_total
      describedObject:
        apiVersion: v1
        kind: Service
        name: torchserve-embedding-svc
      target:
        type: Value
        value: {{ ( ((index .Values "services" .filename).hpa).targetValue | default "150m") }}
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
        periodSeconds: 30
      - type: Pods
        value: 1
        periodSeconds: 30
    scaleUp:
      stabilizationWindowSeconds: 120
      selectPolicy: Max
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
  {{- end }}
{{- end }}
{{- end }}
