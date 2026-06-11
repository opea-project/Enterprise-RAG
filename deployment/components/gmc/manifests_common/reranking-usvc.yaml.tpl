{{- $envData := include "manifest.addEnvsAndEnvFile" (list .filename .) -}}
{{- $filteredEnvData := regexReplaceAll "(?m)^RERANKING_VLLM_API_KEY:.*\n?" $envData "" -}}
---
# Source: reranking-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: reranking-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- $filteredEnvData | nindent 2 }}
  RERANKING_SERVICE_ENDPOINT: "http://reranking-usvc-teirerank"
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
# Source: reranking-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: reranking-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 8000
      targetPort: 8000
      protocol: TCP
      name: reranking-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: reranking-usvc
    app.kubernetes.io/instance: reranking-usvc
  name: reranking-usvc
---
# Source: reranking-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: reranking-usvc
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
      serviceAccountName: reranking-usvc
      initContainers:
        - name: wait-for-svc
          image: alpine/curl
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          envFrom:
            - configMapRef:
                name: reranking-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          command:
            - sh
            - -c
            - |
                if [ -z "$RERANKING_SERVICE_ENDPOINT" ]; then
                  echo "Environment variable RERANKING_SERVICE_ENDPOINT is not set. Skipping the init container.";
                elif [ "$RERANKING_MODEL_SERVER" = "nai" ]; then
                  echo "RERANKING_MODEL_SERVER is 'nai' (external endpoint). Skipping readiness check.";
                elif [ -z "$RERANKING_MODEL_NAME" ]; then
                  echo "Environment variable RERANKING_MODEL_NAME is not set. Skipping torchserve check.";
                elif [ "$RERANKING_MODEL_SERVER" = "torchserve" ]; then
                  MODEL_NAME=$(basename "${RERANKING_MODEL_NAME}")
                  PREDICTIONS_ENDPOINT="${RERANKING_SERVICE_ENDPOINT}/predictions/${MODEL_NAME}"
                  echo "Waiting for torchserve reranking server at ${PREDICTIONS_ENDPOINT}...";
                  until curl -sf -X POST "${PREDICTIONS_ENDPOINT}" \
                    -H "Content-Type: application/json" \
                    -d '{"query": "readiness check", "texts": ["test document"]}' \
                    | grep -q '\['; do
                    echo "waiting for torchserve reranking server ${PREDICTIONS_ENDPOINT} to be ready...";
                    sleep 5;
                  done;
                else
                  until curl -sf "${RERANKING_SERVICE_ENDPOINT}/health"; do
                    echo "waiting for reranking server $RERANKING_SERVICE_ENDPOINT to be ready...";
                    sleep 5;
                  done;
                fi;
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: reranking-usvc
          envFrom:
            - configMapRef:
                name: reranking-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: RERANKING_VLLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: reranking-vllm-api-key-secret
                  key: RERANKING_VLLM_API_KEY
                  optional: true
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: true
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: reranking-usvc
              containerPort: 8000
              protocol: TCP
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: reranking-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
            timeoutSeconds: 10
          readinessProbe:
            failureThreshold: 5
            httpGet:
              path: v1/health_check
              port: reranking-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
            timeoutSeconds: 10
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: reranking-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
            timeoutSeconds: 10
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '2Gi'}, limits: {cpu: '4', memory: '2Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}

