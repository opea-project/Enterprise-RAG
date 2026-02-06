---
# Source: fgp-usvc/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: ConfigMap
metadata:
  name: fgp-usvc-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
  SYSTEM_FINGERPRINT_MONGODB_HOST: "fingerprint-mongodb-ferretdb.fingerprint.svc"
  SYSTEM_FINGERPRINT_MONGODB_PORT: "27017"
  MONGODB_NAME: "SYSTEM_FINGERPRINT"

---
# Source: fgp-usvc/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: fgp-usvc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 6012
      targetPort: 6012
      protocol: TCP
      name: fgp-usvc
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: fgp-usvc
    app.kubernetes.io/instance: fgp-usvc
  name: fgp-usvc
---
# Source: fgp-usvc/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: apps/v1
kind: Deployment
metadata:
  name: fgp-usvc
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
      {{- include "gmc.imagePullSecrets" . }}
      serviceAccountName: fgp-usvc
      initContainers:
        - name: wait-for-ferretdb
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: busybox:1.35
          env:
            - name: FERRETDB_HOST
              value: "fingerprint-mongodb-ferretdb.fingerprint.svc"
            - name: FERRETDB_PORT
              value: "27017"
          command:
            - sh
            - -c
            - |
                until nc -z $FERRETDB_HOST $FERRETDB_PORT; do
                  echo "Waiting for FerretDB server $FERRETDB_HOST:$FERRETDB_PORT to be ready...";
                  sleep 2;
                done;
                echo "FerretDB server $FERRETDB_HOST:$FERRETDB_PORT is ready!";
      containers:
        - name: fgp-usvc
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          ports:
            - name: fgp-usvc
              containerPort: 6012
              protocol: TCP
          env:
            - name: MONGODB_NAME
              value: "SYSTEM_FINGERPRINT"
            - name: MONGO_USER
              valueFrom:
                secretKeyRef:
                  name: mongo-database-secret
                  key: POSTGRES_USER
            - name: MONGO_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mongo-database-secret
                  key: POSTGRES_PASSWORD
          envFrom:
            - configMapRef:
                name: fgp-usvc-config
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          volumeMounts:
            - mountPath: /tmp
              name: tmp
          livenessProbe:
            failureThreshold: 24
            httpGet:
              path: v1/health_check
              port: fgp-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          readinessProbe:
            httpGet:
              path: v1/health_check
              port: fgp-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          startupProbe:
            failureThreshold: 60
            httpGet:
              path: v1/health_check
              port: fgp-usvc
            initialDelaySeconds: 5
            periodSeconds: 60
          resources:
            {{- $defaultValues := "{requests: {cpu: '250m', memory: '64Mi'}, limits: {cpu: '500m', memory: '1Gi'}}" -}}
            {{- include "manifest.getResource" (list .filename $defaultValues .Values) | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}

