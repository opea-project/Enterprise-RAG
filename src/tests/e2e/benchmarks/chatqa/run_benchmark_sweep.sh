#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Enterprise RAG ChatQA – Benchmark parameter sweep
#
# Usage:
#   ./run_benchmark_sweep.sh [--dry-run]
#
# Required environment variables (set before running):
#   KEYCLOAK_ERAG_ADMIN_PASSWORD   – UI admin password
#   KEYCLOAK_REALM_ADMIN_PASSWORD  – Realm admin password
#
# Optional environment variables (defaults shown):
#   ERAG_DOMAIN_NAME   – eRAG domain              (default: erag.com)
#   ERAG_ROUTING_MODE  – "subdomain" or "path"     (default: subdomain)
#   HF_MODEL           – HuggingFace tokenizer model (default: meta-llama/Llama-3.1-8B-Instruct)
#   HF_TOKEN           – HuggingFace token, needed for gated models
#   BENCHMARK_DURATION – Duration per run           (default: 10m)
#   UAT_FILE           – Path for token storage     (default: /tmp/uat.txt)
#   TARGET_VECTORS     – Minimum vectors in DB      (default: 1000000)
#   RESULTS_DIR        – Output directory           (default: ./results_<timestamp>)

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURABLE SWEEP PARAMETERS
# Edit these arrays to change the parameter sweep.
# token_params are PAIRED: SWEEP_INPUT_TOKENS[i] maps to SWEEP_OUTPUT_TOKENS[i]
# Scenarios:
#   128/128   – Short query, short response
#   256/256   – Medium query, medium response
#   256/512   – Medium query, extended response
#   256/1024  – Medium query, long response
# NOTE: input tokens are capped at 256 because the embedding model
# (BAAI/bge-base-en-v1.5) has a hard 512-token architectural limit. vLLM adds
# ~21 special tokens, so inputs padded to 512+ tokens cause a 400 from the
# Embedding step. To test larger inputs, replace the embedding model with one
# that supports longer sequences (e.g., BAAI/bge-m3, max 8192 tokens).
# ─────────────────────────────────────────────────────────────────────────────
SWEEP_USERS=(1 4 8 16 32 64 128)
SWEEP_INPUT_TOKENS=(128 256 256 256)
SWEEP_OUTPUT_TOKENS=(128 256 512 1024)
SWEEP_TOP_N=(1)
SWEEP_K=(5)
SWEEP_Q_FILES=("questions-pubmed")

# ─────────────────────────────────────────────────────────────────────────────
# Runtime settings (override via env vars)
# ─────────────────────────────────────────────────────────────────────────────
ERAG_DOMAIN="${ERAG_DOMAIN_NAME:-erag.com}"
HF_MODEL="${HF_MODEL:-meta-llama/Llama-3.1-8B-Instruct}"
BENCHMARK_DURATION="${BENCHMARK_DURATION:-1m}"
UAT_FILE="${UAT_FILE:-/tmp/uat.txt}"
TARGET_VECTORS="${TARGET_VECTORS:-1000000}"
RESULTS_DIR="${RESULTS_DIR:-}"
DRY_RUN=0

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
log_sep()   { echo -e "${BOLD}────────────────────────────────────────────────────${RESET}"; }

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help)
            head -30 "${BASH_SOURCE[0]}" | grep '^#' | sed 's/^# \?//'
            exit 0 ;;
        *) log_error "Unknown argument: $arg"; exit 1 ;;
    esac
done

