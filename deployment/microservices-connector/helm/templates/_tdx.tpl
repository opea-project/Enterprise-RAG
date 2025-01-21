{{/*
Annotations for the TDX deployment
*/}}
{{- define "manifest.tdx.annotations" }}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
{{- if $context.Values.tdx }}
{{- $tdx := $context.Values.tdx }}
{{- range $service := $tdx.services | default (list) }}
  {{- if and (eq $service.name $deploymentName) (eq $service.tdxEnabled true) }}
annotations:
  {{- range $key, $value := $tdx.common.annotations }}
  {{ $key }}: {{ tpl $value $context | quote | trim }}
  {{- end }}
  {{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
runtime class for the TDX deployment
*/}}
{{- define "manifest.tdx.runtimeClassName" }}
{{- $deploymentName := index . 0 -}}
{{- $context := index . 1 -}}
{{- if $context.Values.tdx }}
{{- $tdx := $context.Values.tdx }}
{{- range $service := $tdx.services | default (list) }}
  {{- if and (eq $service.name $deploymentName) (eq $service.tdxEnabled true) }}
runtimeClassName: {{ $tdx.common.runtimeClassName | quote }}
  {{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Values for the TDX deployment
*/}}
{{- define "manifest.tdx.values" }}
{{- $default := .default }}
{{- if .Values.tdx }}
{{- $deploymentName := .name }}
{{- $valueType := .type }}
{{- $tdx := .Values.tdx }}
{{- $serviceFound := false }}
{{- range $service := $tdx.services | default (list) }}
  {{- if eq $service.name $deploymentName }}
    {{- $serviceFound = true }}
    {{- if eq $service.tdxEnabled true }}
      {{- if eq $valueType "startupProbe.failureThreshold" }}
        {{- include "compareValues" (dict "default" $default "value" ($service.startupProbe.failureThreshold | default 0)) }}
      {{- else if eq $valueType "resources.limits.memory" }}
        {{- include "compareMemory" (dict "default" $default "value" ($service.resources.limits.memory | default "2Gi")) }}
      {{- else if eq $valueType "resources.limits.cpu" }}
        {{- include "compareCPU" (dict "default" $default "value" ($service.resources.limits.cpu | default "1")) }}
      {{- else if eq $valueType "resources.requests.memory" }}
        {{- include "compareMemory" (dict "default" $default "value" ($service.resources.requests.memory | default "2Gi")) }}
      {{- else if eq $valueType "resources.requests.cpu" }}
        {{- include "compareCPU" (dict "default" $default "value" ($service.resources.requests.cpu | default "1")) }}
      {{- end }}
    {{- else }}
      {{- $default }}
    {{- end }}
  {{- end }}
{{- end }}
{{- if not $serviceFound }}
  {{- $default }}
{{- end }}
{{- else }}
  {{- $default }}
{{- end }}
{{- end }}

{{/*
Custom comparison function for memory values
*/}}
{{- define "compareMemory" }}
{{- $default := .default }}
{{- $value := .value }}
{{- $defaultBytes := include "convertToBytes" $default | int }}
{{- $valueBytes := include "convertToBytes" $value | int }}
{{- if gt $valueBytes $defaultBytes }}
  {{ $value | quote }}
{{- else }}
  {{ $default | quote }}
{{- end }}
{{- end }}

{{/*
Custom comparison function for CPU values
*/}}
{{- define "compareCPU" }}
{{- $default := .default }}
{{- $value := .value }}
{{- $defaultMillis := include "convertToMillis" $default | int }}
{{- $valueMillis := include "convertToMillis" $value | int }}
{{- if gt $valueMillis $defaultMillis }}
  {{ $value | quote }}
{{- else }}
  {{ $default | quote }}
{{- end }}
{{- end }}

{{/*
Custom comparison function for integer values
*/}}
{{- define "compareValues" }}
{{- $default := .default | int }}
{{- $value := .value | int }}
{{- if gt $value $default }}
  {{ $value }}
{{- else }}
  {{ $default }}
{{- end }}
{{- end }}

{{/*
Convert memory value to bytes
*/}}
{{- define "convertToBytes" }}
{{- $value := . }}
{{- $valueStr := printf "%v" $value }}
{{- $number := regexReplaceAll "([0-9]+)([KMGi]*)" $valueStr "${1}" | int }}
{{- $unit := regexReplaceAll "([0-9]+)([KMGi]*)" $valueStr "${2}" }}
{{- $factor := 1 }}
{{- if eq $unit "Gi" }}
  {{- $factor = 1073741824 }}
{{- else if eq $unit "Mi" }}
  {{- $factor = 1048576 }}
{{- else if eq $unit "Ki" }}
  {{- $factor = 1024 }}
{{- else if eq $unit "G" }}
  {{- $factor = 1000000000 }}
{{- else if eq $unit "M" }}
  {{- $factor = 1000000 }}
{{- else if eq $unit "K" }}
  {{- $factor = 1000 }}
{{- end }}
{{- $result := mul $number $factor }}
{{- $result }}
{{- end }}

{{/*
Convert CPU value to millis
*/}}
{{- define "convertToMillis" }}
{{- $value := . }}
{{- $valueStr := printf "%v" $value }}
{{- $number := regexReplaceAll "([0-9]+)(m*)" $valueStr "${1}" | int }}
{{- $unit := regexReplaceAll "([0-9]+)(m*)" $valueStr "${2}" }}
{{- $factor := 1 }}
{{- if eq $unit "m" }}
  {{- $factor = 1 }}
{{- else }}
  {{- $factor = 1000 }}
{{- end }}
{{- $result := mul $number $factor }}
{{- $result }}
{{- end }}
