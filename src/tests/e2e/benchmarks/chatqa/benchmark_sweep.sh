#!/bin/bash
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Benchmark sweep across multiple LLM models and concurrency levels.
#
# This script iterates over a list of models, switches each one using
# switch_llm_model.sh, and runs benchmark.py at multiple concurrency levels
# to produce a full performance sweep.
#
# Usage:
#   ./benchmark_sweep.sh [options]
#
# Options:
#   -m <model>    Add a model to the sweep list (repeatable)
#   -d <duration> Benchmark duration per run (default: 1m)
#   --dry-run     Show what would happen without making changes
#   -h, --help    Show this help message
#
# Environment variables:
#   SWEEP_MODELS  Comma-separated list of models to sweep
#                 (e.g. "Qwen/Qwen3-14B-AWQ,casperhansen/llama-3-8b-instruct-awq")
#
# Model selection priority: -m flags > SWEEP_MODELS env var > default (casperhansen/llama-3-8b-instruct-awq)
#
# Examples:
#   ./benchmark_sweep.sh
#   ./benchmark_sweep.sh -d 2m
#   ./benchmark_sweep.sh -m "Qwen/Qwen3-14B-AWQ" -m "casperhansen/llama-3-8b-instruct-awq"
#   SWEEP_MODELS="Qwen/Qwen3-14B-AWQ,casperhansen/llama-3-8b-instruct-awq" ./benchmark_sweep.sh
#   ./benchmark_sweep.sh --dry-run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────
MODELS=()
DURATION="1m"
DRY_RUN=0

# Default model (used when no -m flags and SWEEP_MODELS env var is not set)
DEFAULT_MODEL="casperhansen/llama-3-8b-instruct-awq"

# Concurrency levels to sweep
CONCURRENCY_LEVELS=(1 2 4 8 16 32 64)

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
        -m)
            MODELS+=("$2"); shift 2 ;;
        -d)
            DURATION="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=1; shift ;;
        -h|--help)
            head -25 "${BASH_SOURCE[0]}" | grep '^#' | sed 's/^# \?//'
            exit 0 ;;
        -*)
            log_error "Unknown option: $1"; exit 1 ;;
        *)
            log_error "Unexpected argument: $1"; exit 1 ;;
    esac
done