# ─────────────────────────────────────────────────────────────────────────────
# Prerequisites check
# ─────────────────────────────────────────────────────────────────────────────
check_prerequisites() {
    log_sep
    log_info "Checking prerequisites …"
    local errors=0

    # Required env vars
    for var in KEYCLOAK_ERAG_ADMIN_PASSWORD KEYCLOAK_REALM_ADMIN_PASSWORD; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required env var '$var' is not set."
            if [[ "$var" == "KEYCLOAK_ERAG_ADMIN_PASSWORD" ]]; then
                log_error "  Export it, or load defaults:"
                log_error "    source ${SCRIPT_DIR}/../../../../../deployment/ansible-logs/default_credentials.txt"
                log_error "    export KEYCLOAK_ERAG_ADMIN_PASSWORD=\$KEYCLOAK_ERAG_ADMIN_PASSWORD"
            else
                log_error "  Export it, or load defaults:"
                log_error "    export KEYCLOAK_REALM_ADMIN_PASSWORD=\$(cat ${SCRIPT_DIR}/../../../../../deployment/ansible-logs/default_credentials.yaml | grep KEYCLOAK_REALM_ADMIN_PASSWORD | awk '{print \$2}')"
            fi
            errors=$((errors + 1))
        else
            log_ok "$var is set."
        fi
    done

    # Proxy bypass
    local proxy_ok=0
    for proxy_var in no_proxy NO_PROXY; do
        if echo "${!proxy_var:-}" | grep -q "erag.com"; then
            proxy_ok=1
            break
        fi
    done
    if [[ $proxy_ok -eq 0 ]]; then
        log_error "Proxy bypass for 'erag.com' is NOT configured."
        log_error "  Run:"
        log_error "    export no_proxy=\"\${no_proxy:+\$no_proxy,}erag.com,.erag.com\""
        log_error "    export NO_PROXY=\"\${NO_PROXY:+\$NO_PROXY,}erag.com,.erag.com\""
        errors=$((errors + 1))
    else
        log_ok "Proxy bypass for erag.com is configured."
    fi

    # /etc/hosts entries
    if grep -qE "(^|\s)${ERAG_DOMAIN//./\\.}(\s|$)" /etc/hosts 2>/dev/null; then
        log_ok "/etc/hosts contains an entry for ${ERAG_DOMAIN}."
    else
        log_error "/etc/hosts does NOT contain an entry for '${ERAG_DOMAIN}'."
        log_error "  Add a line such as:"
        log_error "    <ERAG_IP>  minio.${ERAG_DOMAIN} grafana.${ERAG_DOMAIN} s3.${ERAG_DOMAIN} ${ERAG_DOMAIN} auth.${ERAG_DOMAIN}"
        errors=$((errors + 1))
    fi

    # TLS certificate
    local curl_rc=0
    curl --silent --max-time 5 "https://${ERAG_DOMAIN}" -o /dev/null 2>&1 || curl_rc=$?
    if [[ $curl_rc -eq 0 || $curl_rc -eq 22 || $curl_rc -eq 35 ]]; then
        # 0=ok, 22=HTTP error (cert fine), 35=SSL handshake (server alive but cert may be untrusted)
        if [[ $curl_rc -eq 35 ]]; then
            log_warn "TLS certificate may not be fully trusted (curl exit 35). Consider running:"
            log_warn "  sudo -E ${SCRIPT_DIR}/add_cert_to_ca.sh"
        else
            log_ok "TLS certificate appears trusted."
        fi
    elif [[ $curl_rc -eq 60 || $curl_rc -eq 51 ]]; then
        log_error "TLS certificate is NOT trusted (curl exit $curl_rc – SSL verification failed)."
        log_error "  Run: sudo -E ${SCRIPT_DIR}/add_cert_to_ca.sh"
        errors=$((errors + 1))
    else
        log_warn "Cannot reach https://${ERAG_DOMAIN} (curl exit $curl_rc). Verify /etc/hosts and network."
        log_warn "  Continuing – TLS check skipped."
    fi

    # Required tools
    for tool in python3 curl jq wget; do
        if ! command -v "$tool" &>/dev/null; then
            log_error "Required tool '$tool' not found in PATH."
            errors=$((errors + 1))
        else
            log_ok "'$tool' is available."
        fi
    done

    # Python benchmark.py
    if [[ ! -f "${SCRIPT_DIR}/benchmark.py" ]]; then
        log_error "benchmark.py not found in ${SCRIPT_DIR}."
        errors=$((errors + 1))
    else
        log_ok "benchmark.py found."
    fi

    # Question CSV files
    for qf in "${SWEEP_Q_FILES[@]}"; do
        if [[ ! -f "${SCRIPT_DIR}/${qf}.csv" ]]; then
            log_error "Question file '${qf}.csv' not found in ${SCRIPT_DIR}."
            errors=$((errors + 1))
        else
            log_ok "Question file '${qf}.csv' found."
        fi
    done

    # Input/output token array length parity
    if [[ ${#SWEEP_INPUT_TOKENS[@]} -ne ${#SWEEP_OUTPUT_TOKENS[@]} ]]; then
        log_error "SWEEP_INPUT_TOKENS and SWEEP_OUTPUT_TOKENS arrays must have the same length."
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "$errors prerequisite check(s) failed. Please fix the issues above and re-run."
        exit 1
    fi
    log_ok "All prerequisite checks passed."
}

# ─────────────────────────────────────────────────────────────────────────────
# Vector DB check & ingestion
# ─────────────────────────────────────────────────────────────────────────────
check_and_prepare_vectors() {
    log_sep
    log_info "Checking vector count and preparing database if needed …"
    log_info "prepare_1M_vectors.sh handles token generation and the vector count check internally."

    if [[ ! -f "${SCRIPT_DIR}/prepare_1M_vectors.sh" ]]; then
        log_error "prepare_1M_vectors.sh not found in ${SCRIPT_DIR}."
        exit 1
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would run: bash ${SCRIPT_DIR}/prepare_1M_vectors.sh ${TARGET_VECTORS}"
    else
        bash "${SCRIPT_DIR}/prepare_1M_vectors.sh" "${TARGET_VECTORS}"
    fi

    # After the ingestion script returns, do a final authoritative vector count
    # to make absolutely sure everything is ingested and the target is met
    # before allowing any benchmark run to start.
    # A fresh token is needed here because prepare_1M_vectors.sh ran in a subshell.
    if [[ $DRY_RUN -eq 0 ]]; then
        log_info "Performing post-ingestion vector count verification …"
        source "${SCRIPT_DIR}/generate_uat_to_file.sh" "/dev/null" 1
        if [[ -z "${USER_ACCESS_TOKEN:-}" ]] || [[ "${USER_ACCESS_TOKEN}" == "null" ]]; then
            log_error "Failed to generate a user access token for post-ingestion verification."
            exit 1
        fi

        local edp_url="https://${ERAG_DOMAIN}/api/v1/edp"
        local verified_chunks=0 in_progress_count=0
        local verify_stat
        verify_stat=$(curl -k -s "${edp_url}/files" -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
        while read -r details; do
            local vstatus vchunks
            vstatus=$(echo "$details" | jq -r '.status')
            if [[ "$vstatus" == "ingested" ]]; then
                vchunks=$(echo "$details" | jq -r '.chunks_processed')
                verified_chunks=$((verified_chunks + vchunks))
            elif [[ "$vstatus" != "error" ]]; then
                in_progress_count=$((in_progress_count + 1))
            fi
        done < <(echo "$verify_stat" | jq -c '.[]' 2>/dev/null)

        if [[ $in_progress_count -gt 0 ]]; then
            log_error "Ingestion is still in progress (${in_progress_count} file(s) not yet ingested)."
            log_error "Wait for ingestion to complete, then re-run this script."
            exit 1
        fi

        if [[ "$verified_chunks" -lt "$TARGET_VECTORS" ]]; then
            log_error "Vector count after ingestion (${verified_chunks}) is still below the target (${TARGET_VECTORS})."
            log_error "Check the ingestion logs and re-run prepare_1M_vectors.sh manually."
            exit 1
        fi

        log_ok "Post-ingestion verification passed: ${verified_chunks} vectors in DB (target: ${TARGET_VECTORS})."
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Token generation
# ─────────────────────────────────────────────────────────────────────────────
generate_tokens() {
    local n=$1
    log_info "Generating ${n} user access token(s) → ${UAT_FILE} …"
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would run: source ${SCRIPT_DIR}/generate_uat_to_file.sh ${UAT_FILE} ${n}"
        return
    fi
    # Source so that USER_ACCESS_TOKEN is available in this shell too
    source "${SCRIPT_DIR}/generate_uat_to_file.sh" "${UAT_FILE}" "${n}"
    if [[ $? -ne 0 ]]; then
        log_error "Token generation failed."
        exit 1
    fi
    log_ok "${n} token(s) written to ${UAT_FILE}."
}

# ─────────────────────────────────────────────────────────────────────────────
# eRAG configuration helpers
# ─────────────────────────────────────────────────────────────────────────────
set_top_n() {
    log_info "Configuring reranker top_n=$1 …"
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would run: bash ${SCRIPT_DIR}/prepare_change_reranker.sh $1"
        return
    fi
    bash "${SCRIPT_DIR}/prepare_change_reranker.sh" "$1"
}

set_k() {
    log_info "Configuring retriever k=$1 …"
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would run: bash ${SCRIPT_DIR}/prepare_change_retriever.sh $1"
        return
    fi
    bash "${SCRIPT_DIR}/prepare_change_retriever.sh" "$1"
}

set_max_new_tokens() {
    log_info "Configuring LLM max_new_tokens=$1 …"
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "[DRY-RUN] Would run: bash ${SCRIPT_DIR}/prepare_change_max_tokens.sh $1"
        return
    fi
    bash "${SCRIPT_DIR}/prepare_change_max_tokens.sh" "$1"
}

# ─────────────────────────────────────────────────────────────────────────────
# Benchmark sweep
# ─────────────────────────────────────────────────────────────────────────────
run_sweep() {
    log_sep
    if [[ -z "$RESULTS_DIR" ]]; then
        RESULTS_DIR="${SCRIPT_DIR}/results_$(date +%Y%m%d_%H%M%S)"
    fi
    mkdir -p "${RESULTS_DIR}"
    log_info "Results directory: ${RESULTS_DIR}"

    local total_token_pairs=${#SWEEP_INPUT_TOKENS[@]}
    local total_runs=$(( ${#SWEEP_TOP_N[@]} * ${#SWEEP_K[@]} * total_token_pairs * ${#SWEEP_Q_FILES[@]} * ${#SWEEP_USERS[@]} ))
    log_info "Sweep dimensions:"
    log_info "  top_n values     : ${SWEEP_TOP_N[*]}"
    log_info "  k values         : ${SWEEP_K[*]}"
    log_info "  token pairs      : $(for i in "${!SWEEP_INPUT_TOKENS[@]}"; do printf "in%s/out%s " "${SWEEP_INPUT_TOKENS[$i]}" "${SWEEP_OUTPUT_TOKENS[$i]}"; done)"
    log_info "  question files   : ${SWEEP_Q_FILES[*]}"
    log_info "  user counts      : ${SWEEP_USERS[*]}"
    log_info "  duration per run : ${BENCHMARK_DURATION}"
    log_info "  total runs       : ${total_runs}"
    log_sep

    local current_run=0
    local prev_top_n="" prev_k="" prev_output_tokens=""

    for top_n in "${SWEEP_TOP_N[@]}"; do
      for k in "${SWEEP_K[@]}"; do

        # Only call the API when the value actually changes
        if [[ "$top_n" != "$prev_top_n" ]]; then
            set_top_n "$top_n"
            prev_top_n="$top_n"
        fi
        if [[ "$k" != "$prev_k" ]]; then
            set_k "$k"
            prev_k="$k"
        fi

        for tok_idx in "${!SWEEP_INPUT_TOKENS[@]}"; do
            local input_tokens="${SWEEP_INPUT_TOKENS[$tok_idx]}"
            local output_tokens="${SWEEP_OUTPUT_TOKENS[$tok_idx]}"

            if [[ "$output_tokens" != "$prev_output_tokens" ]]; then
                set_max_new_tokens "$output_tokens"
                prev_output_tokens="$output_tokens"
            fi

          for q_file in "${SWEEP_Q_FILES[@]}"; do
            for users in "${SWEEP_USERS[@]}"; do
                current_run=$((current_run + 1))

                local label="run${current_run}_users${users}_in${input_tokens}_out${output_tokens}_topn${top_n}_k${k}_${q_file}"
                local run_dir="${RESULTS_DIR}/${label}"
                mkdir -p "${run_dir}"

                log_sep
                log_info "Run ${current_run}/${total_runs}: ${label}"
                log_info "Results directory: ${run_dir}"

                # Regenerate tokens before every run – tokens expire after ~3 hours
                generate_tokens "$users"

                local benchmark_cmd=(
                    python3 "${SCRIPT_DIR}/benchmark.py"
                    -f "${SCRIPT_DIR}/${q_file}.csv"
                    -d "${BENCHMARK_DURATION}"
                    -c "${users}"
                    -b "${UAT_FILE}"
                    -m "${HF_MODEL}"
                    -x "${input_tokens}"
                    -s "https://${ERAG_DOMAIN}/api/v1/chatqna"
                )

                log_info "Command: ${benchmark_cmd[*]}"

                if [[ $DRY_RUN -eq 1 ]]; then
                    log_info "[DRY-RUN] Skipping actual benchmark execution."
                    continue
                fi

                # Each benchmark.py execution runs in its own labelled subdirectory.
                # benchmark.py writes bench_<timestamp>_users-N_delay-Xs.csv into cwd.
                # Use || rc=$? to prevent set -e from killing the sweep on benchmark failure.
                local rc=0
                (
                    cd "${run_dir}" || exit 1
                    "${benchmark_cmd[@]}"
                ) || rc=$?

                if [[ $rc -ne 0 ]]; then
                    log_warn "Run ${current_run} exited with code ${rc}."
                    echo "${label}: FAILED (exit ${rc})" >> "${RESULTS_DIR}/sweep_summary.txt"
                else
                    log_ok "Run ${current_run} completed. Results in: ${run_dir}"
                    echo "${label}: OK" >> "${RESULTS_DIR}/sweep_summary.txt"
                fi

            done   # users
          done   # q_file
        done   # token pairs
      done   # k
    done   # top_n

    log_sep
    log_info "All ${total_runs} runs finished."

    if [[ $DRY_RUN -eq 0 ]]; then
        log_info "Sweep summary:"
        cat "${RESULTS_DIR}/sweep_summary.txt" 2>/dev/null || true

        # Aggregate parse.py output from all run dirs into one CSV
        if [[ -f "${SCRIPT_DIR}/parse.py" ]]; then
            log_info "Parsing all run results into ${RESULTS_DIR}/parsed_results.csv …"
            local first=1
            for run_dir_item in "${RESULTS_DIR}"/run*; do
                [[ -d "$run_dir_item" ]] || continue
                if [[ $first -eq 1 ]]; then
                    python3 "${SCRIPT_DIR}/parse.py" "${run_dir_item}" \
                        >> "${RESULTS_DIR}/parsed_results.csv" 2>/dev/null && first=0
                else
                    python3 "${SCRIPT_DIR}/parse.py" "${run_dir_item}" 2>/dev/null \
                        | tail -n +2 >> "${RESULTS_DIR}/parsed_results.csv"
                fi
            done
            if [[ -f "${RESULTS_DIR}/parsed_results.csv" ]]; then
                log_ok "Parsed results: ${RESULTS_DIR}/parsed_results.csv"
            else
                log_warn "No parsed results generated."
            fi
        fi
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}"
    echo "======================================================"
    echo " Enterprise RAG ChatQA – Benchmark Sweep"
    echo " $(date)"
    if [[ $DRY_RUN -eq 1 ]]; then
        echo " *** DRY-RUN MODE – no commands will be executed ***"
    fi
    echo "======================================================"
    echo -e "${RESET}"

    check_prerequisites
    check_and_prepare_vectors
    run_sweep
}

main "$@"
