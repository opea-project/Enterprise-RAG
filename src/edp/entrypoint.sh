#!/usr/bin/env bash

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

python $HOME/app/init_db.py

if [ "$#" -eq 0 ]; then
    exec uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
else
    exec "$@"
fi
