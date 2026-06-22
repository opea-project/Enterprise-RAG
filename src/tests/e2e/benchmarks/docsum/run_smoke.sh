#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "=== DocSum Benchmark Smoke Test ==="
echo ""

echo "Step 1: Preflight check"
./preflight_check.sh
echo ""

echo "Step 2: Generate bearer token"
BEARER_FILE="${SCRIPT_DIR}/.bearer"
if [[ -n "${KEYCLOAK_ERAG_ADMIN_PASSWORD:-}" ]]; then
    python3 -c "
import sys; sys.path.insert(0, '.')
from benchmark import refresh_token_file
if not refresh_token_file('${BEARER_FILE}'):
    sys.exit(1)
print('Token refreshed inline')
"
elif [[ -f "${SCRIPT_DIR}/../chatqa/generate_uat_to_file.sh" ]]; then
    "${SCRIPT_DIR}/../chatqa/generate_uat_to_file.sh" "${BEARER_FILE}" 1
else
    echo "Error: set KEYCLOAK_ERAG_ADMIN_PASSWORD or ensure ../chatqa/generate_uat_to_file.sh exists"
    exit 1
fi
echo ""

echo "Step 3: Run benchmark on small document"
SMOKE_DOC="docs/pubmed_3k.txt"
if [[ ! -f "${SMOKE_DOC}" ]]; then
    echo "  Smoke doc missing, running prepare_pubmed_docs.py..."
    python3 prepare_pubmed_docs.py
fi

SMOKE_OUTPUT="${SCRIPT_DIR}/results/smoke_$(date +%Y%m%d_%H%M%S).csv"
mkdir -p "${SCRIPT_DIR}/results"

python3 -u benchmark.py \
    -f "${SMOKE_DOC}" \
    -c 1 \
    -r 1 \
    -t map_reduce \
    --max-tokens 512 \
    -b .bearer \
    -o "${SMOKE_OUTPUT}" \
    --json-summary

echo ""
echo "Step 4: Validate results"

if [[ ! -f "${SMOKE_OUTPUT}" ]]; then
    echo "SMOKE TEST FAILED: no output CSV produced"
    exit 1
fi

LINES=$(wc -l < "${SMOKE_OUTPUT}")
if [[ ${LINES} -lt 2 ]]; then
    echo "SMOKE TEST FAILED: CSV has no data rows"
    exit 1
fi

HAS_ERROR=$(tail -n +2 "${SMOKE_OUTPUT}" | awk -F',' '{if (NF >= 12 && $12 != "") print $12}')
if [[ -n "${HAS_ERROR}" ]]; then
    echo "SMOKE TEST FAILED: errors in results: ${HAS_ERROR}"
    exit 1
fi

E2E=$(tail -n +2 "${SMOKE_OUTPUT}" | head -1 | cut -d',' -f6)
echo ""
echo "=== SMOKE TEST PASSED ==="
echo "  Output: ${SMOKE_OUTPUT}"
echo "  E2E latency: ${E2E}s"
