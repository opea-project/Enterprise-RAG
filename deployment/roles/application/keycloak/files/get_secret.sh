#!/bin/bash

# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:${KEYCLOAK_FPORT}}
KEYCLOAK_REALM=EnterpriseRAG
KEYCLOAK_CLIENT_ID=admin
ADMIN_PASSWORD=${1:-admin}
CLIENT_ID=${2:-"EnterpriseRAG-oidc-backend"}


get_client_id(){
    local client_name=$1
    local url="${KEYCLOAK_URL}/admin/realms/$KEYCLOAK_REALM/clients"
    local response=$(curl -s -w "%{http_code}" \
            -X GET "$url" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Accept: application/json")
    local http_code="${response: -3}" # Last 3 characters are the status code
    local content="${response:: -3}"  # Everything before the last 3 characters is the content

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 400 ]; then
        echo "${http_content}" | jq; parse_return_code=$?
        if [ "${parse_return_code}" -ne "0" ]; then
            echo "HTTP response content is not json parsable. Response content was: ${http_content}" >&2
            exit 1
        fi

        C_ID=$(echo $content | jq -r --arg key "clientId" --arg value "$client_name" '.[] | select(.[$key] == $value)' | jq -r '.id')
    else
        echo "Error: Unable to get client ID, HTTP status code $http_code for URL $url" >&2
        exit 1
    fi
}

get_client_secret(){
    #Get client secret. This will be needed by APISIX and UI
    local url="${KEYCLOAK_URL}/admin/realms/$KEYCLOAK_REALM/clients/$C_ID/client-secret"
    local response=$(curl -s -w "%{http_code}" \
                    -X POST \
                    -H "Authorization: Bearer $ACCESS_TOKEN" \
                    -H "Content-Type: application/json" \
                    "$url")
    local http_code="${response: -3}" # Last 3 characters are the status code
    local content="${response:: -3}"  # Everything before the last 3 characters is the content

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 400 ]; then
        echo "${http_content}" | jq; parse_return_code=$?
        if [ "${parse_return_code}" -ne "0" ]; then
            echo "HTTP response content is not json parsable. Response content was: ${http_content}" >&2
            exit 1
        fi

        CLIENT_SECRET=$(echo $content | jq -r '.value')
    else
        echo "Error: Unable to get client secret, HTTP status code $http_code for URL $url" >&2
        exit 1
    fi
}

# Obtain an Access Token using admin credentials
get_access_token() {
    local url="${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    local response=$(curl -s -w "%{http_code}" \
                    -X POST "$url" \
                    -H "Content-Type: application/x-www-form-urlencoded" \
                    -d "username=${KEYCLOAK_CLIENT_ID}" \
                    -d "password=${ADMIN_PASSWORD}" \
                    -d 'grant_type=password' \
                    -d 'client_id=admin-cli')
    local http_code="${response: -3}" # Last 3 characters are the status code
    local content="${response:: -3}"  # Everything before the last 3 characters is the content

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 400 ]; then
        echo "${http_content}" | jq; parse_return_code=$?
        if [ "${parse_return_code}" -ne "0" ]; then
            echo "HTTP response content is not json parsable. Response content was: ${http_content}" >&2
            exit 1
        fi

        ACCESS_TOKEN=$(echo $content | jq -r '.access_token')
    else
        echo "Error: Unable to get access token, HTTP status code $http_code for URL $url" >&2
        exit 1
    fi
}

get_access_token
get_client_id $CLIENT_ID
get_client_secret
echo $CLIENT_SECRET
