{{/*
Common labels
*/}}
{{- define "rag-utils.labels" -}}
helm.sh/chart: {{ include "rag-utils.chart" . }}
{{ include "rag-utils.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "rag-utils.selectorLabels" -}}
app.kubernetes.io/name: {{ include "rag-utils.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "rag-utils.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "rag-utils.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "rag-utils.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Commonly used name templates
*/}}
{{- define "rag-utils.name" -}}
{{- default .Chart.Name .Values.nameOverride }}
{{- end }}

{{- define "rag-utils.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride }}
{{- else }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Generic pod label definition
*/}}
{{- define "manifest.podLabels" -}}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
labels:
  {{- include "rag-utils.selectorLabels" $context | nindent 2 }}
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

{{/*
Create namespace
*/}}
{{- define "rag-utils.namespace" -}}
{{- .Release.Namespace }}
{{- end }}

{{/*
Generate image reference with support for alternate tagging
Usage: {{ include "rag-utils.image" (list "init-container" .) }}
*/}}
{{- define "rag-utils.image" -}}
{{- $filename := index . 0 -}}
{{- $context := index . 1 -}}
{{- $imageConfig := index $context.Values.images $filename -}}
{{- $alternateTagging := $context.Values.alternateTagging -}}
{{- if $alternateTagging -}}
{{- printf "%s:%s_%s" $imageConfig.repository $imageConfig.image $imageConfig.tag -}}
{{- else -}}
{{- printf "%s/%s:%s" $imageConfig.repository $imageConfig.image $imageConfig.tag -}}
{{- end -}}
{{- end -}}

{{/*
Validate namespace is default
*/}}
{{- define "rag-utils.validateNamespace" -}}
{{- if ne .Release.Namespace "default" -}}
{{- fail "rag-utils must be deployed in the 'default' namespace" -}}
{{- end -}}
{{- end -}}
