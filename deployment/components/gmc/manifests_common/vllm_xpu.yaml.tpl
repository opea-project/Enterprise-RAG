---
# Source: vllm/templates/configmap.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
{{- if (.Values.is_bmg_platform_enable | default (.Values.is_bmg_platform | default false)) }}
{{- $modelName := required "Please specify a valid llm_model_xpu (or llm_model) name in your Helm chart values" (coalesce .Values.llm_model_xpu .Values.llm_model) }}
{{- $defaultModelConfigs := (index .Values "defaultModelConfigs" | default dict) }}
{{- $modelChatTemplate := (index (default dict .Values.modelConfigs) $modelName).modelChatTemplate | default $defaultModelConfigs.modelChatTemplate }}
{{- $port := "8000" }}
{{- $vllmReplicas := include "getReplicas" (list .filename .Values) | trim -}}
{{- /*
    Compute memory request and limit from model configuration:
      - VLLM_CPU_KVCACHE_SPACE (Gi) is read from the model's configMapValues (default: 10)
      - Base memory: 16 Gi for AWQ-quantized models, 32 Gi for all others
      - Memory request  = base + kvcache
      - Memory limit    = 2 × request
*/ -}}
{{- $configMapValues := (index (default dict .Values.modelConfigs) $modelName).configMapValues | default $defaultModelConfigs.configMapValues -}}
{{- $modelExtraArgs := (index (default dict .Values.modelConfigs) $modelName).extraCmdArgs | default $defaultModelConfigs.extraCmdArgs | default list -}}
{{- $isAwq := has "awq" $modelExtraArgs -}}
{{- $kvCacheGi := int (index ($configMapValues | default dict) "VLLM_CPU_KVCACHE_SPACE" | default "10") -}}
{{- $baseMemGi := ternary 16 32 $isAwq -}}
{{- $memRequestGi := add $baseMemGi $kvCacheGi -}}
{{- $memLimitGi := mul 2 $memRequestGi }}

apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-config
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
  {{- include "manifest.addEnvsAndEnvFile" (list .filename .) | nindent 2 }}
  {{- if $configMapValues }}
    {{- range $key, $value := $configMapValues }}
      {{- printf "%s: %s" $key ($value | quote) | nindent 2 }}
    {{- end }}
  {{- end }}
  LLM_DEVICE: "xpu"
  VLLM_DEVICE: "xpu"
  VLLM_TARGET_DEVICE: "xpu"
  PORT: {{ $port | quote }}
  http_proxy: {{ .Values.proxy.httpProxy | quote }}
  https_proxy: {{ .Values.proxy.httpsProxy | quote }}
  no_proxy: {{ .Values.proxy.noProxy | quote }}
---
{{- if $modelChatTemplate }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-chat-template
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
   chat_template.jinja: |
{{ $modelChatTemplate | indent 4 }}
{{- end }}
---
{{- if not .Values.balloons.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-assign-cores
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
data:
   assign_cores.sh: |
{{ (.Files.Get "envs/src/comps/llms/impl/model_server/vllm/docker/assign_cores.sh" | indent 4) }}
{{- end }}
---
{{- range .Values.vllmNodes }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ $.Values.pvc.modelLlm.name }}-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
spec:
  accessModes:
    - {{ $.Values.pvc.modelLlm.accessMode }}
  resources:
    requests:
      storage: {{ $.Values.pvc.modelLlm.storage }}
{{- end }}
---
# Source: vllm/templates/service.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apiVersion: v1
kind: Service
metadata:
  name: vllm-xpu-svc
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: {{ $port }}
      targetPort: 8000
      protocol: TCP
      name: vllm
  selector:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 4 }}
---
{{- if and $.Values.vllmNodes $.Values.balloons.enabled }}
{{- range .Values.vllmNodes }}
# Source: vllm/templates/deployment.yaml
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: vllm-service-m-{{ .name }}
  labels:
    {{- include "manifest.labels" (list $.filename $) | nindent 4 }}
    vllm-node: {{ .name }}
