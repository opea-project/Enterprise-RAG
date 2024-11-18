#!/bin/bash

KEYCLOAK_URL=localhost:1234
KEYCLOAK_REALM=EnterpriseRAG
KEYCLOAK_CLIENT_ID=admin
ADMIN_PASSWORD=${1:-admin}

get_client_id(){
    local client_name=$1
    C_ID=$(curl -s -X GET "http://${KEYCLOAK_URL}/admin/realms/$KEYCLOAK_REALM/clients" -H "Authorization: Bearer $ACCESS_TOKEN" -H "Accept: application/json" | jq -r --arg key "clientId" --arg value "$client_name" '.[] | select(.[$key] == $value)' | jq -r '.id')
}

get_client_secret(){
#Get client secret. This will be needed by APISIX and UI
CLIENT_SECRET=$(curl -s -X POST \
     -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     "http://${KEYCLOAK_URL}/admin/realms/$KEYCLOAK_REALM/clients/$C_ID/client-secret" | \
     jq -r '.value')

}

# Obtain an Access Token using admin credentials
ACCESS_TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=${KEYCLOAK_CLIENT_ID}" \
 -d "password=${ADMIN_PASSWORD}" \
 -d 'grant_type=password' \
 -d 'client_id=admin-cli' | jq -r '.access_token')

get_client_id "EnterpriseRAG-oidc-backend"
get_client_secret
echo $CLIENT_SECRET
