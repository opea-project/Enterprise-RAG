---
# Source: vllm-query-rewrite/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
{{- $modelName := .Values.query_rewrite_model | default "AMead10/Llama-3.2-3B-Instruct-AWQ" }}
{{- $port := "8000" }}

apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-query-rewrite-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  LLM_VLLM_MODEL_NAME: {{ $modelName | quote }}
  LLM_DEVICE: "cpu"
  VLLM_TARGET_DEVICE: "cpu"
  PORT: {{ $port | quote }}
  VLLM_CPU_KVCACHE_SPACE: "40"
  VLLM_DTYPE: "bfloat16"
  VLLM_MAX_NUM_SEQS: "256"
  VLLM_TP_SIZE: "1"
  VLLM_PP_SIZE: "1"
  VLLM_MAX_MODEL_LEN: "4096"
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
{{- if not .Values.balloons.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-query-rewrite-assign-cores
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
   assign_cores.sh: |
{{ (.Files.Get "envs/src/comps/llms/impl/model_server/vllm/docker/assign_cores.sh" | indent 4) }}
{{- end }}
{{- if and .Values.vllmNodes .Values.balloons.enabled }}
{{- range .Values.vllmNodes }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-query-rewrite-pvc-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
{{- end }}
{{- else }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-query-rewrite-pvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
{{- end }}
---
# Source: vllm-query-rewrite/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: vllm-query-rewrite-svc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: {{ $port }}
      targetPort: 8000
      protocol: TCP
      name: vllm-query-rewrite
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
# Source: vllm-query-rewrite/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

{{- if and .Values.vllmNodes .Values.balloons.enabled }}
{{- range .Values.vllmNodes }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-query-rewrite-svc-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
    query-rewrite-node: {{ .name }}
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "manifest.selectorLabels" (list $.filename $) | nindent 6 }}
      query-rewrite-node: {{ .name }}
  template:
    metadata:
      labels:
        {{- include "manifest.selectorLabels" (list $.filename $) | nindent 8 }}
        query-rewrite-node: {{ .name }}
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
        - name: vllm-query-rewrite
          envFrom:
            - configMapRef:
                name: vllm-query-rewrite-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: HF_HOME
              value: /tmp/.cache
            - name: USER
              value: user
          {{- if $.Values.tokens.hugToken }}
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
            {{- toYaml $.Values.securityContext | nindent 12 }}
          image: public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.14.0
          imagePullPolicy: IfNotPresent
          command:
            - bash
            - -c
            - |
                export VLLM_CPU_OMP_THREADS_BIND=$(tr ' ' ',' < /sys/fs/cgroup/cpuset.cpus.effective)
                python3 -m vllm.entrypoints.openai.api_server --model {{ $modelName }} --quantization awq --pipeline-parallel-size $VLLM_PP_SIZE --dtype $VLLM_DTYPE --max-model-len $VLLM_MAX_MODEL_LEN --max-num-seqs $VLLM_MAX_NUM_SEQS --enforce-eager --disable-log-requests --download-dir /data --port 8000
          resources:
            {{- $defaultValues := "{requests: {cpu: '16', memory: '32Gi'}, limits: {cpu: '16', memory: '48Gi'}}" -}}
            {{- include "manifest.getResource" (list $.filename $defaultValues $.Values) | nindent 12 }}
          volumeMounts:
            - mountPath: /data
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /dev/shm
              name: shm
            - mountPath: /.cache
              name: cache
            - mountPath: /home/user/.config
              name: config
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 120
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 120
            periodSeconds: 60
          startupProbe:
            failureThreshold: 240
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 30
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: model-query-rewrite-pvc-{{ .name }}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 12Gi
        - name: tmp
          emptyDir: {}
        - name: cache
          emptyDir: {}
        - name: config
          emptyDir: {}
---
{{- end }}
{{- else }}
# Source: vllm-query-rewrite/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-query-rewrite-svc-deployment
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
      containers:
        - name: vllm-query-rewrite
          envFrom:
            - configMapRef:
                name: vllm-query-rewrite-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: HF_HOME
              value: /tmp/.cache
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
            - name: VLLM_POD_INDEX
              value: "0"
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.11.2
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          command:
            - bash
            - -c
            - |
                source /etc/helpers/assign_cores.sh
                python3 -m vllm.entrypoints.openai.api_server --model $LLM_VLLM_MODEL_NAME --quantization awq --pipeline-parallel-size $VLLM_PP_SIZE --dtype $VLLM_DTYPE --max-model-len $VLLM_MAX_MODEL_LEN --max-num-seqs $VLLM_MAX_NUM_SEQS --enforce-eager --disable-log-requests --download-dir /data --port 8000
          resources:
            {{- $defaultValues := "{requests: {cpu: '16', memory: '32Gi'}, limits: {cpu: '16', memory: '48Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
          volumeMounts:
            - mountPath: /data
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /dev/shm
              name: shm
            - mountPath: /.cache
              name: cache
            - mountPath: /home/user/.config
              name: config
            - mountPath: /etc/helpers
              name: assign-cores-volume
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 120
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 120
            periodSeconds: 60
          startupProbe:
            failureThreshold: 240
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 30
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: model-query-rewrite-pvc
        - name: tmp
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 12Gi
        - name: cache
          emptyDir: {}
        - name: config
          emptyDir: {}
        - name: assign-cores-volume
          configMap:
            name: vllm-query-rewrite-assign-cores
{{- end }}