spec:
  serviceName: "vllm-service-m"
  replicas: {{ .VLLM_INSTANCES | default 1 }}
  selector:
    matchLabels:
      {{- include "manifest.selectorLabels" (list $.filename $) | nindent 6 }}
      vllm-node: {{ .name }}
  template:
    metadata:
      labels:
        {{- include "manifest.selectorLabels" (list $.filename $) | nindent 8 }}
        vllm-node: {{ .name }}
    spec:
      nodeSelector:
        {{- toYaml .nodeSelector | nindent 8 }}
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: kubernetes.io/hostname
                    operator: In
                    values:
                      - {{ .name }}
      tolerations:
        - key: "inference_eligible_vllm"
          operator: "Equal"
          value: "true"
          effect: "PreferNoSchedule"
      initContainers:
        {{- include "manifest.balloons.initContainer" $ | nindent 8 }}
      securityContext:
        {{- toYaml $.Values.podSecurityContext | nindent 8 }}
        supplementalGroups: [991]
      {{- include "gmc.imagePullSecrets" $ }}
      containers:
        - name: vllm
          envFrom:
            - configMapRef:
                name: vllm-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: HF_HOME
              value: /tmp/.cache
            - name: USER
              value: user
            {{- if $.Values.tokens.hugToken }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token-secret
                  key: HF_TOKEN
            {{- end }}
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
            - name: VLLM_POD_INDEX
              valueFrom:
                fieldRef:
                  fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
          securityContext:
            {{- toYaml $.Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list $.filename $.Values) }}
          imagePullPolicy: {{ toYaml (index $.Values "images" $.filename "pullPolicy" | default "Always") }}
          {{- $modelArgs := (index (default dict $.Values.modelConfigs) $modelName).extraCmdArgs | default $defaultModelConfigs.extraCmdArgs }}
          {{- if $modelArgs }}
          {{- $cmd := concat (list "python3" "-m" "vllm.entrypoints.openai.api_server") $modelArgs (list "--model" $modelName "--allow-deprecated-quantization" "--enforce-eager" "--port" $port) }}
          {{- if $modelChatTemplate }}
            {{- $cmd = concat $cmd (list "--chat-template" "/etc/vllm/chat_template.jinja") }}
          {{- end }}
          command:
            - bash
            - -c
            - |
                {{- if $.Values.balloons.enabled }}
                export VLLM_CPU_OMP_THREADS_BIND=$(tr ' ' ',' < /sys/fs/cgroup/cpuset.cpus.effective)
                {{- end }}
                {{ join " " $cmd }}
          {{- else }}
          command:
            - bash
            - -c
            - |
                {{- if $.Values.balloons.enabled }}
                export VLLM_CPU_OMP_THREADS_BIND=$(tr ' ' ',' < /sys/fs/cgroup/cpuset.cpus.effective)
                {{- end }}
                python3 -m "vllm.entrypoints.openai.api_server" --model $LLM_VLLM_MODEL_NAME --allow-deprecated-quantization --enforce-eager --tensor-parallel-size $VLLM_TP_SIZE --pipeline-parallel-size $VLLM_PP_SIZE --dtype $VLLM_DTYPE --max_model_len $VLLM_MAX_MODEL_LEN --max-num-seqs $VLLM_MAX_NUM_SEQS --disable-log-requests --download-dir "/data"{{- if $modelChatTemplate }} --chat-template /etc/vllm/chat_template.jinja{{- end }}
          {{- end }}
          volumeMounts:
            - mountPath: /data
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /dev/shm
              name: shm
            - mountPath: /home/user/.cache
              name: cache
            - mountPath: /home/user/.config
              name: config
            {{- if $modelChatTemplate }}
            - mountPath: /etc/vllm
              name: chat-template-volume
            {{- end }}
            {{- if not $.Values.balloons.enabled }}
            - mountPath: /etc/helpers
              name: assign-cores-volume
            {{- end }}
          ports:
            - name: http
              containerPort: {{ $port }}
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          readinessProbe:
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          startupProbe:
            failureThreshold: 120
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          resources:
            limits:
              memory: {{ printf "%dGi" $memLimitGi }}
              cpu: {{ .VLLM_CPU | default "2" }}
              gpu.intel.com/xe: 1
            requests:
              memory: {{ printf "%dGi" $memRequestGi }}
              cpu: {{ .VLLM_CPU | default "4" }}
              gpu.intel.com/xe: 1
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ $.Values.pvc.modelLlm.name }}-{{ .name }}
        - name: tmp
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 4Gi
        - name: cache
          emptyDir: {}
        - name: config
          emptyDir: {}
        {{- if $modelChatTemplate }}
        - name: chat-template-volume
          configMap:
            name: vllm-chat-template
        {{- end }}
        {{- if not $.Values.balloons.enabled }}
        - name: assign-cores-volume
          configMap:
            name: vllm-assign-cores
        {{- end }}
