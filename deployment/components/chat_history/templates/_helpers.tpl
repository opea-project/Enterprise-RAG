{{/*
Common labels
*/}}
{{- define "chat-history.labels" -}}
helm.sh/chart: {{ include "chat-history.chart" . }}
{{ include "chat-history.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "chat-history.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chat-history.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "chat-history.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "chat-history.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "chat-history.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Commonly used name templates
*/}}
{{- define "chat-history.name" -}}
{{- default .Chart.Name .Values.nameOverride }}
{{- end }}

{{- define "chat-history.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "chat-history.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Generic pod label definition
*/}}
{{- define "manifest.podLabels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
labels:
  {{- include "chat-history.selectorLabels" $context | nindent 2 }}
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
{{- else if and $values.minimalConfiguration (index $values "minimalResources" $filename) }}
  {{- $minimalCpu := index $values "minimalResources" $filename "requests" "cpu" }}
  {{- $defaultValues = mergeOverwrite $defaultValues (dict "requests" (dict "cpu" $minimalCpu)) }}
{{- end -}}

{{- $defaultValues | toYaml }}
{{- end -}}
