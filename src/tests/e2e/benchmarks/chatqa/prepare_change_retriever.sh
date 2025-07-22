#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

source generate_uat_to_file.sh "/dev/null" 1
if [[ -z "$USER_ACCESS_TOKEN" ]] || [[ "$USER_ACCESS_TOKEN" == "null" ]]; then
	echo "Error: failed to generate user access token"
	exit 1
fi

if [ -z "$1" ]; then
	echo "Error: No k, provided"
	exit 1
else
	k=$1
fi

url="https://${ERAG_DOMAIN_NAME:-erag.com}/v1/system_fingerprint/change_arguments"
curl -H "Content-Type: application/json" -H "Authorization: Bearer ${USER_ACCESS_TOKEN}" -vkL ${url} -d '[
    {
        "name": "retriever",
        "data": {
            "k": '${k}'
        }
    }
]'
