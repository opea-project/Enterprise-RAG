{{/*
Expand the name of the chart.
*/}}
{{- define "helm-ui.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "helm-ui.fullname" -}}
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
{{- define "helm-ui.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "helm-ui.labels" -}}
helm.sh/chart: {{ include "helm-ui.chart" . }}
{{ include "helm-ui.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "helm-ui.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helm-ui.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "helm-ui.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "helm-ui.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generic pod label definition
*/}}
{{- define "manifest.podLabels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
labels:
  {{- include "helm-ui.selectorLabels" $context | nindent 2 }}
{{- if $context.Values.tdx }}
  {{- include "manifest.tdx.labels" (list $deploymentName $context) | nindent 2 }}
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
