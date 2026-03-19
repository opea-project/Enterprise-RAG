#!/usr/bin/env bash

# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

alembic upgrade head

if [ "$#" -eq 0 ]; then
    exec uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
else
    exec "$@"
fi
