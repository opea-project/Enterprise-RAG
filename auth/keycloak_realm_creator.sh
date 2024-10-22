#!/bin/bash

# requires jq
# sudo apt install jq

# set -x
repo_path=$(realpath "$(pwd)/../")
auth_path="$repo_path/auth"
keyclock_config_path="$auth_path/keycloak-config"
AUTH_NS=${1:-default}

export_realm() {
    local realm_name=$1
    local json_name="${realm_name}.json"

    # Step 4: Fetch Realm Details
    REALM_DETAILS=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json")

    # # Step 5: Fetch Clients
    CLIENTS=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json")

    # # Step 6: Fetch Roles
    ROLES=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/roles" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json")

    # Combine all data into one JSON
    jq -n \
        --argjson realmDetails "$REALM_DETAILS" \
        --argjson clients "$CLIENTS" \
        --argjson roles "$ROLES" \
        '{realm: $realmDetails, clients: $clients, roles: $roles}' > "$json_name"
}


add_user() {
    local realm_name=$1
    local username=$2
    local email=$3
    local first_name=$4
    local last_name=$5
    local password=$6
    local role_name=$7
    local client_name=$8

    echo "Adding user $username to realm $realm_name"
    
    CLIENT_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients?clientId=$client_name" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.[0].id')

    NEW_USER_JSON='{
        "username": "'$username'",
	"enabled": true,
	"emailVerified": true,
        "firstName": "'$first_name'",
        "lastName": "'$last_name'",
	"email": "'$email'",
        "emailVerified": true,
        "credentials": [{
            "type": "password",
            "value": "'$password'",
            "temporary": false
        }]
    }'

    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${realm_name}/users" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$NEW_USER_JSON" | jq

    if [ -n "$role_name" ]; then
        echo "Assigning role $role_name to user $username"

        USER_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/users?username=$username" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" | jq -r '.[0].id')
        ROLE_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/$CLIENT_ID/roles" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" | jq -r --arg ROLE_NAME "$role_name" '.[] | select(.name==$ROLE_NAME) | .id')

        curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${realm_name}/users/$USER_ID/role-mappings/clients/$CLIENT_ID" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "[{\"id\": \"$ROLE_ID\", \"name\": \"$role_name\"}]" | jq
    fi
}


create_realm() {
    local realm_name=$1

    echo "Creating a new Keycloak realm: $realm_name"

    NEW_REALM_JSON='{
        "realm": "'$realm_name'",
        "enabled": true,
        "displayName": "My Custom Realm",
        "sslRequired": "none",
        "registrationAllowed": false
    }'

    curl -s -X POST "${KEYCLOAK_URL}/admin/realms" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_REALM_JSON" | jq

    local client_name=myclient-oidc

    echo "Creating a new client: $client_name in realm $realm_name"

    NEW_CLIENT_JSON='{
        "clientId": "'$client_name'",
        "surrogateAuthRequired": false,
        "enabled": true,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": [ "*" ],
        "webOrigins": [ "*" ],
        "publicClient": true,
        "protocol": "openid-connect",
        "frontchannelLogout": false
    }'

    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_CLIENT_JSON" | jq

    CLIENT_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients?clientId=$client_name" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.[0].id')

    echo "CLIENT_ID=$CLIENT_ID"

    local role_name=rag-admin

    echo "Creating a new role: $role_name in client $client_name"

    NEW_ROLE_JSON='{
        "name": "'$role_name'",
        "description": "",
        "composite": false,
        "clientRole": true,
        "containerId": "'$CLIENT_ID'"
    }'

    # Create the role in the client
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/$CLIENT_ID/roles" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_ROLE_JSON" | jq

    add_user "$realm_name" "viktor" "viktor@viktor.viktor" "Viktor" "👨🏻" "password"
    add_user "$realm_name" "ragadmin" "rag@rag.rag" "Admin" "User" "adminpassword" "$role_name"
}


delete_realm() {
    local realm_name=$1

    curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${realm_name}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" | jq
}

upload_config() {
    curl -X POST \
     -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d @ERAG-realm-export.json \
     http://localhost:1234/admin/realms
}

get_client_id(){
    local client_name=$1
    C_ID=$(curl -X GET "http://${KEYCLOAK_URL}/admin/realms/EnterpriseRAG/clients" -H "Authorization: Bearer $ACCESS_TOKEN" -H "Accept: application/json" | jq -r --arg key "clientId" --arg value "$client_name" '.[] | select(.[$key] == $value)' | jq -r '.id')
}

get_client_secret(){
#Get client secret. This will be needed by APISIX and UI
CLIENT_SECRET=$(curl -X POST \
     -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     "http://${KEYCLOAK_URL}/admin/realms/EnterpriseRAG/clients/$C_ID/client-secret" | \
     jq -r '.value')

}

create_client(){
   local realm_name=$1
   local client_name=$2
   local authorization=$3
   local authentication=$4

    echo "Creating a new client: $client_name in realm $realm_name"

    NEW_CLIENT_JSON='{
        "clientId": "'$client_name'",
        "enabled": true,
        "authorizationServicesEnabled": '$authorization',
        "serviceAccountsEnabled":  '$authentication',
	"directAccessGrantsEnabled": true,
	"publicClient": false,
	"clientAuthenticatorType": "client-secret",
        "redirectUris": [ "*" ],
        "webOrigins": [ "*" ],
        "protocol": "openid-connect",
        "frontchannelLogout": false
    }'
    echo $NEW_CLIENT_JSON
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_CLIENT_JSON" | jq

    CLIENT_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients?clientId=$client_name" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.[0].id')

    echo "CLIENT_ID=$CLIENT_ID"

}
create_role(){
    local realm_name=$1
    local client_name=$2
    local role_name=$3

    echo "Creating a new role: $role_name in client $client_ID"

    CLIENT_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients?clientId=$client_name" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.[0].id')

    echo "CLIENT_ID=$CLIENT_ID"
    NEW_ROLE_JSON='{
        "name": "'$role_name'",
        "description": "",
        "composite": false,
        "clientRole": true,
        "containerId": "'$CLIENT_ID'"
    }'

    # Create the role in the client
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/$CLIENT_ID/roles" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_ROLE_JSON" | jq

}
CWD="$(pwd)"

# Step 1: Define Variables
KEYCLOAK_URL=localhost:1234
KEYCLOAK_REALM=EnterpriseRAG
KEYCLOAK_CLIENT_ID=admin
ADMIN_PASSWORD=admin

# Obtain an Access Token using admin credentials
ACCESS_TOKEN=$(curl -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=${KEYCLOAK_CLIENT_ID}" \
 -d "password=${ADMIN_PASSWORD}" \
 -d 'grant_type=password' \
 -d 'client_id=admin-cli' | jq -r '.access_token')
cd $keyclock_config_path
upload_config
create_role $KEYCLOAK_REALM "EnterpriseRAG-oidc" "ERAG-admin"
create_role $KEYCLOAK_REALM "EnterpriseRAG-oidc" "ERAG-user"
add_user $KEYCLOAK_REALM "testadmin" "testadmin@example.com" "Test" "Admin" "password" "ERAG-admin" "EnterpriseRAG-oidc"
add_user $KEYCLOAK_REALM "testuser" "testuser@example.com" "Test" "User" "password" "ERAG-user" "EnterpriseRAG-oidc" 
