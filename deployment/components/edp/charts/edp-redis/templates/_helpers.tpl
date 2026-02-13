{{- define "edp-redis.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "edp-redis.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Check if chart is only used as dependency, as it's not a standalone component
*/}}
{{- define "edp-redis.verifyIsDependency" -}}
{{- $dependencyOnly := eq (index .Chart.Annotations "dependency-only" | default "false") "true" }}
{{- $hasParentDefined := and .Values.global ( hasKey .Values.global "parentChartDefined" ) ( eq ( index .Values.global "parentChartDefined" | default false ) true ) }}
{{- if $dependencyOnly }}
    {{- if not $hasParentDefined }}
        {{- fail ( printf "Chart '%s' is marked as 'dependency-only: true'. Use it as dependency or otherwise refactor and include it in versioned components." .Chart.Name ) }}
    {{- end }}
{{- end }}
{{- end }}
