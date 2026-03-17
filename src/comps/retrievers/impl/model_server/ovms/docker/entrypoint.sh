#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# NER OVMS entrypoint — exports model to OpenVINO IR, starts OVMS in the
# background, waits for readiness, then starts the NER gateway in the
# foreground.

set -e

# ---------- Model name ----------
if [ -n "$NER_MODEL_NAME" ]; then
    NAME=$(basename "$NER_MODEL_NAME")
    echo "Model name: $NAME"
else
    echo "ERROR: NER_MODEL_NAME not set"
    exit 1
fi

NER_MODEL_DIR="/data/${NAME}_ner"
OVMS_MODEL_DIR="/model/1"

# ---------- Step 1: Export model to OpenVINO IR ----------
if [ -d "$NER_MODEL_DIR" ]; then
    echo "Model already exported at $NER_MODEL_DIR — skipping export."
else
    echo "Exporting NER model to OpenVINO IR …"

    # Configurable weight format (default: int8 for performance)
    WEIGHT_FORMAT=${NER_WEIGHT_FORMAT:-int8}
    if [ "$WEIGHT_FORMAT" = "int8" ]; then
        WEIGHT_ARG="--weight-format int8"
        echo "Using INT8 quantization"
    else
        WEIGHT_ARG=""
        echo "Using FP32 (full precision)"
    fi

    EXPORT_TIMEOUT=${NER_EXPORT_TIMEOUT:-600}
    echo "Export timeout: ${EXPORT_TIMEOUT}s"

    timeout ${EXPORT_TIMEOUT}s optimum-cli export openvino \
        --model "$NER_MODEL_NAME" \
        --task token-classification \
        $WEIGHT_ARG \
        "$NER_MODEL_DIR"

    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "ERROR: Model export timed out after ${EXPORT_TIMEOUT}s"
        echo "Check: network connectivity to huggingface.co, proxy settings (HTTP_PROXY in .env)"
        exit 1
    elif [ $EXIT_CODE -ne 0 ]; then
        echo "ERROR: Model export failed (exit code $EXIT_CODE)"
        exit 1
    fi

    echo "Export complete: $NER_MODEL_DIR"
fi

# ---------- Step 2: Prepare OVMS model directory ----------
mkdir -p "$OVMS_MODEL_DIR"
cp "$NER_MODEL_DIR"/openvino_model.xml "$OVMS_MODEL_DIR/model.xml"
cp "$NER_MODEL_DIR"/openvino_model.bin "$OVMS_MODEL_DIR/model.bin"
echo "Model copied to $OVMS_MODEL_DIR"

# ---------- Step 3: Start OVMS in background ----------
OVMS_INTERNAL_PORT=${OVMS_INTERNAL_PORT:-9000}
echo "Starting OVMS on internal port $OVMS_INTERNAL_PORT …"

/ovms/bin/ovms \
    --model_name "$NAME" \
    --model_path /model \
    --rest_port "$OVMS_INTERNAL_PORT" \
    --log_level INFO &

OVMS_PID=$!
echo "OVMS started (PID $OVMS_PID)"

# ---------- Step 4: Wait for OVMS readiness ----------
echo "Waiting for OVMS to be ready …"
MAX_WAIT=120
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "http://localhost:$OVMS_INTERNAL_PORT/v2/health/ready" > /dev/null 2>&1; then
        echo "OVMS is ready."
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "ERROR: OVMS failed to become ready within ${MAX_WAIT}s"
    kill $OVMS_PID 2>/dev/null
    exit 1
fi

# ---------- Step 5: Start NER gateway (foreground, production WSGI) ----------
export OVMS_INTERNAL_ENDPOINT="http://localhost:$OVMS_INTERNAL_PORT"

echo "Starting NER Gateway …"
exec python /home/ovms/ner_gateway.py
