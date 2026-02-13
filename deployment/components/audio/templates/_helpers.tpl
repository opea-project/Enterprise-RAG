# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

{{/*
Expand the name of the chart.
*/}}
{{- define "audio.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "audio.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels for audio chart
*/}}
{{- define "audio.labels" -}}
helm.sh/chart: {{ include "audio.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ .Chart.Name }}
{{- end }}

{{/*
ASR component helpers
*/}}
{{- define "audio.asr.fullname" -}}
{{- .Values.asr.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.asr.name" -}}
{{- .Values.asr.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.asr.selectorLabels" -}}
app.kubernetes.io/name: {{ include "audio.asr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: asr
{{- end }}

{{- define "audio.asr.labels" -}}
{{ include "audio.labels" . }}
{{ include "audio.asr.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
{{- end }}

{{/*
vLLM ASR CPU component helpers
*/}}
{{- define "audio.vllmAudioCpu.fullname" -}}
{{- .Values.vllmAudioCpu.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.vllmAudioCpu.name" -}}
{{- .Values.vllmAudioCpu.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.vllmAudioCpu.selectorLabels" -}}
app.kubernetes.io/name: {{ include "audio.vllmAudioCpu.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: vllm-asr-cpu
{{- end }}

{{- define "audio.vllmAudioCpu.labels" -}}
{{ include "audio.labels" . }}
{{ include "audio.vllmAudioCpu.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
{{- end }}

{{/*
TTS component helpers
*/}}
{{- define "audio.tts.fullname" -}}
{{- .Values.tts.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.tts.name" -}}
{{- .Values.tts.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.tts.selectorLabels" -}}
app.kubernetes.io/name: {{ include "audio.tts.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: tts
{{- end }}

{{- define "audio.tts.labels" -}}
{{ include "audio.labels" . }}
{{ include "audio.tts.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
{{- end }}

{{/*
FastAPI TTS Model Server component helpers
*/}}
{{- define "audio.ttsFastapiModelServer.fullname" -}}
{{- .Values.ttsFastapiModelServer.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.ttsFastapiModelServer.name" -}}
{{- .Values.ttsFastapiModelServer.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "audio.ttsFastapiModelServer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "audio.ttsFastapiModelServer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: tts-fastapi-model-server
{{- end }}

{{- define "audio.ttsFastapiModelServer.labels" -}}
{{ include "audio.labels" . }}
{{ include "audio.ttsFastapiModelServer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
{{- end }}
