---
# Source: text-splitter-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: text-splitter-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: text-splitter-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: text-splitter
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 9399
      targetPort: 9399
      protocol: TCP
      name: text-splitter
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: text-splitter
    app.kubernetes.io/instance: text-splitter
  name: text-splitter
---
# Source: text-splitter-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: text-splitter
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
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      serviceAccountName: text-splitter
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: text-splitter
          envFrom:
            - configMapRef:
                name: text-splitter-config
            - configMapRef:
                name: extra-env-config
                optional: true
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: text-splitter
              containerPort: 9399
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: text-splitter
            initialDelaySeconds: 5
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: text-splitter
            initialDelaySeconds: 5
            periodSeconds: 30
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: text-splitter
            initialDelaySeconds: 5
            periodSeconds: 30
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '512Mi'}, limits: {cpu: '2', memory: '4Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