---
{{- end }}
{{- else }}
{{- if ne $vllmReplicas "0" }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Values.pvc.modelLlm.name }}
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  accessModes:
    - {{ .Values.pvc.modelLlm.accessMode }}
  resources:
    requests:
      storage: {{ .Values.pvc.modelLlm.storage }}
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: vllm-service-m-deployment
  labels:
    {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  serviceName: "vllm-service-m"
  replicas: {{ $vllmReplicas | default 1 }}
  selector:
    matchLabels:
    {{- include "manifest.selectorLabels" (list .filename .) | nindent 6 }}
  template:
    metadata:
      {{- include "manifest.podLabels" (list .filename .) | nindent 6 }}
    spec:
      affinity:
        nodeAffinity:
          {{- if .Values.balloons.enabled }}
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: inference-eligible-vllm
                    operator: In
                    values:
                      - "true"
          {{- else }}
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: inference-eligible-vllm
                    operator: In
                    values:
                      - "true"
          {{- end }}
      tolerations:
        - key: "inference_eligible_vllm"
          operator: "Equal"
          value: "true"
          effect: "PreferNoSchedule"
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
        supplementalGroups: [991]
      {{- include "gmc.imagePullSecrets" . }}
      containers:
        - name: vllm
          envFrom:
            - configMapRef:
                name: vllm-config
            - configMapRef:
                name: extra-env-config
                optional: true
          env:
            - name: HF_HOME
              value: /tmp/.cache
            - name: USER
              value: user
            {{- if .Values.tokens.hugToken }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token-secret
                  key: HF_TOKEN
            {{- end }}
            - name: OMP_NUM_THREADS
              valueFrom:
                resourceFieldRef:
                  resource: limits.cpu
            - name: VLLM_POD_INDEX
              valueFrom:
                fieldRef:
                  fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: {{ include "manifest.image" (list .filename .Values) }}
          imagePullPolicy: {{ toYaml (index .Values "images" .filename "pullPolicy" | default "Always") }}
          {{- $modelArgs := (index (default dict .Values.modelConfigs) $modelName).extraCmdArgs | default $defaultModelConfigs.extraCmdArgs }}
          {{- if $modelArgs }}
          {{- $cmd := concat (list "python3" "-m" "vllm.entrypoints.openai.api_server") $modelArgs (list "--model" $modelName "--allow-deprecated-quantization" "--enforce-eager" "--port" $port) }}
          {{- if $modelChatTemplate }}
            {{- $cmd = concat $cmd (list "--chat-template" "/etc/vllm/chat_template.jinja") }}
          {{- end }}
          command:
            - bash
            - -c
            - |
                {{- if .Values.balloons.enabled }}
                export VLLM_CPU_OMP_THREADS_BIND=$(tr ' ' ',' < /sys/fs/cgroup/cpuset.cpus.effective)
                {{- end }}
                {{ join " " $cmd }}
          {{- else }}
          command:
            - bash
            - -c
            - |
                {{- if .Values.balloons.enabled }}
                export VLLM_CPU_OMP_THREADS_BIND=$(tr ' ' ',' < /sys/fs/cgroup/cpuset.cpus.effective)
                {{- end }}
                python3 -m "vllm.entrypoints.openai.api_server" --model $LLM_VLLM_MODEL_NAME --allow-deprecated-quantization --enforce-eager --tensor-parallel-size $VLLM_TP_SIZE --pipeline-parallel-size $VLLM_PP_SIZE --dtype $VLLM_DTYPE --max_model_len $VLLM_MAX_MODEL_LEN --max-num-seqs $VLLM_MAX_NUM_SEQS --disable-log-requests --download-dir "/data"{{- if $modelChatTemplate }} --chat-template /etc/vllm/chat_template.jinja{{- end }}
          {{- end }}
          volumeMounts:
            - mountPath: /data
              name: model-volume
            - mountPath: /tmp
              name: tmp
            - mountPath: /dev/shm
              name: shm
            - mountPath: /home/user/.cache
              name: cache
            - mountPath: /home/user/.config
              name: config
            {{- if $modelChatTemplate }}
            - mountPath: /etc/vllm
              name: chat-template-volume
            {{- end }}
            {{- if not .Values.balloons.enabled }}
            - mountPath: /etc/helpers
              name: assign-cores-volume
            {{- end }}
          ports:
            - name: http
              containerPort: {{ $port }}
              protocol: TCP
          livenessProbe:
            failureThreshold: 24
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          readinessProbe:
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          startupProbe:
            failureThreshold: 120
            initialDelaySeconds: 30
            periodSeconds: 60
            httpGet:
              path: /health
              port: http
          resources:
            {{- $vllmRes := dict -}}
            {{- if and .Values.services (index .Values.services .filename) (index .Values.services .filename "resources") -}}
              {{- $vllmRes = index .Values.services .filename "resources" -}}
            {{- end -}}
            {{- $vllmResReqs := index ($vllmRes | default dict) "requests" | default dict -}}
            {{- $vllmResLims := index ($vllmRes | default dict) "limits" | default dict -}}
            {{- $cpuReq := index $vllmResReqs "cpu" | default "4" -}}
            {{- $cpuLim := index $vllmResLims "cpu" | default "4" }}
            {{- $memReq := index $vllmResReqs "memory" | default (printf "%dGi" $memRequestGi) -}}
            {{- $memLim := index $vllmResLims "memory" | default (printf "%dGi" $memLimitGi) }}
            requests:
              cpu: {{ $cpuReq }}
              memory: {{ $memReq }}
              gpu.intel.com/xe: 1
            limits:
              cpu: {{ $cpuLim }}
              memory: {{ $memLim }}
              gpu.intel.com/xe: 1
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: {{ .Values.pvc.modelLlm.name }}
        - name: tmp
          emptyDir: {}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 12Gi
        - name: cache
          emptyDir: {}
        - name: config
          emptyDir: {}
        {{- if $modelChatTemplate }}
        - name: chat-template-volume
          configMap:
            name: vllm-chat-template
        {{- end }}
        {{- if not .Values.balloons.enabled }}
        - name: assign-cores-volume
          configMap:
            name: vllm-assign-cores
        {{- end }}
---
{{- end }}
{{- end }}

{{- if and .Values.hpaEnabled (not .Values.balloons.enabled) (ne $vllmReplicas "0") }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm
  labels:
  {{- include "manifest.labels" (list .filename .) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: vllm-service-m-deployment
  minReplicas: {{ ( ((index .Values "services" .filename).hpa).minReplicas | default 1) }}
  maxReplicas: {{ ( ((index .Values "services" .filename).hpa).maxReplicas | default 4) }}
  metrics:
  - type: Object
    object:
      metric:
        # vLLM time metrics are in seconds
        name: vllm_token_latency
      describedObject:
        apiVersion: v1
        # get metric for named object of given type (in same namespace)
        kind: Service
        name: vllm-service-m
      target:
        # vllm_token_latency is average for all the vLLM pods. To avoid replica fluctuations when
        # vLLM startup + request processing takes longer than HPA evaluation period, this uses
        # "Value" (replicas = metric.value / target.value), instead of "averageValue" type:
        #  https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#algorithm-details
        type: Value
        value: {{ ( ((index .Values "services" .filename).hpa).targetValue | default "150m") }}
  {{- $hpaBehavior := ( ((index .Values "services" .filename).hpa).behavior) }}
  {{- if $hpaBehavior }}
  behavior:
    {{- toYaml $hpaBehavior | nindent 4 }}
  {{- else }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 180
      policies:
      - type: Percent
        value: 25
        periodSeconds: 90
    scaleUp:
      selectPolicy: Max
      stabilizationWindowSeconds: 0
      policies:
      - type: Pods
        value: 1
        periodSeconds: 90
  {{- end }}
{{- end }}
{{- end }}
