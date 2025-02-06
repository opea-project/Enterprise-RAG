#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

repo_path=$(git rev-parse --show-toplevel)
source ${repo_path}/src/ui/.env
source ${repo_path}/deployment/default_credentials.txt

username=${KEYCLOAK_ERAG_ADMIN_USERNAME}
password=${KEYCLOAK_ERAG_ADMIN_PASSWORD}

resolve_hosts="--resolve ${VITE_KEYCLOAK_URL#*://}:80:127.0.0.1 --resolve ${VITE_KEYCLOAK_URL#*://}:443:127.0.0.1"

ADMIN_PASSWORD=$(kubectl get secret --namespace auth keycloak -o jsonpath="{.data.admin-password}" | base64 -d)
ADMIN_ACCESS_TOKEN=$(curl $resolve_hosts -ksL -X POST "${VITE_KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
	-H "Content-Type: application/x-www-form-urlencoded" \
	-d "username=admin" \
	-d "password=${ADMIN_PASSWORD}" \
	-d 'grant_type=password' \
	-d 'client_id=admin-cli' | jq -r '.access_token')

TIMEOUT_REALM_JSON='{
"ssoSessionIdleTimeout": "10800",
"oauth2DeviceCodeLifespan": "10800",
"accessTokenLifespan": "10800",
"accessTokenLifespanForImplicitFlow": "10800"
}'

curl $resolve_hosts -ksL -X PUT "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}" \
-H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d "$TIMEOUT_REALM_JSON"

USER_ID=$(curl $resolve_hosts -ksL -X GET "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users?username=$username" \
-H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
-H "Content-Type: application/json" | jq -r '.[0].id')

CURRENT_REQUIRED_ACTIONS=$(curl $resolve_hosts -ksL -X GET "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users/${USER_ID}" \
-H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}" \
-H "Content-Type: application/json" | jq -r '.requiredActions')

curl $resolve_hosts -ksL -X PUT "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users/${USER_ID}" \
-H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}" \
-H "Content-Type: application/json" \
-d '{
	"requiredActions": []
}'

export USER_ACCESS_TOKEN=$(curl $resolve_hosts -ksL -X POST "${VITE_KEYCLOAK_URL}/realms/${VITE_KEYCLOAK_REALM}/protocol/openid-connect/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=${username}" \
-d "password=${password}" \
-d 'grant_type=password' \
-d "client_id=${VITE_KEYCLOAK_CLIENT_ID}" | jq -r '.access_token')

curl $resolve_hosts -ksL -X PUT "${VITE_KEYCLOAK_URL}/admin/realms/${VITE_KEYCLOAK_REALM}/users/${USER_ID}" \
-H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}" \
-H "Content-Type: application/json" \
-d '{
	"requiredActions": '"${CURRENT_REQUIRED_ACTIONS}"'
}'
