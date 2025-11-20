{{/*
Expand the name of the chart.
*/}}
{{- define "gmc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "gmc.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "gmc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "gmc.labels" -}}
helm.sh/chart: {{ include "gmc.chart" . }}
{{ include "gmc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "gmc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "gmc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "gmc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "gmc.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Common labels for manifests with deployment name as an argument
*/}}
{{- define "manifest.labels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
helm.sh/chart: {{ printf "%s-%s" $deploymentName $context.Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ $deploymentName }}
app.kubernetes.io/instance: {{ $deploymentName }}
app.kubernetes.io/version: {{ $context.Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ $context.Release.Service }}
{{- end }}


{{/*
Selector labels for manifests with deployment name as an argument
*/}}
{{- define "manifest.selectorLabels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
app.kubernetes.io/name: {{ $deploymentName }}
app.kubernetes.io/instance: {{ $deploymentName }}
{{- end }}


{{/*
Generic pod label definition
*/}}
{{- define "manifest.podLabels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
labels:
  {{- include "manifest.selectorLabels" (list $deploymentName $context) | nindent 2 }}
{{- if $context.Values.tdx }}
  {{- include "manifest.tdx.labels" (list $deploymentName $context) | nindent 2 }}
{{- end }}
{{- end }}


{{/*
Helper placeholder for image pull secrets
*/}}
{{- define "gmc.imagePullSecrets" -}}
{{- if .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- range .Values.imagePullSecrets }}
          - name: {{ .name }}
        {{- end }}
      {{- end }}
{{- end }}



{{/*
Helper for adding environment variables and env files
*/}}
    {{- define "manifest.addEnvsAndEnvFile" -}}
    {{- $deploymentName := index . 0 -}}
    {{- $context := index . 1 -}}
    {{- $imageKey := index $context.Values.images $deploymentName -}}
    {{- if $imageKey.envfile }}
        {{- $envfile := (printf "envs/%s" $imageKey.envfile) }}
        {{- $envContent := $context.Files.Get $envfile }}
        {{- $envContent = regexReplaceAll "#.*" $envContent "" | trim }}
        {{- $envContent = regexReplaceAll "(?m)\\s+$" $envContent "" }}
        {{- $envContent = $envContent | replace "=" ": " }}
        {{- $envContent = regexReplaceAll "(?m)^([^:]+):\\s*[\"']?(.*?)[\"']?$" $envContent "$1: \"$2\"" }}
        {{- $envContent }}
    {{- end -}}
    {{- if $imageKey.envs }}
        {{- range $key, $value := $imageKey.envs }}
            {{- $key | nindent 0 }}: {{ $value | quote }}
        {{- end -}}
    {{- end -}}
{{- end -}}

{{- /*
  Retrieves resource values based on the provided filename and values.
*/ -}}
{{- define "manifest.getResource" -}}
{{- $filename := index . 0 -}}
{{- $defaultValues := fromYaml (index . 1) -}}
{{- $values := index . 2 -}}

{{- if and ($values.services) (index $values "services" $filename) (index $values "services" $filename "resources") }}
  {{- $defaultValues = index $values "services" $filename "resources" }}
{{- end -}}

{{- $isTDXEnabled := hasKey $values "tdx" -}}
{{- $isGaudiService := regexMatch "(?i)gaudi" $filename -}}

{{- if and $isTDXEnabled (not $isGaudiService) }}
  {{- include "manifest.tdx.getResourceValues" (dict "defaultValues" $defaultValues "filename" $filename "values" $values) }}
{{- else }}
  {{- $defaultValues | toYaml }}
{{- end -}}
{{- end -}}

{{- /*
  Retrieves replica values based on the provided filename and values.
*/ -}}
{{- define "getReplicas" -}}
{{- $filename := index . 0 -}}
{{- $values := index . 1 -}}

{{- if and ($values.services) (index $values "services" $filename) (index $values "services" $filename "replicas") }}
  {{- index $values "services" $filename "replicas" }}
{{- end -}}
{{- end -}}


{{- define "manifest.image" -}}
{{- $filename := index . 0 -}}
{{- $values := index . 1 -}}
{{- $alternateTagging := index $values "alternateTagging" -}}
{{- if $alternateTagging -}}
{{- printf "%s:%s_%s" (index $values "images" $filename "repository") (index $values "images" $filename "image") (index $values "images" $filename "tag") -}}
{{- else -}}
{{- printf "%s/%s:%s" (index $values "images" $filename "repository") (index $values "images" $filename "image") (index $values "images" $filename "tag") -}}
{{- end -}}
{{- end -}}

{{/*
Init container that waits for balloons DaemonSet to be ready
Usage: {{ include "manifest.balloons.initContainer" . }}
*/}}
{{- define "manifest.balloons.initContainer" -}}
{{- if .Values.balloons.enabled }}
- name: wait-for-balloons
  image: {{ include "manifest.image" (list "init-container" .Values) }}
  securityContext:
    runAsUser: 1000
    allowPrivilegeEscalation: false
    capabilities:
      drop:
        - ALL
  command:
    - /bin/sh
    - -c
    - |
      set -e
      echo "Waiting for all {{ .Values.balloons.chart_name }} DaemonSet pods to be ready..."
      SECONDS=0
      TIMEOUT={{ .Values.balloons.wait_timeout | default 300 }}
      while true; do
        DESIRED=$(kubectl get daemonset {{ .Values.balloons.chart_name }} -n {{ .Values.balloons.namespace }} -o jsonpath="{.status.desiredNumberScheduled}")
        READY=$(kubectl get daemonset {{ .Values.balloons.chart_name }} -n {{ .Values.balloons.namespace }} -o jsonpath="{.status.numberReady}")
        if [ "$DESIRED" = "$READY" ] && [ "$DESIRED" != "" ]; then
          echo "All pods ready: $READY/$DESIRED"
          break
        fi
        if [ "$SECONDS" -ge "$TIMEOUT" ]; then
          echo "Timeout waiting for all pods to be ready ($READY/$DESIRED)"
          exit 1
        fi
        echo "Waiting... ($READY/$DESIRED ready)"
        sleep 5
      done
  resources:
    requests:
      cpu: 10m
      memory: 32Mi
    limits:
      cpu: 100m
      memory: 128Mi
{{- end -}}
{{- end -}}
