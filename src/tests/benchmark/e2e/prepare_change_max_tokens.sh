#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

echo "generate uat.sh"
source generate_uat.sh

echo $USER_ACCESS_TOKEN
if [ -z "$1" ]; then
  echo "Error: No max_new_tokens, provided"
  exit 1
else
  tokens=$1
fi

curl -H "Content-Type: application/json" -H "Authorization: Bearer ${USER_ACCESS_TOKEN}" -vkL https://erag.com/v1/system_fingerprint/change_arguments -d '[
    {
        "name": "llm",
        "data": {
            "max_new_tokens": '${tokens}',
            "top_k": 10
        }
    }
]'
