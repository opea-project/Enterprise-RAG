{{/*
Common labels
*/}}
{{- define "fingerprint.labels" -}}
helm.sh/chart: {{ include "fingerprint.chart" . }}
{{ include "fingerprint.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "fingerprint.selectorLabels" -}}
app.kubernetes.io/name: {{ include "fingerprint.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "fingerprint.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "fingerprint.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "fingerprint.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Commonly used name templates
*/}}
{{- define "fingerprint.name" -}}
{{- default .Chart.Name .Values.nameOverride }}
{{- end }}

{{- define "fingerprint.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "fingerprint.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}