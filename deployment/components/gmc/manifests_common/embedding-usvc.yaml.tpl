---
# Source: embedding-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: embedding-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: embedding-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: embedding-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 6000
      targetPort: 6000
      protocol: TCP
      name: embedding-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: embedding-usvc
    app.kubernetes.io/instance: embedding-usvc
  name: embedding-usvc
---
# Source: embedding-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: embedding-usvc
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
      serviceAccountName: embedding-usvc
      initContainers:
        - name: wait-for-embedding
          image: alpine/curl
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: true
          command:
            - sh
            - -c
            - |
                if [ -z "$EMBEDDING_MODEL_SERVER_ENDPOINT" ]; then
                  echo "Environment variable EMBEDDING_MODEL_SERVER_ENDPOINT is not set. Skipping the init container.";
                else
                  until curl -s $EMBEDDING_MODEL_SERVER_ENDPOINT; do
                    echo "waiting for embedding model server $EMBEDDING_MODEL_SERVER_ENDPOINT to be ready...";
                    sleep 2;
                  done;
                fi;
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: embedding-usvc
          envFrom:
            - configMapRef:
                name: embedding-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: embedding-usvc
              containerPort: 6000
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: embedding-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: embedding-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: embedding-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '2Gi'}, limits: {cpu: '4', memory: '4Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