# Model priority: -m flags > SWEEP_MODELS env var > DEFAULT_MODEL
if [[ ${#MODELS[@]} -eq 0 ]]; then
    if [[ -n "${SWEEP_MODELS:-}" ]]; then
        # SWEEP_MODELS is comma-separated, e.g. "model1,model2"
        IFS=',' read -ra MODELS <<< "$SWEEP_MODELS"
    else
        MODELS=("$DEFAULT_MODEL")
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Activate Python virtual environment
# ─────────────────────────────────────────────────────────────────────────────
VENV_DIR="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)/deployment/erag-venv"
if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"
    log_info "Activated venv: ${VENV_DIR}"
else
    log_warn "erag-venv not found at ${VENV_DIR} — using system Python"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Validate
# ─────────────────────────────────────────────────────────────────────────────
if [[ ! -x "${SCRIPT_DIR}/switch_llm_model.sh" ]]; then
    log_error "switch_llm_model.sh not found or not executable in ${SCRIPT_DIR}"
    exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/benchmark.py" ]]; then
    log_error "benchmark.py not found in ${SCRIPT_DIR}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
TOTAL_RUNS=$(( ${#MODELS[@]} * ${#CONCURRENCY_LEVELS[@]} ))

echo -e "${BOLD}"
echo "======================================================"
echo " ERAG — Benchmark Sweep"
echo " $(date)"
echo " Models:            ${#MODELS[@]}"
echo " Concurrency sweep: ${CONCURRENCY_LEVELS[*]}"
echo " Duration per run:  ${DURATION}"
echo " Total runs:        ${TOTAL_RUNS}"
if [[ $DRY_RUN -eq 1 ]]; then
    echo " *** DRY-RUN MODE ***"
fi
echo "======================================================"
echo -e "${RESET}"

for i in "${!MODELS[@]}"; do
    echo -e "  $((i+1)). ${MODELS[$i]}"
done
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Results directory
# ─────────────────────────────────────────────────────────────────────────────
SWEEP_DIR="${SCRIPT_DIR}/results_sweep_$(date +%Y%m%d_%H%M%S)"
if [[ $DRY_RUN -eq 0 ]]; then
    mkdir -p "${SWEEP_DIR}"
    log_info "Results will be stored in: ${SWEEP_DIR}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Validate credentials by generating 1 token upfront
# ─────────────────────────────────────────────────────────────────────────────
if [[ $DRY_RUN -eq 0 ]]; then
    log_info "Validating Keycloak credentials (generating 1 token) …"
    set +eu
    source "${SCRIPT_DIR}/generate_uat_to_file.sh" "${SCRIPT_DIR}/uat.txt" "1"
    gen_rc=$?
    set -eu
    if [[ $gen_rc -ne 0 ]]; then
        log_error "Failed to generate bearer token. Ensure KEYCLOAK_REALM_ADMIN_PASSWORD and KEYCLOAK_ERAG_ADMIN_PASSWORD are set."
        exit 1
    fi
    log_ok "Credentials validated."
fi

# ─────────────────────────────────────────────────────────────────────────────
# Sweep
# ─────────────────────────────────────────────────────────────────────────────
FAILED=0
RUN_NUM=0

for i in "${!MODELS[@]}"; do
    MODEL="${MODELS[$i]}"
    MODEL_IDX=$((i + 1))
    # Sanitize model name for filenames
    MODEL_SLUG=$(echo "$MODEL" | tr '/' '_')

    # Create per-model results directory
    RESULTS_DIR="${SWEEP_DIR}/${MODEL_SLUG}"
    if [[ $DRY_RUN -eq 0 ]]; then
        mkdir -p "${RESULTS_DIR}"
    fi

    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    log_info "[Model ${MODEL_IDX}/${#MODELS[@]}] Switching to: ${MODEL}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

    # ── Switch model ──────────────────────────────────────────────────────
    SWITCH_ARGS=("${MODEL}")
    if [[ $DRY_RUN -eq 1 ]]; then
        SWITCH_ARGS+=("--dry-run")
    fi

    if ! "${SCRIPT_DIR}/switch_llm_model.sh" "${SWITCH_ARGS[@]}"; then
        log_error "Failed to switch to model: ${MODEL}"
        FAILED=$((FAILED + ${#CONCURRENCY_LEVELS[@]}))
        continue
    fi

    # ── Run benchmark at each concurrency level ───────────────────────────
    for CONCURRENCY in "${CONCURRENCY_LEVELS[@]}"; do
        RUN_NUM=$((RUN_NUM + 1))

        log_info "[Run ${RUN_NUM}/${TOTAL_RUNS}] model=${MODEL}  concurrency=${CONCURRENCY}  duration=${DURATION}"

        if [[ $DRY_RUN -eq 1 ]]; then
            log_info "[DRY-RUN] Would run: python3 benchmark.py -d ${DURATION} -c ${CONCURRENCY} -m ${MODEL}"
            continue
        fi

        pushd "${SCRIPT_DIR}" >/dev/null 2>&1 || cd "${SCRIPT_DIR}"

        # Generate fresh bearer tokens for this run
        log_info "  Generating ${CONCURRENCY} bearer token(s) …"
        set +eu
        source "${SCRIPT_DIR}/generate_uat_to_file.sh" "${SCRIPT_DIR}/uat.txt" "${CONCURRENCY}"
        gen_rc=$?
        set -eu
        if [[ $gen_rc -ne 0 ]]; then
            log_error "Failed to generate bearer tokens. Skipping run."
            FAILED=$((FAILED + 1))
            popd >/dev/null 2>&1 || true
            continue
        fi

        # Record existing CSVs before benchmark so we only move new ones
        existing_csvs=$(ls bench_*.result.csv 2>/dev/null || true)

        if python3 benchmark.py -d "$DURATION" -c "$CONCURRENCY" -m "$MODEL" -b uat.txt; then
            log_ok "[Run ${RUN_NUM}/${TOTAL_RUNS}] Completed: ${MODEL} @ c=${CONCURRENCY}"
        else
            log_warn "[Run ${RUN_NUM}/${TOTAL_RUNS}] Failed: ${MODEL} @ c=${CONCURRENCY}"
            FAILED=$((FAILED + 1))
        fi

        # Move only newly created result CSVs to per-model results directory
        for csv_file in bench_*.result.csv; do
            if [[ -f "$csv_file" ]] && ! echo "$existing_csvs" | grep -qF "$csv_file"; then
                mv "$csv_file" "${RESULTS_DIR}/c${CONCURRENCY}_${csv_file}"
                log_info "  Result: ${RESULTS_DIR}/c${CONCURRENCY}_${csv_file}"
            fi
        done

        popd >/dev/null 2>&1 || true
    done
done

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}======================================================"
echo " Sweep Complete"
echo "======================================================${RESET}"
echo -e " Models:        ${#MODELS[@]}"
echo -e " Total runs:    ${TOTAL_RUNS}"
echo -e " Succeeded:     $((TOTAL_RUNS - FAILED))"
if [[ $FAILED -gt 0 ]]; then
    echo -e " ${RED}Failed:        ${FAILED}${RESET}"
fi
if [[ $DRY_RUN -eq 0 ]]; then
    echo -e " Results dir:   ${SWEEP_DIR}"
fi
echo ""

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
