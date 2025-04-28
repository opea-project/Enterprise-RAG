{{/*
Expand the name of the chart.
*/}}

{{- define "helm-edp.celery_backend_url" -}}
{{- if .Values.redisPassword }}
{{- printf "redis://%s:%s@%s" .Values.redisUsername .Values.redisPassword .Values.redisUrl }}
{{- else }}
{{- printf "redis://%s" .Values.redisUrl }}
{{- end }}
{{- end }}

{{- define "helm-edp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.celery.name" -}}
{{- default .Chart.Name .Values.celery.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.backend.name" -}}
{{- default .Chart.Name .Values.backend.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.flower.name" -}}
{{- default .Chart.Name .Values.flower.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.dataprep.name" -}}
{{- default .Chart.Name .Values.dataprep.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.dpguard.name" -}}
{{- default .Chart.Name .Values.dpguard.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.embedding.name" -}}
{{- default .Chart.Name .Values.embedding.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.ingestion.name" -}}
{{- default .Chart.Name .Values.ingestion.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.vllm.name" -}}
{{- default .Chart.Name .Values.vllm.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "helm-edp.noProxyWithContainers" -}}
{{- printf "%s,edp-backend,edp-celery,edp-dataprep,edp-dpguard,edp-embedding,edp-flower,edp-ingestion,edp-vllm,edp-minio,edp-postgresql-0,edp-redis-master-0" .Values.proxy.noProxy }}
{{- end }}

{{- define "helm-edp.awsSqs.name" -}}
{{- default .Chart.Name .Values.awsSqs.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "helm-edp.fullname" -}}
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
{{- define "helm-edp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "helm-edp.labels" -}}
helm-edp.sh/chart: {{ include "helm-edp.chart" . }}
{{ include "helm-edp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "helm-edp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
celery labels
*/}}
{{- define "helm-edp.celery.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.celery.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
flower labels
*/}}
{{- define "helm-edp.flower.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.flower.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
backend labels
*/}}
{{- define "helm-edp.backend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.backend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
dpguard labels
*/}}
{{- define "helm-edp.dpguard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.dpguard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
embedding labels
*/}}
{{- define "helm-edp.embedding.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.embedding.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
ingestion labels
*/}}
{{- define "helm-edp.ingestion.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.ingestion.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
vllm labels
*/}}
{{- define "helm-edp.vllm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.vllm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
dataprep labels
*/}}
{{- define "helm-edp.dataprep.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.dataprep.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
awsSqs labels
*/}}
{{- define "helm-edp.awsSqs.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-edp.awsSqs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Create the name of the service account to use
*/}}
{{- define "helm-edp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "helm-edp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

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
