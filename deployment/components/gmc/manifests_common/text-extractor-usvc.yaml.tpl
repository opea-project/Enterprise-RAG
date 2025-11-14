---
# Source: text-extractor-usvc/templates/configmap.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: text-extractor-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: text-extractor-usvc/templates/service.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: text-extractor
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 9398
      targetPort: 9398
      protocol: TCP
      name: text-extractor
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: text-extractor
    app.kubernetes.io/instance: text-extractor
  name: text-extractor
---
# Source: text-extractor-usvc/templates/deployment.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: text-extractor
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
      serviceAccountName: text-extractor
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: text-extractor
          envFrom:
            - configMapRef:
                name: text-extractor-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
            - name: OMP_THREAD_LIMIT
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
            - name: PDF_MAX_WORKERS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: text-extractor
              containerPort: 9398
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
            - mountPath: /home/user/nltk_data
              name: nltk-data
            - mountPath: /home/user/.config
              name: config-dir
            - mountPath: /home/user/.cache
              name: cache-dir
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: text-extractor
            initialDelaySeconds: 5
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: text-extractor
            initialDelaySeconds: 5
            periodSeconds: 30
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: text-extractor
            initialDelaySeconds: 5
            periodSeconds: 30
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '1Gi'}, limits: {cpu: '4', memory: '8Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
        - name: nltk-data
          emptyDir: {}
        - name: config-dir
          emptyDir: {}
        - name: cache-dir
          emptyDir: {}
