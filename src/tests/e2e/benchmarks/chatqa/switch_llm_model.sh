#!/bin/bash
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Switch the LLM model used by ERAG's chatqa pipeline.
#
# This script:
#   1. Patches the gmc-config ConfigMap in the 'system' namespace
#      (updates LLM_VLLM_MODEL_NAME in vllm.yaml and LLM_MODEL_NAME in llm-usvc.yaml)
#   2. Re-applies the pipeline GMConnector YAML to trigger GMC reconciliation
#      (GMC controller detects the ConfigMap change and automatically recreates pods)
#   3. Waits for vLLM pods to become ready
#
# Usage:
#   ./switch_llm_model.sh <model_name> [--dry-run]
#
# Examples:
#   ./switch_llm_model.sh "meta-llama/Llama-3.1-8B-Instruct"
#   ./switch_llm_model.sh "casperhansen/llama-3-8b-instruct-awq" --dry-run
#
# Environment variables:
#   HF_TOKEN  – If set, creates/updates the hf-token-secret in the pipeline namespace.
#               Required when switching to a gated model (e.g. meta-llama/*).

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────
GMC_NAMESPACE="system"
PIPELINE_NAMESPACE="chatqa"
TIMEOUT=600
DRY_RUN=0
MODEL_NAME=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Colours & logging
# ─────────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[0;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${RESET}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_error() { echo -e "${RED}[ERROR]${RESET} $*" >&2; }

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1; shift ;;
        -h|--help)
            head -20 "${BASH_SOURCE[0]}" | grep '^#' | sed 's/^# \?//'
            exit 0 ;;
        -*)
            log_error "Unknown option: $1"; exit 1 ;;
        *)
            if [[ -z "$MODEL_NAME" ]]; then
                MODEL_NAME="$1"; shift
            else
                log_error "Unexpected argument: $1"; exit 1
            fi ;;
    esac
done

