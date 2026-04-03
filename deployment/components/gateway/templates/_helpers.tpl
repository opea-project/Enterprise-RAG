{{- /*
Copyright (C) 2024-2026 Intel Corporation
SPDX-License-Identifier: Apache-2.0
*/ -}}

{{- define "erag-gateway.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ERAG
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
