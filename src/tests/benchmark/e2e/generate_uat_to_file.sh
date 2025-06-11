#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

generate_uat_to_file()
{
	fname=$1
	sessions=$2
	if ! [[ "$sessions" =~ ^[1-9][0-9]*$ ]]; then
		echo "the second argument (number of tokens) must be a positive integer."
		return 1
	fi

	VITE_KEYCLOAK_REALM="EnterpriseRAG"
	VITE_KEYCLOAK_CLIENT_ID="EnterpriseRAG-oidc"
	VITE_KEYCLOAK_URL="https://auth.${ERAG_DOMAIN_NAME:-erag.com}"

	if [[ -z "${KEYCLOAK_REALM_ADMIN_PASSWORD}" ]]; then
		echo "missing KEYCLOAK_REALM_ADMIN_PASSWORD env variable"
		return 1
	fi

	if [[ -z "${KEYCLOAK_ERAG_ADMIN_PASSWORD}" ]]; then
		echo "missing KEYCLOAK_ERAG_ADMIN_PASSWORD env variable"
		return 1
	fi

	realm_user="${KEYCLOAK_REALM_ADMIN_USERNAME:-admin}"
	realm_pass="${KEYCLOAK_REALM_ADMIN_PASSWORD}"

	ui_user=${KEYCLOAK_ERAG_ADMIN_USERNAME:-erag-admin}
	ui_pass=${KEYCLOAK_ERAG_ADMIN_PASSWORD}

	ADMIN_ACCESS_TOKEN=$(curl -ksL -X POST "${VITE_KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
		-H "Content-Type: application/x-www-form-urlencoded" \
		-d "username=${realm_user}" \
		-d "password=${realm_pass}" \
		-d 'grant_type=password' \
		-d 'client_id=admin-cli' | jq -r '.access_token')

	if [[ "$ADMIN_ACCESS_TOKEN" == "null" ]]; then
		echo "failed to generate admin access token, Realm username/password is incorrect"
		return 1
	fi

	TIMEOUT_REALM_JSON='{
	"ssoSessionIdleTimeout": "10800",
	"oauth2DeviceCodeLifespan": "10800",
	"accessTokenLifespan": "10800",
	"accessTokenLifespanForImplicitFlow": "10800"
	}'

	curl -ksL -X PUT "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}" \
	-H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
	-H "Content-Type: application/json" \
	-d "$TIMEOUT_REALM_JSON"

	USER_ID=$(curl -ksL -X GET "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users?username=${ui_user}" \
	-H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
	-H "Content-Type: application/json" | jq -r '.[0].id')

	CURRENT_REQUIRED_ACTIONS=$(curl -ksL -X GET "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users/${USER_ID}" \
	-H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}" \
	-H "Content-Type: application/json" | jq -r '.requiredActions')

	curl -ksL -X PUT "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users/${USER_ID}" \
	-H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}" \
	-H "Content-Type: application/json" \
	-d '{
		"requiredActions": []
	}'

	if [[ "$fname" != "/dev/null" ]]; then
		rm -rf $fname
	fi
	for i in $(seq 1 ${sessions}); do
		export USER_ACCESS_TOKEN=$(curl -ksL -X POST "${VITE_KEYCLOAK_URL}/realms/${VITE_KEYCLOAK_REALM}/protocol/openid-connect/token" \
		-H "Content-Type: application/x-www-form-urlencoded" \
		-d "username=${ui_user}" \
		-d "password=${ui_pass}" \
		-d 'grant_type=password' \
		-d "client_id=${VITE_KEYCLOAK_CLIENT_ID}" | jq -r '.access_token')
		if [ "$USER_ACCESS_TOKEN" == "null" ]; then
			echo "failed to generate user access token, UI username/password is incorrect"
			return 1
		fi
		echo $USER_ACCESS_TOKEN | tee -a $fname
	done

	curl -ksL -X PUT "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users/${USER_ID}" \
	-H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}" \
	-H "Content-Type: application/json" \
	-d '{
		"requiredActions": '"${CURRENT_REQUIRED_ACTIONS}"'
	}'
}

if [ "$#" -ne 2 ]; then
	echo "you must provide exactly two arguments."
	status_code=1
else
	generate_uat_to_file $1 $2
	status_code=$?
fi

# script is called in both ways: using 'source' and directly
# so both scenarios have be handled separately
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
	return $status_code
else
	exit $status_code
fi
