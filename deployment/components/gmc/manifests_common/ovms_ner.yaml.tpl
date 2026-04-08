---
# Source: ovms_ner/templates/configmap.yaml
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: ovms-ner-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: ovms_ner/templates/pvc.yaml
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Values.pvc.modelNer.name }}
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  accessModes:
    - {{ .Values.pvc.modelNer.accessMode }}
  resources:
    requests:
      storage: {{ .Values.pvc.modelNer.storage }}
---
# Source: ovms_ner/templates/service.yaml
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: retriever-ner-ovms
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 9001
      targetPort: 9001
      protocol: TCP
      name: ner-ovms
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
# Source: ovms_ner/templates/serviceaccount.yaml
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: ovms-ner
    app.kubernetes.io/instance: ovms-ner
  name: retriever-ner-ovms
---
# Source: ovms_ner/templates/deployment.yaml
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: retriever-ner-ovms-deployment
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
    spec:
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      serviceAccountName: retriever-ner-ovms
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: ovms-ner
          envFrom:
            - configMapRef:
                name: ovms-ner-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: HOME
              value: /tmp
            - name: XDG_CACHE_HOME
              value: /tmp/.cache
            - name: HF_HOME
              value: /tmp/.cache/huggingface
            - name: TRANSFORMERS_CACHE
              value: /tmp/.cache/huggingface
            - name: MPLCONFIGDIR
              value: /tmp/matplotlib
          {{- if .Values.tokens.hugToken }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token-secret
                  key: HF_TOKEN
          {{- end }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          resources:
            {{- $defaultValues := "{requests: {cpu: '2', memory: '4Gi'}, limits: {cpu: '4', memory: '8Gi'}}" -}}
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
            - mountPath: /model
              name: model-staging
          ports:
            - name: http
              containerPort: 9001
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: /v2/health/ready
              port: http
            initialDelaySeconds: 30
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: /v2/health/ready
              port: http
            initialDelaySeconds: 30
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: /v2/health/ready
              port: http
            initialDelaySeconds: 30
            periodSeconds: 60
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ .Values.pvc.modelNer.name }}
        - name: tmp
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 1Gi
        - name: cache
          emptyDir: {}
        - name: model-staging
          emptyDir: {}
