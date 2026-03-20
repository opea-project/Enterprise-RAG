---
# Source: query-rewrite-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: query-rewrite-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
  {{ if .Values.chat_history.enabled }}
  CHAT_HISTORY_ENDPOINT: "http://chat-history-svc.chat-history.svc:6012"
  {{ end }}
---
# Source: query-rewrite-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: query-rewrite-svc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 6626
      targetPort: 6626
      protocol: TCP
      name: query-rewrite-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: query-rewrite-usvc
    app.kubernetes.io/instance: query-rewrite-usvc
  name: query-rewrite-usvc
---
# Source: query-rewrite-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: query-rewrite-usvc
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
      serviceAccountName: query-rewrite-usvc
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      initContainers:
        - name: wait-for-llm-service
          image: alpine/curl
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          command:
            - sh
            - -c
            - |
                if [ -z "$QUERY_REWRITE_LLM_ENDPOINT" ]; then
                  echo "Environment variable QUERY_REWRITE_LLM_ENDPOINT is not set. Skipping the init container.";
                else
                  until [ "$(curl -s -o /dev/null -w '%{http_code}' ${QUERY_REWRITE_LLM_ENDPOINT}/health)" = "200" ]; do
                    echo "waiting for LLM service $QUERY_REWRITE_LLM_ENDPOINT to return HTTP 200...";
                    sleep 2;
                  done;
                  echo "LLM service is ready!";
                fi;
      {{ if .Values.chat_history.enabled }}
        - name: wait-for-chat-history
          image: alpine/curl
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          env:
            - name: CHAT_HISTORY_ENDPOINT
              valueFrom:
                configMapKeyRef:
                  name: query-rewrite-usvc-config
                  key: CHAT_HISTORY_ENDPOINT
          command:
            - sh
            - -c
            - |
                if [ -z "$CHAT_HISTORY_ENDPOINT" ]; then
                  echo "Environment variable CHAT_HISTORY_ENDPOINT is not set. Skipping the init container.";
                else
                  until curl -s $CHAT_HISTORY_ENDPOINT; do
                    echo "waiting for chat history service $CHAT_HISTORY_ENDPOINT to be ready...";
                    sleep 2;
                  done;
                fi;
      {{ end }}
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: query-rewrite-usvc
          envFrom:
            - configMapRef:
                name: query-rewrite-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: true
            runAsUser: 1000
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: query-rewrite
              containerPort: 6626
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: query-rewrite
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: query-rewrite
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: {{ include "manifest.tdx.values" (dict "default" 120 "name" .filename "Values" .Values "type" "startupProbe.failureThreshold") | trim }}
            httpGet:
              path: v1/health_check
              port: query-rewrite
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '500m', memory: '1Gi'}, limits: {cpu: '2', memory: '2Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}

