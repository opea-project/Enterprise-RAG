---
# Source: prmpt-tmpl-usvc/templates/configmap.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: prompttemplate-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
  PORT: "7900"
  {{ if .Values.chat_history.enabled }}
  CHAT_HISTORY_ENDPOINT: "http://chat-history-svc.chat-history.svc:6012"
  {{ end }}
---
# Source: prmpt-tmpl-usvc/templates/service.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: prmpt-tmpl-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 7900
      targetPort: 7900
      protocol: TCP
      name: prmpt-tmpl-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: prmpt-tmpl-usvc
    app.kubernetes.io/instance: prmpt-tmpl-usvc
  name: prmpt-tmpl-usvc
---
# Source: prmpt-tmpl-usvc/templates/deployment.yaml
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: prmpt-tmpl-usvc
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
      serviceAccountName: prmpt-tmpl-usvc
      {{ if .Values.chat_history.enabled }}
      initContainers:
        - name: wait-for-svc
          image: alpine/curl
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          env:
            - name: CHAT_HISTORY_ENDPOINT
              valueFrom:
                configMapKeyRef:
                  name: prompttemplate-usvc-config
                  key: CHAT_HISTORY_ENDPOINT
          command:
            - sh
            - -c
            - |
                if [ -z "$CHAT_HISTORY_ENDPOINT" ]; then
                  echo "Environment variable CHAT_HISTORY_ENDPOINT is not set. Skipping the init container.";
                else
                  until curl -s $CHAT_HISTORY_ENDPOINT; do
                    echo "waiting for reranking server $CHAT_HISTORY_ENDPOINT to be ready...";
                    sleep 2;
                  done;
                fi;
      {{ end }}
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: prmpt-tmpl-usvc
          envFrom:
            - configMapRef:
                name: prompttemplate-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: prmpt-tmpl-usvc
              containerPort: 7900
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: prmpt-tmpl-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: prmpt-tmpl-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: prmpt-tmpl-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '2Gi'}, limits: {cpu: '4', memory: '2Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}

