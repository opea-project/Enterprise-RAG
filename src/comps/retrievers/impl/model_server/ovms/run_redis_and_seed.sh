#!/bin/bash
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Starts Redis with RediSearch and seeds it with test documents
#
# The script:
# 1. Starts the `edp-redis` container
# 2. Waits for Redis to be ready
# 3. Inserts examplary documents
#
# Usage:
#   chmod +x run_redis_and_seed.sh
#   ./run_redis_and_seed.sh [--redis-port 6379] [--dims 768]

set -euo pipefail

REDIS_IMAGE="redis:8.2.5-alpine"
CONTAINER_NAME="edp-redis"
REDIS_PORT="${REDIS_PORT:-6379}"
DIMS="${DIMS:-768}"

# Parse optional CLI arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --redis-port) REDIS_PORT="$2"; shift 2 ;;
    --dims)       DIMS="$2";       shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# 1. Start Redis
# ---------------------------------------------------------------------------
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "[redis] Container '${CONTAINER_NAME}' is already running — skipping start."
elif docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "[redis] Starting existing container '${CONTAINER_NAME}'..."
  docker start "${CONTAINER_NAME}"
else
  echo "[redis] Starting new container '${CONTAINER_NAME}' on port ${REDIS_PORT}..."
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${REDIS_PORT}:6379" \
    "${REDIS_IMAGE}"
fi

# Wait for Redis to be ready
echo "[redis] Waiting for Redis to be ready..."
for i in $(seq 1 30); do
  if docker exec "${CONTAINER_NAME}" redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "[redis] Ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "[redis] ERROR: Redis did not become ready in time."
    exit 1
  fi
  sleep 1
done

# ---------------------------------------------------------------------------
# 2. Seed test documents
# ---------------------------------------------------------------------------
echo "[seed] Inserting test documents (DIMS=${DIMS})..."

SEED_DIMS="${DIMS}" SEED_PORT="${REDIS_PORT}" python3 - <<'PYEOF'
import struct, uuid, random, time, sys, os
import importlib.util

# Check redis package
if importlib.util.find_spec("redis") is None:
    import subprocess
    print("[seed] Installing redis package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis", "-q"])

import redis

DIMS = int(os.environ["SEED_DIMS"])
r = redis.Redis(host="localhost", port=int(os.environ["SEED_PORT"]), decode_responses=False)

def rand_embedding(dims=DIMS):
    v = [random.gauss(0, 1) for _ in range(dims)]
    return struct.pack(f"{dims}f", *v)

documents = [
    {
        "text": "John Smith's Q1 2024 financial report shows revenue growth of 12%.",
        "author": "John Smith",
        "file_title": "Q1 2024 Financial Report",
        "creation_date": int(time.mktime(time.strptime("2024-03-31", "%Y-%m-%d"))),
        "bucket_name": "default",
        "object_name": "Q1_2024_report.pdf",
        "file_id": str(uuid.uuid4()),
    },
    {
        "text": "John Smith's review of AI infrastructure investments from Q3 2023.",
        "author": "John Smith",
        "file_title": "AI Infrastructure Review Q3 2023",
        "creation_date": int(time.mktime(time.strptime("2023-09-30", "%Y-%m-%d"))),
        "bucket_name": "default",
        "object_name": "ai_infra_q3_2023.pdf",
        "file_id": str(uuid.uuid4()),
    },
    {
        "text": "Anna Nowak's summary of European market trends and forecasts for 2025.",
        "author": "Anna Nowak",
        "file_title": "European Market Outlook 2025",
        "creation_date": int(time.mktime(time.strptime("2025-01-15", "%Y-%m-%d"))),
        "bucket_name": "default",
        "object_name": "eu_market_outlook_2025.pdf",
        "file_id": str(uuid.uuid4()),
    },
]

for doc in documents:
    key = f"erag:{uuid.uuid4()}"
    r.hset(key, mapping={
        "text":          doc["text"].encode(),
        "embedding":     rand_embedding(),
        "author":        doc["author"].encode(),
        "file_title":    doc["file_title"].encode(),
        "creation_date": doc["creation_date"],
        "bucket_name":   doc["bucket_name"].encode(),
        "object_name":   doc["object_name"].encode(),
        "file_id":       doc["file_id"].encode(),
    })
    print(f"  Inserted: {key}  [{doc['file_title']}]")

print(f"\n[seed] Done. {len(documents)} documents inserted.")

PYEOF
