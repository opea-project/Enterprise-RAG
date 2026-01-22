---
# Source: retriever-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: retriever-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
---
# Source: retriever-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: retriever-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 6620
      targetPort: 6620
      protocol: TCP
      name: retriever-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: retriever-usvc
    app.kubernetes.io/instance: retriever-usvc
  name: retriever-usvc
---
# Source: retriever-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: retriever-usvc
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
      serviceAccountName: retriever-usvc
      initContainers:
        {{- if eq (index .Values "images" .filename "vector_store") "redis" }}
          {{- include "redis_init_container" . | nindent 8 }}
        {{- else if eq (index .Values "images" .filename "vector_store") "redis-cluster" }}
          {{- include "redis_init_container" . | nindent 8 }}
        {{- else if eq (index .Values "images" .filename "vector_store") "pgvector" }}
          {{- include "postgresql_init_container" . | nindent 8 }}
        {{- end }}
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: retriever-usvc
          envFrom:
            - configMapRef:
                name: retriever-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
            - secretRef:
                name: vector-database-config
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: true
            seccompProfile:
              type: RuntimeDefault
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: retriever-usvc
              containerPort: 6620
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
            - mountPath: /home/user/.cache
              name: user-cache
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: retriever-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: retriever-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: retriever-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '2Gi'}, limits: {cpu: '4', memory: '2Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
        - name: user-cache
          emptyDir: {}

