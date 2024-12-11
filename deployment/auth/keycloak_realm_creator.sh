#!/bin/bash

# requires jq
# sudo apt install jq

# set -x
repo_path=$(realpath "$(pwd)/../")
deployment_path="$repo_path/deployment"
auth_path="$repo_path/deployment/auth"
keyclock_config_path="$auth_path/keycloak-config"
AUTH_NS=${1:-default}
ADMIN_PASSWORD=${2:-admin}

SSOSESSIONMAXLIFESPAN=10800
SSOSESSIONIDLETIMEOUT=1800

generate_random_password() {
  local CHAR_SET="a-zA-Z0-9"
  local LENGTH=12
  random_string=$(tr -dc "$CHAR_SET" < /dev/urandom | head -c $LENGTH)
  echo "$random_string"
}

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
            "temporary": true
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
    echo "username: $username --- password: $password" >> $deployment_path/default_credentials.txt
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
create_realm() {
    local realm_name=$1

    echo "Creating a new Keycloak realm: $realm_name"

    NEW_REALM_JSON='{
        "realm": "'$realm_name'",
        "enabled": true,
        "displayName": "",
        "sslRequired": "none",
        "registrationAllowed": true
    }'
   
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_REALM_JSON" | jq

}

create_client(){
   local realm_name=$1
   local client_name=$2
   local options="$3"
   eval "$options"
    echo "Creating a new client: $client_name in realm $realm_name"

    NEW_CLIENT_JSON='{
        "clientId": "'$client_name'",
        "enabled": true,
	"directAccessGrantsEnabled": true,
        "authorizationServicesEnabled": '$authorization',
        "serviceAccountsEnabled": '$authentication',
        "publicClient": '$clientauthentication',
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

    echo "Creating a new role: $role_name in client $client_name"

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

# Set the default max & idle session timeout for a realm
set_realm_timeouts(){
    local realm_name=$1

    curl -X PUT "${KEYCLOAK_URL}/admin/realms/$realm_name" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
    "ssoSessionIdleTimeout": '"$SSOSESSIONIDLETIMEOUT"',
    "ssoSessionMaxLifespan": '"$SSOSESSIONMAXLIFESPAN"'
    }'

    echo "Setting SSO session MaxLifespan: $SSOSESSIONMAXLIFESPAN in realm $realm_name"
    echo "Setting SSO session IdleTimeout: $SSOSESSIONIDLETIMEOUT in realm $realm_name"
}
create_group(){
    local realm_name=$1
    local group_name=$2
    NEW_GROUP_JSON='{
        "name": "'$group_name'",
        "path": "'/$group_name'",
        "subGroups": [],
        "attributes": {}
   }'
   echo "Creating a group: $group_name"
   curl -s -X POST "${KEYCLOAK_URL}/admin/realms/$realm_name/groups" \
   -H "Authorization: Bearer $ACCESS_TOKEN" \
   -H "Content-Type: application/json" \
   -d "$NEW_GROUP_JSON" | jq

}

map_role_to_group() {
    local realm_name=$1
    local group_name=$2
    local role_name=$3

    # Get group ID from the group name
    local response=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$realm_name/groups" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
    group_id=$(echo $response | jq -r --arg name "$group_name" '.[] | select(.name == $name) | .id')
    # Get role ID from the role name
    local roleresponse=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$realm_name/roles" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
    role_id=$(echo $roleresponse | jq -r --arg name "$role_name" '.[] | select(.name == $name) | .id')
    # Check if both group_id and role_id are not empty
    if [[ -z "$group_id" || -z "$role_id" ]]; then
        echo "Error: Unable to retrieve group ID or role ID for group '$group_name' or role '$role_name'"
        return 1
    fi

    # Map the role to the group
    response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" \
        -X POST "$KEYCLOAK_URL/admin/realms/$realm_name/groups/$group_id/role-mappings/realm" \
        -d "[{\"id\": \"$role_id\", \"name\": \"$role_name\"}]")

    if [[ "$response" -eq 204 ]]; then
        echo "Successfully mapped role '$role_name' to group '$group_name'"
    else
        echo "Failed to map role '$role_name' to group '$group_name'. HTTP Status: $response"
        return 1
    fi
}
CWD="$(pwd)"

delete_realm() {
    local realm_name=$1

    curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${realm_name}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" | jq
}

# Step 1: Define Variables
KEYCLOAK_URL=${KEYCLOAK_URL:-localhost:1234}
KEYCLOAK_REALM=EnterpriseRAG
KEYCLOAK_DEFAULT_REALM=master
KEYCLOAK_CLIENT_ID=admin


# Step 3: Obtain an Access Token using admin credentials
ACCESS_TOKEN=$(curl -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=${KEYCLOAK_CLIENT_ID}" \
 -d "password=${ADMIN_PASSWORD}" \
 -d 'grant_type=password' \
 -d 'client_id=admin-cli' | jq -r '.access_token')

create_realm "EnterpriseRAG"
ROLES=(
  '{"name": "ERAG-admin", "description": "", "composite": false, "clientRole": false,  "attributes": {}}'
  '{"name": "ERAG-user", "description": "", "composite": false, "clientRole": false, "attributes": {}}'
)
for ROLE in "${ROLES[@]}"; do
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/roles" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${ROLE}")

  if [ "$RESPONSE" -eq 201 ]; then
    echo "Role created successfully"
  else
    echo "Failed to create role, HTTP status code: $RESPONSE"
  fi
done
create_client $KEYCLOAK_REALM "EnterpriseRAG-oidc" 'authorization=false authentication=false clientauthentication=true'
create_client $KEYCLOAK_REALM "EnterpriseRAG-oidc-backend" 'authorization=true authentication=true clientauthentication=false'
create_role $KEYCLOAK_REALM "EnterpriseRAG-oidc" "ERAG-admin"
create_role $KEYCLOAK_REALM "EnterpriseRAG-oidc" "ERAG-user"
create_role $KEYCLOAK_REALM "EnterpriseRAG-oidc-backend" "ERAG-admin"
create_role $KEYCLOAK_REALM "EnterpriseRAG-oidc-backend" "ERAG-user"
create_group $KEYCLOAK_REALM ERAG-admins
create_group $KEYCLOAK_REALM ERAG-users
map_role_to_group $KEYCLOAK_REALM ERAG-admins ERAG-admin
map_role_to_group $KEYCLOAK_REALM ERAG-users ERAG-user
true > $deployment_path/default_credentials.txt
add_user $KEYCLOAK_REALM "erag-admin" "testadmin@example.com" "Test" "Admin" "$(generate_random_password)" "ERAG-admin" "EnterpriseRAG-oidc"
add_user $KEYCLOAK_REALM "erag-user" "testuser@example.com" "Test" "User" "$(generate_random_password)" "ERAG-user" "EnterpriseRAG-oidc"
set_realm_timeouts $KEYCLOAK_REALM
set_realm_timeouts $KEYCLOAK_DEFAULT_REALM
