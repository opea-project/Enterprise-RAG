---
# Source: text-compression-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: text-compression-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: text-compression-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: text-compression
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 9397
      targetPort: 9397
      protocol: TCP
      name: txt-compression
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: text-compression
    app.kubernetes.io/instance: text-compression
  name: text-compression
---
# Source: text-compression-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: text-compression
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
      serviceAccountName: text-compression
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: text-compression
          envFrom:
            - configMapRef:
                name: text-compression-config
            - configMapRef:
                name: extra-env-config
                optional: true
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: txt-compression
              containerPort: 9397
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: txt-compression
            initialDelaySeconds: 5
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: txt-compression
            initialDelaySeconds: 5
            periodSeconds: 30
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: txt-compression
            initialDelaySeconds: 5
            periodSeconds: 30
          resources:
            {{- $defaultValues := "{requests: {cpu: '0.5', memory: '64Mi'}, limits: {cpu: '2', memory: '1Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
