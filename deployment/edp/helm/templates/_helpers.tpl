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
Create the name of the service account to use
*/}}
{{- define "helm-edp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "helm-edp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
