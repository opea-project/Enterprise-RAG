---
# Source: docsum-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: docsum-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: docsum-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: docsum-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 9001
      targetPort: 9001
      protocol: TCP
      name: docsum-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: docsum-usvc
    app.kubernetes.io/instance: docsum-usvc
  name: docsum-usvc
---
# Source: docsum-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: docsum-usvc
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
      serviceAccountName: docsum-usvc
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
                if [ -z "$DOCSUM_LLM_USVC_ENDPOINT" ]; then
                  echo "Environment variable DOCSUM_LLM_USVC_ENDPOINT is not set. Skipping the init container.";
                else
                  until [ "$(curl -s -o /dev/null -w '%{http_code}' ${DOCSUM_LLM_USVC_ENDPOINT}/v1/health_check)" = "200" ]; do
                    echo "waiting for LLM service $DOCSUM_LLM_USVC_ENDPOINT to return HTTP 200...";
                    sleep 2;
                  done;
                  echo "LLM service is ready!";
                fi;
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: docsum-usvc
          envFrom:
            - configMapRef:
                name: docsum-usvc-config
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
            - name: docsum-usvc
              containerPort: 9001
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: docsum-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: docsum-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: {{ include "manifest.tdx.values" (dict "default" 120 "name" .filename "Values" .Values "type" "startupProbe.failureThreshold") | trim }}
            httpGet:
              path: v1/health_check
              port: docsum-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '2Gi'}, limits: {cpu: '4', memory: '4Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}

