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

{{/*
Generic pod label definition
*/}}
{{- define "manifest.podLabels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
labels:
  {{- include "fingerprint.selectorLabels" $context | nindent 2 }}
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