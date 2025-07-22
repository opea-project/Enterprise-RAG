#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

refresh_uat()
{
	source generate_uat_to_file.sh "/dev/null" 1
	if [[ -z "$USER_ACCESS_TOKEN" ]] || [[ "$USER_ACCESS_TOKEN" == "null" ]]; then
		echo "Error: failed to generate user access token"
		exit 1
	fi
}

delete_file()
{
	filename=$1
	tmpstr="{ \"bucket_name\": \"default\", \"object_name\": \"${filename}\", \"method\": \"DELETE\" }"
	echo $tmpstr > /tmp/dataprep.json
	curloutput=$(curl -k --no-buffer "${EDP_URL}/presignedUrl" -X POST -d @/tmp/dataprep.json -H 'Content-Type: application/json' -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
	furl=$(echo $curloutput | jq -r '.url')
	curl -k -X DELETE $furl
}


delete_vectors()
{
	upload_stat=$(curl -k -s ${EDP_URL}/files -H "Authorization: Bearer ${USER_ACCESS_TOKEN}")
	while read -r details; do
		fname=$(echo "$details" | jq -r .object_name)
		delete_file $fname
	done < <(echo $upload_stat | jq -c '.[]')
}

export EDP_URL="https://${ERAG_DOMAIN_NAME:-erag.com}/api/v1/edp"
refresh_uat
delete_vectors