if [[ -z "$MODEL_NAME" ]]; then
    log_error "Usage: $0 <model_name> [options]"
    log_error "Example: $0 \"meta-llama/Llama-3.1-8B-Instruct\""
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Ensure HF token secret exists (if HF_TOKEN env var is set)
# ─────────────────────────────────────────────────────────────────────────────
ensure_hf_token() {
    if [[ -z "${HF_TOKEN:-}" ]]; then
        return
    fi

    log_info "HF_TOKEN set — creating/updating hf-token-secret in '${PIPELINE_NAMESPACE}' namespace …"

    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would create/update hf-token-secret"
        return
    fi

    kubectl create secret generic hf-token-secret \
        -n "${PIPELINE_NAMESPACE}" \
        --from-literal=HF_TOKEN="${HF_TOKEN}" \
        --dry-run=client -o yaml | kubectl apply -f -

    log_ok "hf-token-secret updated."
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Patch gmc-config ConfigMap — update vllm.yaml (LLM_VLLM_MODEL_NAME)
# ─────────────────────────────────────────────────────────────────────────────
patch_gmc_config() {
    log_info "Patching gmc-config ConfigMap in '${GMC_NAMESPACE}' namespace …"
    log_info "  New model: ${MODEL_NAME}"

    # Extract current vllm.yaml content from gmc-config
    local vllm_yaml
    vllm_yaml=$(kubectl get configmap gmc-config -n "${GMC_NAMESPACE}" -o jsonpath='{.data.vllm\.yaml}')
    if [[ -z "$vllm_yaml" ]]; then
        log_error "Could not read 'vllm.yaml' key from gmc-config ConfigMap."
        exit 1
    fi

    # Replace LLM_VLLM_MODEL_NAME value in ConfigMap data
    local new_vllm_yaml
    new_vllm_yaml=$(echo "$vllm_yaml" | sed -E "s|(LLM_VLLM_MODEL_NAME: \")([^\"]+)(\")|\1${MODEL_NAME}\3|g")

    # Also replace --model <name> in the container command (Helm bakes it in at render time)
    new_vllm_yaml=$(echo "$new_vllm_yaml" | sed -E "s|(--model )[^ \"]+|\1${MODEL_NAME}|g")

    # Extract current llm-usvc.yaml content from gmc-config
    local llm_usvc_yaml
    llm_usvc_yaml=$(kubectl get configmap gmc-config -n "${GMC_NAMESPACE}" -o jsonpath='{.data.llm-usvc\.yaml}')
    if [[ -z "$llm_usvc_yaml" ]]; then
        log_error "Could not read 'llm-usvc.yaml' key from gmc-config ConfigMap."
        exit 1
    fi

    # Replace LLM_MODEL_NAME value
    local new_llm_usvc_yaml
    new_llm_usvc_yaml=$(echo "$llm_usvc_yaml" | sed -E "s|(LLM_MODEL_NAME: \")([^\"]+)(\")|\1${MODEL_NAME}\3|g")

    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would patch gmc-config:"
        log_info "  vllm.yaml: LLM_VLLM_MODEL_NAME → ${MODEL_NAME}"
        log_info "  llm-usvc.yaml: LLM_MODEL_NAME → ${MODEL_NAME}"
        return
    fi

    # Apply patches using kubectl patch with strategic merge
    # We use a temp file to handle multi-line YAML content safely
    local patch_file
    patch_file=$(mktemp /tmp/gmc-config-patch-XXXXXX.json)
    trap "rm -f ${patch_file}" EXIT

    # Build JSON patch — properly escape the YAML content for JSON
    python3 -c "
import json, sys

vllm_yaml = sys.stdin.read()
" <<< "" > /dev/null  # just checking python3 is available

    # Use kubectl to apply the patch key-by-key
    kubectl get configmap gmc-config -n "${GMC_NAMESPACE}" -o json | \
        python3 -c "
import json, sys

cm = json.load(sys.stdin)
vllm_yaml = '''${new_vllm_yaml}'''
llm_usvc_yaml = '''${new_llm_usvc_yaml}'''
cm['data']['vllm.yaml'] = vllm_yaml
cm['data']['llm-usvc.yaml'] = llm_usvc_yaml
# Remove resourceVersion to avoid conflicts
cm['metadata'].pop('resourceVersion', None)
cm['metadata'].pop('uid', None)
cm['metadata'].pop('creationTimestamp', None)
json.dump(cm, sys.stdout)
" | kubectl apply -f - -n "${GMC_NAMESPACE}"

    log_ok "gmc-config ConfigMap patched successfully."
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Trigger GMC reconciliation
#         The ConfigMap changed but GMConnector spec didn't, so we need to
#         restart the GMC manager to pick up the new ConfigMap content.
# ─────────────────────────────────────────────────────────────────────────────
apply_pipeline() {
    log_info "Triggering GMC reconciliation …"

    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would restart gmc-controller to reconcile ConfigMap changes"
        return
    fi

    # Restart the GMC controller — it re-reads gmc-config on startup and reconciles all pipelines
    kubectl rollout restart deployment/gmc-controller -n "${GMC_NAMESPACE}"
    kubectl rollout status deployment/gmc-controller -n "${GMC_NAMESPACE}" --timeout=120s

    log_ok "GMC controller restarted — reconciling with new model config."

    # Give GMC time to start reconciling pods (it restarts vLLM, then llm-usvc, etc.)
    log_info "Waiting 15s for GMC to begin pod reconciliation …"
    sleep 15
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Wait for pods to be ready (GMC recreates them automatically)
# ─────────────────────────────────────────────────────────────────────────────
wait_for_ready() {
    log_info "Waiting up to ${TIMEOUT}s for vLLM pods to become ready …"

    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would wait for pods."
        return
    fi

    # First, wait for the rollout to complete — this ensures old pods are gone
    # and new pods are fully up (handles rolling update correctly)
    local vllm_resources
    vllm_resources=$(kubectl get deployments,statefulsets -n "${PIPELINE_NAMESPACE}" \
        -l "app.kubernetes.io/name=vllm" -o name 2>/dev/null || echo "")

    # Calculate timeout based on number of replicas (5 min per instance)
    local replicas
    replicas=$(kubectl get deployments,statefulsets -n "${PIPELINE_NAMESPACE}" \
        -l "app.kubernetes.io/name=vllm" -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "1")
    replicas=${replicas:-1}
    local rollout_timeout=$((replicas * 400))
    log_info "  Rollout: ${replicas} replica(s), timeout ${rollout_timeout}s (~7min × ${replicas})"

    if [[ -n "$vllm_resources" ]]; then
        local elapsed=0
        local poll_interval=15
        local prev_updated=0

        while [[ $elapsed -lt $rollout_timeout ]]; do
            # Get rollout status numbers from the statefulset/deployment
            local updated_replicas
            updated_replicas=$(kubectl get deployments,statefulsets -n "${PIPELINE_NAMESPACE}" \
                -l "app.kubernetes.io/name=vllm" \
                -o jsonpath='{.items[0].status.updatedReplicas}' 2>/dev/null || echo "0")
            updated_replicas=${updated_replicas:-0}

            local ready_replicas
            ready_replicas=$(kubectl get deployments,statefulsets -n "${PIPELINE_NAMESPACE}" \
                -l "app.kubernetes.io/name=vllm" \
                -o jsonpath='{.items[0].status.readyReplicas}' 2>/dev/null || echo "0")
            ready_replicas=${ready_replicas:-0}

            local current_replicas
            current_replicas=$(kubectl get deployments,statefulsets -n "${PIPELINE_NAMESPACE}" \
                -l "app.kubernetes.io/name=vllm" \
                -o jsonpath='{.items[0].status.currentReplicas}' 2>/dev/null || echo "0")
            current_replicas=${current_replicas:-0}

            # Log progress on change or periodically
            if [[ $updated_replicas -ne $prev_updated ]] || [[ $((elapsed % 30)) -eq 0 ]]; then
                log_info "  Rolling update: ${updated_replicas}/${replicas} updated, ${ready_replicas}/${replicas} ready (${elapsed}s elapsed)"
            fi
            prev_updated=$updated_replicas

            # Rollout is done when all replicas are updated and ready
            if [[ $updated_replicas -eq $replicas && $ready_replicas -eq $replicas && $current_replicas -eq $replicas ]]; then
                log_ok "Rollout complete: all ${replicas} replica(s) updated and ready after ${elapsed}s."
                break
            fi

            sleep $poll_interval
            elapsed=$((elapsed + poll_interval))
        done

        if [[ $elapsed -ge $rollout_timeout ]]; then
            log_warn "Rollout did not complete within ${rollout_timeout}s."
        fi
    fi

    # Then confirm all pods are Ready (belt-and-suspenders)
    local elapsed=0
    local poll_interval=15

    while [[ $elapsed -lt $TIMEOUT ]]; do
        local ready_count
        ready_count=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" \
            -l "app.kubernetes.io/name=vllm" \
            -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' 2>/dev/null \
            | grep -c "True" || true)

        local total_count
        total_count=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" \
            -l "app.kubernetes.io/name=vllm" --no-headers 2>/dev/null \
            | wc -l || echo "0")

        if [[ $total_count -gt 0 && $ready_count -eq $total_count ]]; then
            log_ok "All vLLM pods ready (${ready_count}/${total_count}) after rollout."
            log_info "Verifying model is actually serving …"
            return
        fi

        log_info "  Waiting … (${ready_count}/${total_count} ready, ${elapsed}s elapsed)"
        sleep $poll_interval
        elapsed=$((elapsed + poll_interval))
    done

    log_warn "Timeout after ${TIMEOUT}s. vLLM pods may still be starting."
    log_warn "Check status with: kubectl get pods -n ${PIPELINE_NAMESPACE} -l app.kubernetes.io/name=vllm"
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Verify model is loaded (polls until model responds on /v1/models)
# ─────────────────────────────────────────────────────────────────────────────
verify_model() {
    if [[ $DRY_RUN -eq 1 ]]; then
        return
    fi

    log_info "Waiting for model '${MODEL_NAME}' to be serving on all vLLM pods …"

    local verify_timeout=300
    local poll_interval=15
    local elapsed=0

    # Get all vLLM pod names
    local pods
    pods=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" \
        -l "app.kubernetes.io/name=vllm" \
        -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null)

    if [[ -z "$pods" ]]; then
        log_warn "No vLLM pods found — skipping verification."
        return
    fi

    local pod_count
    pod_count=$(echo "$pods" | wc -l)

    while [[ $elapsed -lt $verify_timeout ]]; do
        local serving_count=0

        while IFS= read -r pod; do
            local models_response
            models_response=$(kubectl exec -n "${PIPELINE_NAMESPACE}" "$pod" -- \
                curl -s --max-time 5 http://localhost:8000/v1/models 2>/dev/null || echo "")

            if echo "$models_response" | grep -q "$MODEL_NAME"; then
                serving_count=$((serving_count + 1))
            fi
        done <<< "$pods"

        if [[ $serving_count -eq $pod_count ]]; then
            log_ok "Model '${MODEL_NAME}' confirmed serving on all ${pod_count} vLLM pod(s) after ${elapsed}s."
            return
        fi

        log_info "  Model loading … (${serving_count}/${pod_count} serving, ${elapsed}s elapsed)"
        sleep $poll_interval
        elapsed=$((elapsed + poll_interval))
    done

    log_warn "Timeout after ${verify_timeout}s waiting for model to serve."
    log_warn "Check manually:"
    while IFS= read -r pod; do
        log_warn "  kubectl exec -n ${PIPELINE_NAMESPACE} ${pod} -- curl -s http://localhost:8000/v1/models"
    done <<< "$pods"
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Wait for ALL pods in the pipeline namespace to be ready
#         GMC may restart other services (llm-usvc, gateway, etc.)
# ─────────────────────────────────────────────────────────────────────────────
wait_all_pods_ready() {
    if [[ $DRY_RUN -eq 1 ]]; then
        return
    fi

    log_info "Waiting for all pods in '${PIPELINE_NAMESPACE}' namespace to stabilize …"

    local all_pods_timeout=300
    local poll_interval=15
    local elapsed=0

    while [[ $elapsed -lt $all_pods_timeout ]]; do
        # First check for terminating pods (have deletionTimestamp set)
        local terminating
        terminating=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" \
            -o jsonpath='{range .items[?(@.metadata.deletionTimestamp)]}{.metadata.name}{"\n"}{end}' 2>/dev/null | grep -c . || true)

        if [[ $terminating -gt 0 ]]; then
            log_info "  ${terminating} pod(s) still terminating … (${elapsed}s elapsed)"
            sleep $poll_interval
            elapsed=$((elapsed + poll_interval))
            continue
        fi

        # No terminating pods — now check all remaining are Ready
        local total_pods
        total_pods=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" --no-headers 2>/dev/null | wc -l || echo "0")

        local ready_pods
        ready_pods=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" \
            -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' 2>/dev/null \
            | grep -c "True" || true)

        local not_ready
        not_ready=$((total_pods - ready_pods))

        if [[ $total_pods -gt 0 && $not_ready -eq 0 ]]; then
            log_ok "All ${total_pods} pod(s) in '${PIPELINE_NAMESPACE}' are ready (no terminating pods)."
            return
        fi

        # Show which pods are not ready
        local pending
        pending=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" --no-headers 2>/dev/null \
            | awk '$3 != "Running" && $3 != "Completed" {print $1}' || true)
        if [[ -z "$pending" ]]; then
            # All show Running but some containers not ready
            pending=$(kubectl get pods -n "${PIPELINE_NAMESPACE}" --no-headers 2>/dev/null \
                | awk '$2 ~ /0\// {print $1}' || true)
        fi

        log_info "  Pods not ready: ${not_ready}/${total_pods} (${elapsed}s elapsed)"
        if [[ -n "$pending" ]]; then
            log_info "    Waiting on: $(echo $pending | tr '\n' ' ')"
        fi

        sleep $poll_interval
        elapsed=$((elapsed + poll_interval))
    done

    log_warn "Timeout after ${all_pods_timeout}s. Some pods may still be starting."
    kubectl get pods -n "${PIPELINE_NAMESPACE}" --no-headers 2>/dev/null | grep -v "Running\|Completed" || true
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}"
    echo "======================================================"
    echo " ERAG — LLM Model Switch"
    echo " Model: ${MODEL_NAME}"
    echo " $(date)"
    if [[ $DRY_RUN -eq 1 ]]; then
        echo " *** DRY-RUN MODE ***"
    fi
    echo "======================================================"
    echo -e "${RESET}"

    # Show current model before change
    log_info "Current model in gmc-config:"
    kubectl get configmap gmc-config -n "${GMC_NAMESPACE}" -o jsonpath='{.data.vllm\.yaml}' 2>/dev/null \
        | grep -o 'LLM_VLLM_MODEL_NAME: "[^"]*"' || log_warn "Could not read current model."
    echo ""

    ensure_hf_token
    patch_gmc_config
    apply_pipeline
    wait_for_ready
    wait_all_pods_ready
    verify_model

    echo ""
    log_ok "Done. LLM model switched to: ${MODEL_NAME}"
}

main
