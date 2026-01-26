---
# Source: vllm/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
{{- $modelName := required "Please specify a valid embedding_model_name name in your Helm chart values" .Values.embedding_model_name }}
{{- $port := "8108" }}

apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-embedding-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
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
---
# Source: vllm/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: vllm-embedding
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: {{ $port }}
      targetPort: {{ $port }}
      protocol: TCP
      name: vllm-embedding
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
# Source: vllm/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-embedding-svc-deployment
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
        - name: vllm-embedding
          envFrom:
            - configMapRef:
                name: vllm-embedding-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: HF_HOME
              value: /home/user/.cache
            - name: USER
              value: user
          {{- if .Values.tokens.hugToken }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token-secret
                  key: HF_TOKEN
          {{- end }}
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.14.0
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          command:
            - bash
            - -c
            - |
                {{- if .Values.balloons.enabled }}
                export VLLM_CPU_OMP_THREADS_BIND=$(tr ' ' ',' < /sys/fs/cgroup/cpuset.cpus.effective)
                {{- end }}
                python3 -m vllm.entrypoints.openai.api_server --model {{ $modelName }} --dtype $VLLM_DTYPE --enforce_eager --download-dir /data --host 0.0.0.0 --port {{ $port }}
          resources:
            {{- $defaultValues := "{requests: {cpu: '4', memory: '4Gi'}, limits: {cpu: '4', memory: '16Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
          volumeMounts:
            - mountPath: /data
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /dev/shm
              name: shm
            - mountPath: /home/user/.cache
              name: cache
            - mountPath: /home/user/.config
              name: config
          ports:
            - name: http
              containerPort: {{ $port }}
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 60
          readinessProbe:
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 60
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ .Values.pvc.modelEmbedding.name }}
        - name: tmp
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 1Gi
        - name: cache
          emptyDir: {}
        - name: config
          emptyDir: {}
---
{{- if and .Values.hpaEnabled (not .Values.balloons.enabled) }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-embedding
  labels:
  {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-embedding-svc-deployment
  minReplicas: {{ ( ((index .Values "services" .filename).hpa).minReplicas | default 4) }}
  maxReplicas: {{ ( ((index .Values "services" .filename).hpa).maxReplicas | default 10) }}
  metrics:
  - type: Object
    object:
      metric:
        name: vllm:request_total
      describedObject:
        apiVersion: v1
        kind: Service
        name: vllm-embedding
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
