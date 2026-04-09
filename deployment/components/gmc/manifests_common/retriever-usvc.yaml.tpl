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
    spec:
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
        {{- else if eq (index .Values "images" .filename "vector_store") "mssql" }}
          {{- include "mssql_init_container" . | nindent 8 }}
        {{- end }}
        - name: wait-for-ner-service
          image: alpine/curl
          envFrom:
            - configMapRef:
                name: retriever-usvc-config
            - configMapRef:
                name: extra-env-config
                optional: true
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          command:
            - sh
            - -c
            - |
                if [ -z "$NER_ENDPOINT" ]; then
                  echo "NER_ENDPOINT is not set. Skipping NER readiness wait.";
                  exit 0;
                fi;
                NER_READY_URL="${NER_ENDPOINT%/}/v2/health/ready";
                MAX_WAIT_SECONDS=180;
                SLEEP_SECONDS=2;
                ELAPSED=0;
                echo "Waiting for NER service at ${NER_READY_URL} ...";
                until [ "$ELAPSED" -ge "$MAX_WAIT_SECONDS" ]; do
                  if [ "$(curl -s -o /dev/null -w '%{http_code}' "$NER_READY_URL")" = "200" ]; then
                    echo "NER service is ready.";
                    exit 0;
                  fi;
                  echo "NER not ready yet (${ELAPSED}s/${MAX_WAIT_SECONDS}s). Retrying...";
                  sleep "$SLEEP_SECONDS";
                  ELAPSED=$((ELAPSED + SLEEP_SECONDS));
                done;
                echo "ERROR: Timed out waiting for NER service readiness.";
                exit 1;
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
            timeoutSeconds: 10
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: retriever-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
            timeoutSeconds: 10
          startupProbe:
            failureThreshold: 120
            httpGet:
              path: v1/health_check
              port: retriever-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
            timeoutSeconds: 10
          resources:
            {{- $defaultValues := "{requests: {cpu: '1', memory: '2Gi'}, limits: {cpu: '4', memory: '2Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
        - name: user-cache
          emptyDir: {}

