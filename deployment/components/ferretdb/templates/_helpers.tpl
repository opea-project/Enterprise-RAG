{{- define "ferretdb.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ferretdb.fullname" -}}
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
{{- define "ferretdb.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ferretdb.labels" -}}
helm.sh/chart: {{ include "ferretdb.chart" . }}
{{ include "ferretdb.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ferretdb.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ferretdb.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "ferretdb.postgresql.labels" -}}
helm.sh/chart: {{ include "ferretdb.chart" . }}
{{ include "ferretdb.postgresql.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: postgresql
{{- end }}

{{/*
PostgreSQL selector labels
*/}}
{{- define "ferretdb.postgresql.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ferretdb.name" . }}-postgresql
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Check if chart is only used as dependency, as it's not a standalone component
*/}}
{{- define "ferretdb.verifyIsDependency" -}}
{{- $dependencyOnly := eq (index .Chart.Annotations "dependency-only" | default "false") "true" }}
{{- $hasParentDefined := and .Values.global ( hasKey .Values.global "parentChartDefined" ) ( eq ( index .Values.global "parentChartDefined" | default false ) true ) }}
{{- if $dependencyOnly }}
    {{- if not $hasParentDefined }}
        {{- fail ( printf "Chart '%s' is marked as 'dependency-only: true'. Use it as dependency or otherwise refactor and include it in versioned components." .Chart.Name ) }}
    {{- end }}
{{- end }}
{{- end }}
