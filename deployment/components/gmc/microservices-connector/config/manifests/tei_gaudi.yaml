---
# Source: tei/templates/configmap.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: tei-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  MODEL_ID: "BAAI/bge-base-en-v1.5"
  PORT: "2081"
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
  NUMBA_CACHE_DIR: "/tmp"
  TRANSFORMERS_CACHE: "/tmp/transformers_cache"
  HF_HOME: "/tmp/.cache/huggingface"
  MAX_WARMUP_SEQUENCE_LENGTH: "512"
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
# Source: tei/templates/service.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: tei
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 2081
      protocol: TCP
      name: tei
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
# Source: tei/templates/deployment.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: tei
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  replicas: {{ include "getReplicas" (list .filename .Values) | default 1 }}
  selector:
    matchLabels:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "manifest.selectorLabels" (list .filename .) | nindent 8 }}
    spec:
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: tei
          envFrom:
            - configMapRef:
                name: tei-config
            - configMapRef:
                name: extra-env-config
                optional: true
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "ghcr.io/huggingface/tei-gaudi:1.5.3"
          imagePullPolicy: IfNotPresent
          args:
            - "--auto-truncate"
          volumeMounts:
            - mountPath: /data
              name: model-volume
            - mountPath: /dev/shm
              name: shm
            - mountPath: /tmp
              name: tmp
          ports:
            - name: http
              containerPort: 2081
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{limits: {habana.ai/gaudi: '1'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
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
