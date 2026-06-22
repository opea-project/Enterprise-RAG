#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export no_proxy="${no_proxy:-},${ERAG_DOMAIN_NAME:-erag.com},auth.${ERAG_DOMAIN_NAME:-erag.com},localhost,127.0.0.1"
export NO_PROXY="${NO_PROXY:-},${ERAG_DOMAIN_NAME:-erag.com},auth.${ERAG_DOMAIN_NAME:-erag.com},localhost,127.0.0.1"
unset https_proxy 2>/dev/null; unset http_proxy 2>/dev/null; unset HTTPS_PROXY 2>/dev/null; unset HTTP_PROXY 2>/dev/null; true

PASS=0
FAIL=0

check() {
    local desc="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "  [OK] ${desc}"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] ${desc}"
        FAIL=$((FAIL + 1))
    fi
}

check_output() {
    local desc="$1"
    shift
    local out
    if out=$("$@" 2>&1); then
        echo "  [OK] ${desc}"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] ${desc}: ${out}"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== DocSum Benchmark Preflight Check ==="
echo ""

echo "1. Network connectivity"
check_output "eRAG API reachable" curl -sk --max-time 10 "https://${ERAG_DOMAIN_NAME:-erag.com}/api/v1/health/ready"
check_output "Keycloak reachable" curl -sk --max-time 10 "https://auth.${ERAG_DOMAIN_NAME:-erag.com}/realms/EnterpriseRAG/.well-known/openid-configuration"

echo ""
echo "2. Credentials"
if [[ -n "${KEYCLOAK_ERAG_ADMIN_PASSWORD:-}" ]]; then
    echo "  [OK] KEYCLOAK_ERAG_ADMIN_PASSWORD set"
    PASS=$((PASS + 1))
else
    CREDS_FILE="${SCRIPT_DIR}/../../../../../deployment/ansible-logs/default_credentials.txt"
    if [[ -f "${CREDS_FILE}" ]]; then
        echo "  [OK] Credentials file found at ${CREDS_FILE}"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] No KEYCLOAK_ERAG_ADMIN_PASSWORD and no credentials file"
        FAIL=$((FAIL + 1))
    fi
fi

echo ""
echo "3. Python environment"
check "Python 3.11+ available" python3 -c "import sys; assert sys.version_info >= (3, 11)"
check "requests module" python3 -c "import requests"
check "pandas module" python3 -c "import pandas"
if python3 -c "from transformers import AutoTokenizer" >/dev/null 2>&1; then
    echo "  [OK] transformers module (optional, enables precise token counting)"
    PASS=$((PASS + 1))
else
    echo "  [INFO] transformers not installed (optional, word-count approximation will be used)"
fi

echo ""
echo "4. Test documents"
if [[ -f "${SCRIPT_DIR}/docs/pubmed_3k.txt" ]]; then
    echo "  [OK] pubmed_3k.txt exists"
    PASS=$((PASS + 1))
else
    echo "  [FAIL] pubmed_3k.txt missing (run ./prepare_pubmed_docs.py)"
    FAIL=$((FAIL + 1))
fi
if [[ -f "${SCRIPT_DIR}/docs/pubmed_67k.txt" ]]; then
    echo "  [OK] pubmed_67k.txt exists"
    PASS=$((PASS + 1))
else
    echo "  [FAIL] pubmed_67k.txt missing (run ./prepare_pubmed_docs.py)"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="

if [[ ${FAIL} -gt 0 ]]; then
    echo "Preflight check FAILED. Fix the issues above before running benchmarks."
    exit 1
fi
echo "All checks passed."
